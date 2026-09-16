# Tareas — Massive histórico, 2026-09-15

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

Pendientes fuera de A6: A7 no implementado ni autorizado; datos operativos,
elegibilidad/costes/stops externos y reconciliación contable de cierres eToro
siguen sujetos a los bloqueos documentados. A6 solo certifica el pipeline local.
No promover su base offline ni sus evidencias sintéticas a un modo conectado.

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

## A3 — DONE / A4 — PENDING, 2026-09-15

ORB_RVOL_v1.0 congelada con decisiones B1–B4 aprobadas. RS contra SPY+QQQ,
sin régimen/VWAP confirmation ni ETF operables. Snapshot/configuración/tests
verificables; docs/STRATEGY_1_A3_AUDIT.md y VERIFICATION. Notas BLOCKED históricas
inferiores superadas. A4 consume esta versión sin modificarla; no iniciado.

## A3 — BLOCKED / A4 — PENDING

Auditoría realizada; congelación no aprobada por reglas pendientes RS/régimen/VWAP
y conflicto ETF/common_stock. Responsable: usuario, decisión explícita del alcance.
No crear umbrales ni iniciar A4. Fuentes y requisitos de desbloqueo en
docs/STRATEGY_1_A3_AUDIT.md; configuración vigente no es una versión final A3.

## A2 — CLOSED (validación de datos), 2026-09-15

Los siete criterios obligatorios PASS con datos Massive reales y reproducción
offline; evidencia y límites en docs/MASSIVE_A2.md. Benchmarks SPY/QQQ completos.
Régimen NOT_APPLICABLE en v0.1; no se implementó ni validó una regla inexistente.
La autorización actual supera la prohibición histórica de iniciar A2 tras A1.
A3, rendimiento, optimización y órdenes no iniciados.

| Tarea vigente | Estado |
|---|---|
| A1 — Massive seleccionable por configuración | CLOSED: data.provider=massive, data.path directorio validado; dispatch explícito sin fallback |
| A1 — batería focal final Massive | CLOSED: 69 passed, exit 0; configuración/importación/servicio 36 passed |
| Proveedor Massive histórico independiente | IMPLEMENTED; MarketDataProvider.load y CSV/manifiesto existentes |
| AAPL 1m, 20 previas + objetivo 14/09 | VERIFIED: 21/21 sesiones válidas, 8.190 barras regulares, HTTP 200 real |
| Semántica y cobertura | VERIFIED_DOCUMENTED: CTA/UTP consolidado, trades elegibles, split-adjusted; plan no observado |
| Calidad sin rellenar | PASS; raw/recibos/checksums preservados |
| ORH/ORL/V5/media/RVOL independiente vs motor | EXACT_MATCH; MASSIVE_HISTORICAL_RVOL_VERIFIED |
| Pruebas y gates vigentes | PASS: 589 pruebas, 16/16 gates, 90,705931%; sin reducción crítica |
| Alpaca, eToro, ORB/RVOL y riesgo | PRESERVED |
| Shadow, realtime, órdenes y Demo Write | NOT_STARTED / DISABLED / NOT_TESTED |

Detalle reproducible: [MASSIVE_DATA_CONTRACT](docs/MASSIVE_DATA_CONTRACT.md).
Estos dos criterios A1 no están pendientes. A2 no se inicia ni se marca completado.

## Antecedente — preparación para fase shadow, 2026-09-14

| Tarea vigente | Estado |
|---|---|
| Clasificación diferenciada de errores y feed observado | IMPLEMENTED; pruebas locales en VERIFICATION |
| Reporte calidad AAPL/agregado y bloqueo por duplicados | IMPLEMENTED; datos fabricados únicamente |
| Alpaca credenciales/conexión/autenticación | BLOCKED: ALPACA_CREDENTIALS_UNAVAILABLE antes de red |
| Primer gate AAPL/SIP/21 y ORH/ORL/RVOL reales | BLOCKED; no barras ni feed observado |
| Ampliación 10 símbolos/60 sesiones | NOT_STARTED; depende del primer gate completo |
| Baseline fijo real, costes 1x/2x/3x, OOS | NOT_STARTED; datos y disponibilidad pendientes |
| Preparación técnica shadow / arranque | NOT_STARTED / DISABLED |
| Continuidad documental y revisión | Decisión BLOCKED_BY_EXTERNAL_CONFIGURATION; ver SHADOW_READINESS |

La fuente de verdad de gates ejecutados es [VERIFICATION](docs/VERIFICATION.md).
No avanzar tras esta decisión ni considerar mocks como acceso externo.

## Antecedente — Alpaca histórico

La clasificación antigua de insuficiencia por claves ausentes queda superada.

