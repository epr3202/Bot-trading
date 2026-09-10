# Estado verificado — 2026-09-10

| Dimensión | Estado | Evidencia / alcance |
|---|---|---|
| Software | **LOCAL_VERIFIED** | 358 pruebas, 16/16 gates locales, lint/formato/tipos/build, HTTP y navegador |
| Bróker | **NOT_CONFIGURED** | Contratos oficiales y mocks; cero lecturas de cuenta o escrituras de trading |
| Datos | **SYNTHETIC_ONLY** | 26.910 barras, 20 warmups + 3 sesiones, importador CSV/Parquet probado |
| Investigación | **RESEARCH_BLOCKED_DATA** | Motor/estadísticas reproducibles, sin históricos aptos ni validación de ventaja |
| Git | **STAGED / COMMITS_BLOCKED_IDENTITY** | 123 archivos preparados en main, sin identidad, commits ni remoto |

Implementado y probado: configuración estricta, calendario, ORB/RVOL, riesgo Decimal,
reservas, máquina de estados, SQLite, exclusión de doble proceso, fills parciales,
UNKNOWN, reconciliación local, propiedad, protección, backups/restauración, simulador,
replay, métricas/bootstrap, informes, API autenticada y panel español.
Adaptador eToro y autorización temporal implementados a nivel contractual y pruebas mock.

Prueba final en entorno CI=true, credenciales retiradas: **358 passed, 0 failed, 0 skipped**,
7 warnings de dependencias, salida 0. Cobertura total de líneas+ramas **90,43%**;
riesgo **100%**, transporte **99,12%**, autorización **98,40%**, ejecutor **94,52%**,
estados **100%**, persistencia **96,34%**. Mypy: 33 archivos fuente sin errores.
Formato/lint y scanner de secretos: aprobados. Las advertencias no se ocultaron.

`demo-offline`: cuatro órdenes locales, cero posiciones abiertas; reinicio/repetición
no duplican órdenes ni PnL. Run ID **42ff34b0e40a7f44e861**. El PnL del simulador de
ciclo de vida es un ejemplo artificial distinto del replay, no rendimiento de cuenta.
Paquete instalado en un entorno nuevo con 52 paquetes desde caché, recorrido offline
reproducido. Chrome autenticado: OFFLINE, cuatro órdenes; captura en runtime/dashboard.png.
El navegador y el servidor de verificación terminaron; no quedan servicios instalados.

Pendiente externo: claves propias Demo y lectura autorizada, fuente OHLCV/volumen
compatible, elegibilidad/precisión/costes/protección de cuenta y reconciliación completa
de cierres v1. `run --mode etoro_demo`, armado y cierre Demo quedan BLOCKED. No hay
ejecutor conectado, trading real, publicación GitHub ni certificación Demo implícita.

Evidencia: [resumen versionado](docs/VERIFICATION.md), runtime/verification.json,
runtime/test-results.xml, runtime/coverage.json, runtime/package-evidence.json,
runtime/browser-evidence.json y reports/runs/. Consultar HANDOFF/TASKS para continuar.
