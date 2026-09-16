## A7 WebSocket: verificacion final del spike (2026-09-16)

23 tests del spike PASS; 165 focales WebSocket/A6/A7 PASS (5 warnings).
Suite completa: 905 passed, 7 warnings, cero fallos/errors/skips; 16/16 gates
PASS con scripts/verify.py y codigo inmutable durante checks. Secret scan:
193 archivos, 0 hallazgos; git diff --check exit 0; inspector Strategy 1 PASS.
52 archivos src/configs/lock/snapshot/pyproject preservados contra baseline.
El primer gate detecto dos fallos del aislamiento monkeypatch del test nuevo;
se corrigieron y se repitieron focales y todos los gates. Evidencia inicial
se conserva, evidencia final: runtime/a7-websocket/verification.json.
No demuestra viabilidad WebSocket: handshake HTTP 403 del proxy EPM, cero
eventos y cero mutaciones; A7 PARTIAL/BLOCKED. Detalle: A7_WEBSOCKET.md.

## A7 WebSocket: spike bloqueado por handshake HTTP 403

Revision contractual permite eToro WebSocket conservando el gate de 3 s.
Diagnostico aislado: el handshake devuelve HTTP 403 con pagina Proxy WebGateway
EPM, antes de Authenticate; cero eventos, suscripciones u ordenes. No se ha
integrado el stream al runner ni se ha cambiado codigo productivo, riesgo,
Strategy 1, A6, Massive, contratos congelados o uv.lock. Reconnect productivo
y validacion en mercado abierto pendientes; no declarar migracion PASS.
Detalle: docs/A7_WEBSOCKET.md (desde docs: A7_WEBSOCKET.md).
A7 PARTIAL/BLOCKED: upgrade WebSocket rechazado por la infraestructura de red.

## Massive: detalle del 403 verificado (2026-09-16 19:35 UTC)

MASSIVE_API_KEY: PRESENT; fuente exclusiva .env del repositorio.
Un GET /v2/last/nbbo/AAPL devuelve HTTP 403, status NOT_AUTHORIZED:
You are not entitled to this data. El proveedor indica falta de entitlement
para estos datos y sugiere upgrade; el nombre del plan sigue UNKNOWN.
No generalizar a todo acceso operativo ni atribuirlo al incidente FMV.
Evidencia sanitizada: runtime/massive-operational/denial-detail-20260916T193532830663Z.json.
La fuente actual queda verificada; la credencial del intento historico sigue
sin identificacion demostrable. A7 PARTIAL/BLOCKED; limite 3 s intacto.
Cero mutaciones; sin cambios de codigo productivo, contratos ni .env.
Las notas inferiores sobre .env MISSING corresponden al estado anterior.

# Estado — Massive histórico, 2026-09-15

Diagnóstico Massive actualizado por autorización del usuario: credencial solo
desde .env del repositorio, sin fallback al entorno. MASSIVE_API_KEY [.env]
MISSING; .env intacto. 21 tests del diagnóstico PASS. Sin llamadas externas ni
cambios de trading; CREDENTIAL_SOURCE_UNVERIFIED continúa para el intento anterior.

## Rectificación de investigación Massive — 2026-09-16

CREDENTIAL_SOURCE_UNVERIFIED. Se invalida la conclusión de acceso operativo
basada en tres 403: PRESENT solo comprobaba una variable no vacía. MASSIVE_API_KEY
está PRESENT en proceso y Windows User, MISSING en .env y Machine. Su emisor,
validez y valor histórico exacto no están acreditados. No nuevos requests ni
cambios de código/contratos/A7. Detalle en la rectificación del informe de viabilidad
y runtime/massive-operational/credential-source-audit.json.

## Investigación Massive operativo — 2026-09-16

CONTRACT_CHANGE_NOT_JUSTIFIED: Last NBBO AAPL/SPY/QQQ devuelve HTTP 403.
Credencial PRESENT, plan UNKNOWN; cero quotes, frescura no medible. Ventana
read-only interrumpida sin retries de denegación. A7 sigue PARTIAL/BLOCKED.
Solo diagnóstico aislado y pruebas; sin cambios productivos ni normativos.
12 tests del spike, 268 focales y 873 completos PASS; 16/16 gates PASS.
Detalle no normativo: [viabilidad](docs/MASSIVE_OPERATIONAL_FEASIBILITY.md).

Validacion final de esta auditoria: 861 tests PASS, 7 warnings; 16/16 gates PASS.
142 focales A7/A6 PASS; secret scan 187 archivos / 0 hallazgos; diff check 0.
Strategy 1/riesgo/runner A6/config/lock preservados por hashes. Evidencia exacta
en runtime/a7-quote-audit/verification.json y acceptance.json.

