from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from intraday_etoro_lab.api.app import create_app
from intraday_etoro_lab.cli import main
from intraday_etoro_lab.config import AppConfig
from intraday_etoro_lab.service import OperationService, read_report


def test_fixture_signal_position_close_report_over_http_and_restart(tmp_path: Path) -> None:
    config = AppConfig(runtime_dir=tmp_path / "runtime", reports_dir=tmp_path / "reports")
    service = OperationService(config)
    auth = {"Authorization": "Bearer " + "a" * 48, "Origin": "http://127.0.0.1:8765"}
    client = TestClient(create_app(service, "a" * 48), base_url="http://127.0.0.1:8765")
    try:
        with pytest.raises(RuntimeError, match="another executor"):
            OperationService(config)
        assert client.get("/").status_code == 200
        started = client.post("/api/commands", headers=auth, json={"action": "fixture-start"})
        assert started.status_code == 200, started.text
        opened = started.json()
        assert len(opened["positions"]) == 2
        assert {p["symbol"] for p in opened["positions"]} == {"SIMA", "SIMB"}
        assert all(p["protected"] for p in opened["positions"])
        assert {o["state"] for o in opened["orders"]} == {"FILLED"}
        assert Decimal(opened["exposure"]) > 0
        paused = client.post("/api/commands", headers=auth, json={"action": "pause-entries"})
        assert paused.json()["entries_paused"]
        assert len(paused.json()["positions"]) == 2
        closed = client.post("/api/commands", headers=auth, json={"action": "fixture-close"})
        assert closed.status_code == 200, closed.text
        final = closed.json()
        assert not final["positions"]
        assert len(final["orders"]) == 4
        assert Decimal(final["exposure"]) == 0
        assert final["report"]["metrics"]["sessions"] == 3
        assert "SYNTHETIC" in final["report"]["label"]
        run_id = final["report"]["run_id"]
        assert read_report(run_id, config.reports_dir)["run_id"] == run_id
        assert (config.reports_dir / f"{run_id}.html").is_file()
        assert not final["entries_armed"]
        assert final["broker_status"] == "NOT_CONFIGURED"
    finally:
        service.close()
    restarted = OperationService(config)
    try:
        recovered = restarted.command("demo-offline")
        assert len(recovered["orders"]) == 4
        assert recovered["realized_pnl"] == final["realized_pnl"]
        assert not recovered["positions"]
        assert not recovered["entries_armed"]
    finally:
        restarted.close()


def test_connected_mode_never_runs_fixture_and_demo_controls_fail_closed(tmp_path: Path) -> None:
    config = AppConfig(mode="shadow", runtime_dir=tmp_path)  # type: ignore[arg-type]
    service = OperationService(config)
    try:
        with pytest.raises(RuntimeError, match="no se usan fixtures"):
            service.command("demo-offline")
        with pytest.raises(ValueError, match="Confirmación"):
            service.command("flatten-owned-demo")
        with pytest.raises(ValueError, match="presupuesto"):
            service.command("arm-demo", confirm="DEMO_ONLY", budget="99999")
        with pytest.raises(RuntimeError, match="DEMO_SESSION_RUNNER_NOT_VALIDATED"):
            service.command("arm-demo", confirm="DEMO_ONLY", budget="10000")
        assert not service.snapshot()["orders"]
    finally:
        service.close()


def test_cli_doctor_and_missing_credentials_are_honest(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["doctor"]) == 0
    assert '"network_calls": 0' in capsys.readouterr().out
    assert main(["etoro", "preflight", "--read-only"]) == 2
    assert "CREDENTIALS_MISSING_OR_INVALID" in capsys.readouterr().out
    assert main(["run", "--mode", "etoro_demo"]) == 2
    assert "DEMO_SESSION_RUNNER_NOT_VALIDATED" in capsys.readouterr().out
    with pytest.raises(SystemExit) as result:
        main(["run", "--mode", "live"])
    assert result.value.code == 2


def test_report_lookup_does_not_accept_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        read_report("../../.env", tmp_path)
    with pytest.raises(ValueError, match="inexistente"):
        read_report("0" * 20, tmp_path)
