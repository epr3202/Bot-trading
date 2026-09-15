# Estado — Massive histórico, 2026-09-15

## Repositorio remoto autorizado — 2026-09-15

El usuario autorizó publicar este proyecto en
[epr3202/Bot-trading](https://github.com/epr3202/Bot-trading), rama `main`.
Revisión previa: remoto vacío; 13 commits y 248 blobs históricos escaneados,
cero hallazgos de secretos o rutas privadas. Código probado sin cambios:
574 pruebas y 16/16 gates locales. GitHub Actions no se declara verificado.
Raw, credenciales, runtime y entornos locales quedan excluidos de Git.

## Validación histórica vigente

**MASSIVE_HISTORICAL_RVOL_VERIFIED**. AAPL, 1m, objetivo 14/09/2026:
20 sesiones previas completas + objetivo; **21/21 válidas, 8.190 barras regulares**.
Captura real HTTP 200 tras fallo de conectividad en el entorno restringido.
Cobertura 100_percent_market según contrato histórico consolidado CTA/UTP;
nombre del plan no observado. Calidad PASS; ninguna barra rellenada.

ORH 334.83; ORL 331.72; V5 objetivo 1834725.760868; media previa
1690527.49202725; RVOL **1.085297795818647139199521439**.
Cinco métricas coinciden exactamente con el motor. Datos HISTORICAL_DOWNLOAD:
el gate operativo OBSERVED_AVAILABILITY_REQUIRED sigue bloqueando señales.

Proveedor Massive independiente y CSV importable. Alpaca, eToro, ORB/RVOL,
riesgo, ejecución, configuración y lock preservados. No shadow, órdenes ni
Demo Write. DEMO_READ_VERIFIED sigue como hito previo, sin lecturas de cuenta.
entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED.

Contrato, métricas y límites: [MASSIVE_DATA_CONTRACT](docs/MASSIVE_DATA_CONTRACT.md).
Código `8ed65eb`: **574 pruebas, 16/16 gates, cobertura 90,525210%**;
sin fallos/skips y sin reducción de cobertura crítica. Evidencia: VERIFICATION.

## Antecedente — preparación para fase shadow, 2026-09-14

**BLOCKED_BY_EXTERNAL_CONFIGURATION / ALPACA_CREDENTIALS_UNAVAILABLE**.
Ambas variables dedicadas ausentes en el proceso; CLI oficial bloqueada antes de
red. Cero datos Alpaca, feed no observado, ORH/ORL/RVOL reales NOT_RUN.
**SHADOW_NOT_READY**; no se ejecutó ampliación, baseline real, OOS ni shadow.

Se corrigen clasificación de fallos, feed inferido sin eco y duplicados que podían
aprobar calidad. Reportes de calidad por AAPL/agregado, hashes y regresiones
temporales preservan el gate OBSERVED_AVAILABILITY_REQUIRED. ORB/RVOL, riesgo,
eToro y configuración operativa intactos. `scripts/verify.py`: **512 pruebas,
16/16 gates, cobertura 90,488615%**, sin fallos/skips ni reducción crítica.
Código local `b7a17b7`; comprobaciones exactas: [VERIFICATION](docs/VERIFICATION.md).

eToro DEMO_READ_VERIFIED se conserva como evidencia histórica registrada, sin
consultas de cuenta nuevas. entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED.
Decisión y requisitos pendientes: [SHADOW_READINESS](docs/SHADOW_READINESS.md).

## Antecedente — Alpaca histórico

La clasificación siguiente es histórica y queda corregida arriba: ausencia de
credenciales no demuestra insuficiencia de datos ni falta de entitlement.

**ALPACA_DATA_INSUFFICIENT_FOR_RVOL**: primer intento SIP bloqueado antes de red
por ALPACA_CREDENTIALS_UNAVAILABLE en el proceso del agente. Feed solicitado SIP;
feed efectivo desconocido; cero barras/sesiones recuperadas. Entitlement no
comprobado: no se afirma que la cuenta necesite una suscripción. ORH/ORL/RVOL y
comparación real NOT_RUN. Manifiesto saneado en docs/alpaca-historical-manifest.json.

Proveedor histórico de solo lectura incorporado: captura por ruta fija, paginación,
SHA-256, carga offline mediante MarketDataProvider y exportación al importador
existente. No depende de SDK; eToro no fue reemplazado. 38 regresiones Alpaca y
15 pruebas existentes de estrategia/datos aprobadas. Batería final: 491 pruebas,
16/16 gates, cobertura total 90,070065%; cobertura crítica sin reducción.
Evidencia y commits en VERIFICATION.
Fórmulas de apertura extraídas sin cambios para comparar con cálculo independiente;
el motor operativo sigue rechazando histórico descargado como datos observados.

eToro DEMO_READ_VERIFIED preservado. No se corrigió el feed eToro, no se consultaron
cuentas, no hubo órdenes, shadow, realtime ni compras. entries_armed=false,
external_mutations=DISABLED, order_submission_enabled=false, etoro_demo_write=NOT_TESTED.
Contrato, limitaciones y comando de captura en [ALPACA_DATA_CONTRACT](docs/ALPACA_DATA_CONTRACT.md).

## Hito anterior conservado — Market Data eToro

| Dimensión actual | Estado | Evidencia / límite |
|---|---|---|
| broker / Demo Read | DEMO_READ_VERIFIED | Hito externo comunicado por el usuario desde Bot 3; connectivity/authentication/demo_identity VERIFIED; no se repitió preflight |
| acceso Market Data | VERIFIED_VIA_MCP | Siete GET exclusivamente Market Data, HTTP 200; AAPL=1001, Nasdaq, quote y velas reales |
| Market Data ORB/RVOL | BLOCKED | ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL |
| volumen | UNKNOWN | No nulo y agregación coherente; unidades y consolidación no acreditadas |
| histórico minuto | INSUFFICIENT | 1.000 velas recientes; 209 minutos regulares completados; 0/20 sesiones previas completas y 0/20 aperturas previas |
| cálculo independiente real | PARTIAL | AAPL 14/09: ORH 334,54; ORL 331,72; volume apertura 1.181.044; RVOL no calculable |
| comparación motor | BLOCKED_AS_EXPECTED | OBSERVED_AVAILABILITY_REQUIRED; no candidato, cero señales; no paridad numérica afirmada |
| shadow | NOT_STARTED_DATA_QUALITY_BLOCKED | Sin sesión ni órdenes externas |
| seguridad | PRESERVED | entries_armed=false; external_mutations=DISABLED; order_submission_enabled=false; etoro_demo_write=NOT_TESTED |
| software local | VERIFIED | 453 pruebas sin fallos/skips; 16/16 gates; cobertura 90,686683% |

Muestra inmutable y manifiesto con SHA-256 preservados. Detalle, timestamps, límites
de cotización y reproducción en [ETORO_MARKET_DATA_VALIDATION](docs/ETORO_MARKET_DATA_VALIDATION.md).
Pruebas y commits de esta fase en [VERIFICATION](docs/VERIFICATION.md).
No se cambió estrategia, calentamiento, riesgo, permisos ni adaptador de ejecución.
X01 histórico queda superado por el hito del usuario; no volver a diagnosticarlo.
La captura MCP es evidencia externa real separada del proceso HTTP de Bot 3.

## Historia conservada — fases anteriores

Actualización 2026-09-14 solicitada por el usuario: soporte de proxy del entorno
y CA corporativa como en `oficios.py`, aplicado al cliente externo de eToro.
TLS sigue obligatorio; no cambian rutas, cuotas, autorizaciones ni mutaciones.
Verificación final: 443 pruebas sin fallos/skips, 16/16 gates aprobados,
cobertura total 90,686683%; ocho regresiones nuevas (ver HANDOFF).
Construcción local del cliente: salida 0, sin solicitudes. En este proceso hay
variables de proxy, pero no `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `SSL_CERT_DIR`
ni `certs/epm-root.cer`. El certificado tampoco está junto al script de referencia.
Conectividad/TLS externo siguen sin comprobar; no se consultaron cuentas.
La tabla siguiente conserva la evidencia histórica de fase 3.

| Dimensión | Estado | Evidencia / límite |
|---|---|---|
| software_local | VERIFIED | C: 435 pruebas, 16/16 gates, cobertura 90,650293%; sin fallos ni skips |
| reconciliación contractual | DOCUMENTED / CONTRACT_TESTED / BLOCKED por campo | Matriz en ETORO_API_AUDIT: lookup v2 aclara estados y exposición; faltan garantías contables de cierres |
| reconciliación externa observada | NOT_OBSERVED | Ningún cierre ni lectura de órdenes de cuenta ejecutados |
| etoro_demo_read | NOT_CONFIGURED | Preflight real del proceso salió 2: ambas claves ausentes |
| etoro_demo_write | NOT_TESTED | Ninguna mutación externa ejecutada |
| market_data | SYNTHETIC_ONLY / BLOCKED_DATA | Sin muestra real descargada; acceso público falló con WinError 10061; candidato limitado a cuatro registros |
| research | BLOCKED_DATA | Sin ORH/ORL/RVOL reales, replay causal real, shadow observado o rentabilidad validada |
| external_mutations | DISABLED | Guardas de red, CLI y panel conservadas; ni configuración ni permiso anterior habilitan envíos |
| panel_http | VERIFIED | Suite HTTP local aprobada |
| panel_visual | NOT_REPRODUCED | Único intento Chrome salió 1: no arrancó depuración; token retirado |
| Git | VERSIONED_LOCAL | A, B y C conservados; rama feat/phase3-readonly-evidence, sin remoto ni publicación |

A: `6af05f1b16b8e3488a5cd959dc0e7f889b258fd6`, base original de 123 archivos:
358 pruebas en instalación aislada. B: `ef8bf5564f6e15bd04ae084c18cd63dd27ba380b`,
los 33 modificados y seis nuevos de Fase 2: 420 pruebas, importación sintética y
paquete offline aprobados. C: `b51506a97771d04a5edfb45d46e8fac4c31f307f`,
correcciones puntuales de Fase 3: 435 pruebas. El incremento documental posterior
comparte exactamente el código de C; no se le atribuye otra ejecución de la suite.

La identidad Git efectiva ya está configurada y se comprobó antes de los commits.
No volver a pedir nombre/correo. El índice original se conservó antes del primer
git add. No se borraron cambios, no hubo push ni se habilitaron mutaciones externas.

Se detiene la ampliación del producto: quedan acceso Demo Read propio, datos
autorizados suficientes y aclaraciones del bróker. Responsables y acciones mínimas
en [HANDOFF](HANDOFF.md); comandos, huellas y versiones en
[VERIFICATION](docs/VERIFICATION.md). Las 435 pruebas son evidencia local.
