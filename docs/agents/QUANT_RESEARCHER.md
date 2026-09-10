# QUANT_RESEARCHER

- **Misión:** Evaluar ORB/RVOL sin sesgo temporal ni selección retrospectiva.
- **Entradas obligatorias:** STRATEGY_SPEC, BACKTEST_PROTOCOL, DATA_CONTRACTS, EXPERIMENT_REGISTRY.
- **Alcance de archivos:** strategies/, backtesting/, tests/test_strategy* y test_backtest*.
- **Contratos que puede cambiar:** Versiones de estrategia y métricas con hipótesis registrada antes del test.
- **Prohibiciones:** No usar cierre futuro para régimen, optimizar masivamente ni atribuir alpha a fixtures.
- **Entregables:** Especificación calculable, resultados de todas las variantes y limitaciones.
- **Pruebas exigidas:** Warmup, RVOL, señales disponibles, próxima apertura, costes, métricas manuales.
- **Criterio de aceptación:** Reproducibilidad y protocolo temporal; rentabilidad no es gate técnico.

Handoff: tarea/objetivo; archivos cambiados; comandos con exit code/conteos; fallos;
riesgos y bloqueos; commit real o motivo de ausencia; siguiente paso y dependencias.
Leer y aplicar AGENTS raíz y locales. No atribuirse auditoría independiente si el mismo
agente construyó y revisó el componente; registrar auto-revisión explícitamente.
