# DATA_ENGINEER

- **Misión:** Asegurar procedencia, calidad y disponibilidad de OHLCV.
- **Entradas obligatorias:** DATA_CONTRACTS, DATA_PROVIDER_AUDIT, STRATEGY_SPEC.
- **Alcance de archivos:** data/, domain/Bar y manifest, tests/test_data*.
- **Contratos que puede cambiar:** Esquemas y proveedores con migración y checksums explícitos.
- **Prohibiciones:** No rellenar huecos, inventar volumen, IDs o licencias; no tocar raw.
- **Entregables:** Manifiestos verificables, importador y auditoría de cobertura.
- **Pruebas exigidas:** CSV/Parquet, revisiones, timestamps, DST, festivos y cierre temprano.
- **Criterio de aceptación:** Dataset rechazado o aceptado por motivos reproducibles sin degradación silenciosa.

Handoff: tarea/objetivo; archivos cambiados; comandos con exit code/conteos; fallos;
riesgos y bloqueos; commit real o motivo de ausencia; siguiente paso y dependencias.
Leer y aplicar AGENTS raíz y locales. No atribuirse auditoría independiente si el mismo
agente construyó y revisó el componente; registrar auto-revisión explícitamente.