## A7 — auditoria UTC/costes, PARTIAL/BLOCKED (2026-09-16)

La evidencia anterior era 81.588043 s, no 81588 s; ambiguedad de coma decimal.
Dos GET rates nuevos confirmaron retrasos de 35.860831 y 75.107782 s.
Recepcion HTTP registrada antes del parseo, UTC aware; limite 3 s intacto.
Costes value/amount normalizados dentro del adapter; fixture real sanitizado.
142 pruebas focales A7/A6 PASS. Gate externo QUOTE_STALE_OR_DELAYED;
cero ordenes/mutaciones; identidad DEMO y parser de costes PASS.
No se habilita el vertical de trading mientras falle frescura. No A8.
Detalle, cambios, comandos y evidencia: [auditoria A7](docs/A7_QUOTE_COST_AUDIT.md).


## A7 — continuación: preparación y diagnóstico externo, PARTIAL/BLOCKED

Se distingue rechazo previo al envío de UNKNOWN: preparación con intención
APPROVED, metadata durable y liberación de reservas solo con cero intentos de
mutación demostrados. Crash durante POST sigue UNKNOWN y nunca reenvía.
El usuario autorizó estímulo sintético A6 exclusivamente para el smoke Demo.
Identidad/scopes/elegibilidad/costes hipotéticos observados con credenciales
existentes PRESENT. La cotización externa falló: 81.588043s frente a máximo 3s.
Costes usa value frente a amount del esquema; contabilidad de cierre pendiente.
Cero órdenes/mutaciones. No se conectó aún el runner ni se habilitó Demo Write.
Gates finales: 842 passed, 7 warnings, 16/16 PASS, cero fallos/skips.
39 A6 y 84 A7 PASS; secretos/diff check/Strategy 1 PASS.
Detalles y partes pendientes: [continuación A7](docs/A7_COMPLETION_ATTEMPT.md).
Las afirmaciones históricas de core intacto o UNKNOWN para todo rechazo quedan
actualizadas por este incremento; Strategy 1, riesgo, A6 y esquema se conservan.

## A7 — PARTIAL / ejecución externa BLOCKED, 2026-09-16

Defensa de identidad centralizada DEMO/REAL/UNKNOWN; adaptador y transporte
verifican /me + portfolio Demo, scopes write y vínculo de autorización antes
de mutar en contratos mock. REAL/UNKNOWN/error y cambio de identidad bloquean.
A7 está autorizado, pero no cerrado: permanecen pendientes feed operativo,
elegibilidad/costes/stops efectivos y reconciliación contable externa de cierres.
La barrera de red sigue activa; no nuevo runner conectado ni DEMO_WRITE_VERIFIED.
Core A6/riesgo/persistencia/Strategy 1 preservados; cero operaciones externas.
Validación final: 822 passed, 7 warnings, cero fallos/skips; 16/16 gates.
64 casos A7 y 39 A6 PASS; código estable, escaneo de secretos y diff check PASS.
Diseño, pruebas, matriz DoD y límites: [A7](docs/A7_DEMO_ONLY.md).
Checks exactos: [VERIFICATION](docs/VERIFICATION.md).
Las notas inferiores de A7 no autorizado quedan como antecedentes superados.

## A6 — PASS / sesión exclusivamente simulada, 2026-09-16

Runner conectado con Strategy 1 v1 congelada: contexto Demo mock, elegibilidad,
señal, riesgo, intención durable, simulador local, reconciliación y cierre flat.
Dos runs aceptados: una señal, entrada+cierre, mismo estado/órdenes/resultado;
retry sin duplicados. No señal: cero intenciones. Evidencia runtime/a6/comparison.json.
39 casos A6; suite completa 758 passed, 7 warnings, cero fallos/skips; 16/16 gates
PASS. Cobertura total 91.411683%, runner 95.18%, inputs/fixture 100%; crítica intacta.
Código previo preservado por huella, Strategy 1 inspector PASS. No cuenta externa,
lectura de .env, mutaciones eToro, cambios de riesgo/schema/dependencias o A7.
A5 real conserva su propia evidencia; A6 no la renueva ni habilita permisos.
Detalles: [A6](docs/A6_SESSION.md); comandos y checks: [VERIFICATION](docs/VERIFICATION.md).
Las notas históricas A6 no iniciado inferiores quedan superadas por este alcance.

## A5 — CLOSED / DEMO_READ_VERIFIED, 2026-09-16

