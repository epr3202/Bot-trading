# Contexto del sistema

Investigación exclusivamente virtual: offline, backtest, shadow y etoro_demo.
ORB_RVOL_v0.1 y sus gates permanecen intactos. No existe autorización para
operaciones externas, dinero real, publicación o inicio automático de shadow.

Massive es una fuente histórica seleccionable: `data.provider: massive` y
`data.path` al directorio de captura offline existente. La configuración normal
inicializa MassiveHistoricalProvider y obtiene DataBundle, sin fixtures, captura
de red ni fallback. Las rutas/capturas inválidas y MassiveDataError fallan
explícitamente. HISTORICAL_DOWNLOAD no se transforma en observed.
El cierre de los dos criterios A1 se documenta en [VERIFICATION](VERIFICATION.md);
A2 no se aborda. La evidencia real Massive anterior se conserva sin reinterpretarla.

Fuentes de verdad: [AGENTS](../AGENTS.md) para invariantes, [STATUS](../STATUS.md)
para estado actual, [HANDOFF](../HANDOFF.md) para continuidad, [TASKS](../TASKS.md)
para tareas, [ARCHITECTURE](ARCHITECTURE.md) para diseño y especificaciones
STRATEGY_SPEC/DATA_CONTRACTS/RISK_POLICY/ORDER_LIFECYCLE para comportamiento.
[SHADOW_READINESS](SHADOW_READINESS.md) registra la decisión de esta fase.
Este índice no sustituye ni duplica esas reglas.
