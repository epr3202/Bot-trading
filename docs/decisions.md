# Índice de decisiones

## A1 — selección histórica Massive, 2026-09-15

Se reutiliza `data.path` como directorio de captura Massive, sin nuevos campos.
La configuración exige directorio existente; el lector valida el contenido.
`data.manifest` externo se rechaza para Massive: la fuente es capture.json dentro
de path. Fixtures/import mantienen sus contratos. El dispatch enumera los tres
proveedores y propaga errores; nunca usa fallback automático a fixtures/import.
Massive sigue separado de broker/ejecución: esta ruta carga histórico offline,
sin autenticación/red, y conserva HISTORICAL_DOWNLOAD y el gate observed.
No se modifica la estrategia ni se avanza a A2.

Las decisiones de arquitectura canónicas permanecen en [adr](adr):
[solo virtual](adr/001-demo-only.md), [datos/bróker](adr/002-data-broker.md),
[estrategia](adr/003-strategy-v01.md), [ejecutor](adr/004-single-executor.md),
[órdenes](adr/005-order-lifecycle.md), [armado](adr/006-arming.md) y
[backtest](adr/007-backtest.md).

Decisión de 2026-09-14: [BLOCKED_BY_EXTERNAL_CONFIGURATION](SHADOW_READINESS.md).
Ausencia de credenciales se distingue de insuficiencia de datos; una query SIP
no acredita feed observado; duplicados no aprueban calidad; histórico descargado
no se reclasifica como recepción realtime. Las reglas ejecutables y la taxonomía
pertenecen a [ALPACA_DATA_CONTRACT](ALPACA_DATA_CONTRACT.md).
