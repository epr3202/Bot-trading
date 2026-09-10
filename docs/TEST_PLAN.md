# Plan de pruebas

`uv run pytest --cov=intraday_etoro_lab --cov-branch --cov-report=json:runtime/coverage.json`
ejecuta pruebas offline y mocks. `uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy src`, `uv run python scripts/scan_secrets.py` y `uv build --offline`
completan los gates locales. No requieren Internet después de instalar dependencias.

| Riesgo | Evidencia |
|---|---|
| Modos reales, opciones desconocidas, CSRF/host/tokens | test_config_api.py, test_e2e_http.py |
| RVOL, warmup, selección congelada, volumen inválido | test_strategy_orb.py |
| DST/festivos/cierre temprano, esquema/importación inmutable | test_data_contracts.py |
| Sizing, mínimos, nonlinear fees, slots, NaN y propiedades | test_risk_engine.py (incluye Hypothesis) |
| Timeout, parcial, cancelación cruzada, propiedad/protección | test_execution_engine.py |
| Doble proceso, rollback, backups, regresiones de fills/costes | test_persistence_recovery.py |
| Allowlist, redirects, 429, credenciales, CI/shadow, lease | test_etoro_transport.py |
| Preflight, payloads, lookup, stops y datos eToro mock | test_etoro_adapter.py |
| Próxima apertura, caducidad, gaps/stops, costes y métricas | test_backtest_replay.py |
| Fixture → señal → posiciones → pausa → cierre → informe | test_e2e_http.py |

Conftest impide conexiones externas por socket y retira credenciales de los tests.
En Windows restringido, temporales pytest con modo 0700 excluían al token del sandbox;
tmp_path usa directorios únicos bajo runtime/test-artifacts con ACL heredada. No cambia
ACL global ni borra directorios anteriores. El caché pytest se desactiva por ese problema.
Las deprecaciones de dependencias se reportan, no se silencian. No hay pruebas externas
automáticamente omitidas: la certificación Demo es una tarea opt-in aún no ejecutada.