| Tarea | Estado |
|---|---|
| Proveedor Alpaca histórico separado de eToro | IMPLEMENTED; contrato MarketDataProvider preservado |
| SIP AAPL, 20 previas + objetivo | ATTEMPT_BLOCKED_BEFORE_NETWORK; feed efectivo desconocido |
| Volumen y parámetros | DOCUMENTED; no evidencia empírica Alpaca disponible |
| Mapeo, cuotas, páginas y feed identity | CONTRACT_TESTED |
| Comparación ORH/ORL/RVOL | SOFTWARE_TESTED; datos reales NOT_RUN |
| Shadow / órdenes / optimización | NOT_STARTED / DISABLED / NOT_PERFORMED |

Estado actual C: ALPACA_DATA_INSUFFICIENT_FOR_RVOL por contexto Alpaca no disponible;
no atribuirlo a entitlement. Próximo paso: captura desde proceso con variables dedicadas
ya configuradas, según docs/ALPACA_DATA_CONTRACT.md. Gates/commits en VERIFICATION.

## Hito anterior conservado — Market Data eToro

| Tarea actual | Estado |
|---|---|
| Preservar DEMO_READ_VERIFIED comunicado por el usuario | DONE; no repetir diagnóstico de cuenta |
| Capturar Market Data exclusivamente | DONE vía MCP; siete GET HTTP 200, raw y hashes locales |
| Identidad, quote, OHLC 1Min y sesión NY | AUDITED; AAPL/1001/Nasdaq; limitaciones temporales documentadas |
| Semántica de volume y 20 sesiones previas | BLOCKED; consolidación desconocida e histórico insuficiente |
| ORH/ORL/RVOL independiente y contraste motor | PARTIAL; ORH/ORL reales; RVOL y paridad numérica bloqueados; rechazo del motor comprobado |
| Shadow | NOT_STARTED_DATA_QUALITY_BLOCKED |
| Estrategia, riesgo y prohibición de mutaciones | PRESERVED |

Informe vigente: docs/ETORO_MARKET_DATA_VALIDATION.md. Gates y commits en VERIFICATION.
Las filas históricas X01 NOT_CONFIGURED de abajo quedan superadas por el hito Demo Read.

## Historia conservada — cierre de fase 3

| ID | Estado | Evidencia / siguiente acción |
|---|---|---|
| T01 Git | DONE | Identidad efectiva verificada. Base A y recuperación B preservadas sin mezclar staging; ramas locales y C reales |
| T02 Datos/estrategia local | LOCAL_VERIFIED | Mismos ORB/RVOL, 20 warmups y riesgo; importación sintética de B aprobada |
| T03 Ejecución/persistencia | LOCAL_VERIFIED | Propiedad, parciales, recuperación, costes y exposición separados; no inferir flat del cierre v1 |
| T04 Contratos | DOCUMENTED / CONTRACT_TESTED / PARTIALLY_BLOCKED | Matriz por campo en ETORO_API_AUDIT, v2 distinto de v1 y consultas de soporte no enviadas |
| T05 Investigación | BLOCKED_DATA | Ninguna muestra real validada, cálculo real, replay causal real ni shadow |
| T06 Panel | HTTP_VERIFIED / VISUAL_NOT_REPRODUCED | Chrome exit 1; depuración local no iniciada; sin cambios de seguridad |
| T07 Software | LOCAL_VERIFIED | A 358, B 420, C 435 pruebas; cada capa con su evidencia; 16 gates por batería |
| X01 | NOT_CONFIGURED | Titular: claves propias de aplicación y usuario Demo Read en el proceso; luego preflight existente |
| X02 | BLOCKED_EXTERNAL_DATA | Titular: archivo licenciado o acceso propio suficiente; 21 sesiones, mismo feed y semántica temporal auditada |
| X03 | DISABLED_THIS_PHASE | Ningún envío, cancelación, cierre o stop externo; resolver lectura no habilita mutaciones |
| X04 | EXTERNAL_NOT_OBSERVED / ACCOUNTING_BLOCKED | Soporte/integración: correlación legacy, fills/revisiones, costes finales y completitud del historial |
| X05 | NOT_EXECUTED | No remoto, CI remoto, publicación ni envío de preguntas a terceros |

Se añadieron únicamente regresiones de riesgos encontrados, sin modificar gates ni
umbrales para aumentar el recuento. El estado 2 de lookup quedó incluido junto con
los demás; 9/10 nunca se interpretan como cero ejecución. No se atribuyen las 420
pruebas de B a A ni las 435 de C a una conexión externa.

La fase termina aquí en cuanto a ampliación de producto. HANDOFF indica responsable,
evidencia faltante y acción mínima de cada dependencia. Identidad Git resuelta:
no pedirla otra vez. No crear fixtures ni infraestructura para ocultar X01/X02/X04.