Credenciales existentes en .env cargadas explícitamente mediante uv --env-file
.env; ambas PRESENT. Sin cambios de código ni del archivo de credenciales.
El diagnóstico anterior comprobó solo el entorno exportado, no ausencia de claves.
CLI real sin instrumentación: 12:55:35.171934Z, exit 0, PASS; identidad Demo,
16 scopes observados, credit virtual válido y AAPL/1001/Stocks/exchangeId=4.
Tres GET, HTTP 200/200/200, cero mutaciones y cero órdenes; protección intacta.
Evidencia local: runtime/a5-preflight/demo-read-verified.json. El primer intento
cargado falló con WinError 10061 bajo red restringida; PASS fuera de esa restricción,
con TLS/CA local conservados y sin cambiar proxy ni ajustes globales.
202 tests focales PASS, 7 warnings, cero fallos/skips; Ruff check/format, mypy e
inspector Strategy 1 PASS. Suite anterior 719/16 gates conservada; no se atribuye
una repetición completa. A6/shadow/Demo Write no iniciados.
Las notas A5 pendiente inferiores quedan como antecedentes superados.
Detalle, diagnóstico y comando: [A5](docs/A5_PREFLIGHT.md); checks exactos: [VERIFICATION](docs/VERIFICATION.md).

## A5 — implementado localmente; validación externa pendiente, 2026-09-16

Preflight separado de Strategy 1: identidad/scopes Demo, portfolio virtual y
resolución del símbolo A2; tres rutas GET, informe JSON saneado y evidencia local.
REAL/UNKNOWN/ambiguo fallan cerrados; mutaciones bloqueadas incluso en mocks.
Intento propio 12:38:58Z: exit Python 2, ambas claves eToro ausentes, cero requests.
No declarar A5 DONE hasta obtener PASS externo y evidencia sanitizada desde el
proceso con credenciales Demo Read. El hito histórico comunicado se conserva.
A6/shadow/Demo Write no iniciados. Detalles y comando: [A5](docs/A5_PREFLIGHT.md).
Checks exactos en [VERIFICATION](docs/VERIFICATION.md). Cambios previos A2–A4 preservados, sin commit.
719 passed, 7 warnings, cero fallos/skips; 16/16 gates PASS. Ruff/mypy,
cobertura crítica y escaneo de secretos PASS. No se atribuye conexión externa.

## A4 — DONE / replay_as_of_v1, 2026-09-15

Contrato temporal aprobado explícitamente e implementado en el boundary:
historical_download preservado, vistas observed solo cuando available_at <= reloj.
Strategy 1 ORB_RVOL_v1.0, parámetros, configuración y fuentes congeladas intactos.
Dos runs Massive A2 reales consecutivos producen operaciones/summary idénticos:
PASS, run_id 1d21808255a75077d902. AAPL evaluable, cero operaciones por
RVOL_BELOW_THRESHOLD; sin rechazo de disponibilidad ni tuning.

Evidencia: runtime/a4-replay/run-1, run-2 y comparison.json. Código efectivo
SHA-256 5b9fefc95ee1b319425f3172ef7be5418365ce2c734d416e968f092051d25db6;
base HEAD ed456c32355bea05b5c6e04bc4b889ce8bce8ef3, sin commit nuevo.
658 passed, 7 warnings, cero fallos/skips; Ruff check/format, mypy, inspector,
secret scan y recorridos offline PASS. Cobertura 90.641410%; crítica sin reducción.

[Informe y comandos](docs/A4_READINESS.md), [contrato](docs/REPLAY_AS_OF_V1.md),
[verificación](docs/VERIFICATION.md). A2/A3/raw preservados. La disponibilidad
es lógica/modelada, no evidencia realtime. No quedan criterios A4 pendientes.
Las secciones A4 BLOCKED/PENDING inferiores son antecedentes superados.
Shadow, eToro Demo Write, nuevas estrategias y optimización no se inician.

## A4 — BLOCKED por contrato temporal A2/A3, 2026-09-15

Inspección terminada: hashes de las tres capturas A2 y congelación A3 PASS.
Strategy 1 v1 rechaza los datos Massive historical_download con
OBSERVED_AVAILABILITY_REQUIRED; las recepciones son posteriores a la sesión.
No se implementan fases 2–5 ni se presentan cero operaciones como replay válido.
A2 CLOSED y A3 DONE se conservan; las notas A4 PENDING inferiores son antecedentes.
Detalle y propuesta mínima fuera de alcance: [A4_READINESS](docs/A4_READINESS.md).
Evidencia local runtime/a4-readiness/evidence.json.
Regresión focal: 63 passed, 5 warnings, cero fallos/skips; comandos en VERIFICATION.
Siguiente dependencia: decisión explícita del responsable sobre contrato temporal
de investigación; no retrofechar datos ni cambiar Strategy 1 dentro de A4.
Sin cambios productivos, raw, configuración, lock, eToro, commits o publicación.

