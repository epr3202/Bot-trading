"""Generate configuration reference directly from validated defaults and JSON Schema."""

import json
from pathlib import Path

from pydantic import BaseModel

from intraday_etoro_lab.config import AppConfig


def main() -> None:
    lines = [
        "# Configuración",
        "",
        "Fuente de verdad: modelos Pydantic y configs/offline.yaml. Campos extra se rechazan.",
        "Números monetarios son Decimal USD; fracciones son proporciones (0.001 = 0,10%).",
        "Todos los costes predeterminados describen únicamente simulación sintética.",
        "",
        "| Clave | Tipo | Valor predeterminado |",
        "|---|---|---|",
    ]

    def visit(model: BaseModel, prefix: str = "") -> None:
        for key, field in type(model).model_fields.items():
            value = getattr(model, key)
            name = f"{prefix}{key}"
            if isinstance(value, BaseModel):
                visit(value, name + ".")
            else:
                kind = str(field.annotation).replace("|", "o").replace("<", "").replace(">", "")
                lines.append(f"| `{name}` | {kind} | `{value}` |")

    visit(AppConfig())
    lines.extend(
        [
            "",
            "*_seconds usa segundos; latency_ms milisegundos; *_bps puntos básicos.",
            "Cambios de modo, datos, estrategia, costes, riesgo y duración alteran el hash de",
            "configuración y requieren nuevo armado. Presupuesto backtest y riesgo, y TTL de",
            "estrategia/riesgo, deben coincidir. Extensiones bool solo admiten false en v0.1.",
            "",
            "BOT_MODE se valida aun si CLI proporciona otro modo. ORDER_SUBMISSION_ENABLED",
            "solo admite texto true/false y requiere etoro_demo para true. .env no se carga.",
            "ETORO_API_KEY/ETORO_USER_KEY no pertenecen al YAML. El host eToro es fijo.",
            "",
            "Esquema completo con límites y tipos: [config.schema.json](config.schema.json).",
            "El panel solo admite host 127.0.0.1, puerto 1024–65535; 8765 por defecto.",
        ]
    )
    Path("docs/CONFIGURATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    Path("docs/config.schema.json").write_text(
        json.dumps(AppConfig.model_json_schema(), indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