## A3 — DONE, ORB_RVOL_v1.0, 2026-09-15

Decisiones B1–B4 explícitas incorporadas: RS activa frente a SPY y QQQ, estricta
contra ambos, margen 0; régimen/VWAP confirmation desactivados; ETF no operables.
Parámetros ORB/RVOL/riesgo/costes preservados. Configuración configs/strategy-1-v1.yaml,
snapshot docs/strategy-1-a3-audit.json; inspección scripts/inspect_strategy_v1.py.
A4 PENDING y no ejecutado. Gate HISTORICAL_DOWNLOAD/observed preservado.
Las secciones BLOCKED inferiores son antecedentes superados por la decisión actual.
Verificación: 645 passed, sin fallos/skips, 7 warnings; focal 116 passed.
Ruff/mypy/inspección/hash/secret scan PASS. Cobertura 91.308711%, crítica intacta.

## A3 — continuación histórica, 2026-09-15

15 commits locales examinados; E1 confirma exclusiones iniciales, sin recuperar
filtros completos ni aprobación ETF. B1–B4 PENDIENTE; A3 BLOCKED, A4 pendiente.
Propuestas no implementadas: docs/A3_PENDING_DECISIONS.md. Auditoría/snapshot
ampliados con fuentes y clasificación. Código/configuración y trabajo A2 preservados.
Verificación: 5 tests A3 PASS, 1 warning; hashes preservados, diff check y secretos
PASS. Detalle exacto en docs/VERIFICATION.md; sin nueva suite global atribuida.

## A3 — BLOCKED, 2026-09-15

Auditoría completa de configuración/reglas actuales. No se congela Strategy 1:
faltan decisión de uso SPY/QQQ y reglas RS, régimen, confirmación VWAP; el universo
ETF solicitado contradice common_stock vigente. Código/YAML/ADR coinciden en
extensiones desactivadas; el usuario debe resolver el alcance. A4 pendiente.
Inventario y evidencia: docs/STRATEGY_1_A3_AUDIT.md y strategy-1-a3-audit.json.
Sin cambios funcionales, órdenes, red ni backtest; A2 previo preservado sin commit.
Checks A3: 74 pruebas PASS, cero fallos/skips, 7 warnings; Ruff check/format,
mypy y escaneo de secretos PASS. Comandos exactos en docs/VERIFICATION.md.

## A2 — datos Massive verificados, 2026-09-15

Siete criterios de datos PASS con capturas HTTP reales AAPL/SPY/QQQ y reproducción
offline. Objetivo 14/09/2026, 20 previas desde 14/08; 8.190 barras por símbolo.
ORH 334.83, ORL 331.72, RVOL 1.085297795818647139199521439;
VWAP HLC3 333.8021631970573334714429697. Evidencia: docs/MASSIVE_A2.md y
runtime/a2-massive/offline-final.json. RS calculada contra ambos benchmarks;
régimen NOT_APPLICABLE porque v0.1 no define esa regla. Strategy 1 intacta.
Sin A3, backtesting de rendimiento, órdenes ni eToro. HISTORICAL_DOWNLOAD conservado.
Esta autorización A2 supera las notas históricas de parada tras A1 que siguen abajo.
Verificación final: 598 passed, 7 warnings, sin fallos/skips; ruff y mypy PASS,
cobertura 91.142857%, crítica sin reducción. Comandos exactos en VERIFICATION.

## A1 cerrado — configuración y batería focal final, 2026-09-15

Los dos criterios pendientes están **CLOSED**. `data.provider="massive"` selecciona
MassiveHistoricalProvider usando `data.path` al directorio de captura existente.
Ruta ausente/inválida, captura corrupta y errores Massive fallan explícitamente;
no hay fallback a fixtures/import. La carga normal es offline, histórica y read-only.

Batería focal final Massive: **69 passed**, exit 0, 0 fallos/errores/skips,
5 warnings. Configuración/importación/servicio: **36 passed**, exit 0, 7 warnings.
Gate oficial: **589 pruebas, 16/16 PASS**, 0 fallos/errores/skips; cobertura
**90,705931%**, sin reducción crítica. Detalle exacto: [VERIFICATION](docs/VERIFICATION.md).

La evidencia real MASSIVE_HISTORICAL_RVOL_VERIFIED anterior se conserva.
ORBStrategy, riesgo, ejecución, eToro, Alpaca, persistencia, semántica/cliente
Massive y uv.lock intactos. HISTORICAL_DOWNLOAD y OBSERVED_AVAILABILITY_REQUIRED
no cambian; order_submission_enabled=false. Sin A2, shadow, órdenes ni Demo Write.

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
