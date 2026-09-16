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

# Continuidad — Massive histórico, 2026-09-15

El diagnóstico Massive ahora carga únicamente MASSIVE_API_KEY de .env raíz;
ignora la clave heredada, no interpola ni hace fallback. La entrada sigue MISSING.
El usuario debe configurarla localmente; no copiar la variable Windows no verificada.
21 tests aislados PASS; .env, trading, contratos y A7 sin cambios.

## Rectificación de credencial Massive — 2026-09-16

Resultado vigente CREDENTIAL_SOURCE_UNVERIFIED. No presentar los tres 403 como
prueba de plan insuficiente o de indisponibilidad Massive. El probe usó la variable
MASSIVE_API_KEY del proceso como Bearer; PRESENT no prueba validez. Hoy aparece
en proceso y Windows User, no en .env/Machine. No hay fingerprint Massive previo
que identifique el valor enviado. Preservar raw y la rectificación separada.
No se modifican A7, contratos, secretos ni código de trading.

## Investigación Massive operativo — 2026-09-16

CONTRACT_CHANGE_NOT_JUSTIFIED: tres GET Last NBBO, AAPL/SPY/QQQ HTTP 403.
No atribuir plan específico al 403 ni inventar métricas sin cotizaciones.
Evidencia runtime/massive-operational/live-20260916; contratos eToro consultados
documentan limitIOC/limitRate, distinto de MIT, sin ejecución ni integración.
A7 permanece PARTIAL/BLOCKED, 3s intacto, REAL fuera de capacidad. Sin A8.
12 tests spike, 268 focales, 873 completos y 16/16 gates PASS; normativa intacta.
La continuación exige evidencia operativa antes de proponer cambios de contrato.
Informe: [viabilidad](docs/MASSIVE_OPERATIONAL_FEASIBILITY.md).

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

## A3 definitivo — Strategy 1 v1, 2026-09-15

ORB_RVOL_v1.0 implementada y congelada según decisiones explícitas B1–B4.
Cargar configs/strategy-1-v1.yaml; verificar con scripts/inspect_strategy_v1.py.
RS evalúa primera candidata ORB con SPY/QQQ del mismo minuto disponibles al decidir;
si falla, no intenta otra barra. ETF/reference-only nunca alcanzan señales/sizing.
Importador multiinstrumento existente sirve DataBundle; fixtures antiguos sin
benchmarks rechazan RS. Massive A2 sigue histórico, no observed. A4 no se ejecutó.
Snapshot preserva auditoría histórica; v0.1 continúa disponible. Código/riesgo/
ejecución/proveedores previos se conservan salvo cambios A3 en config.py y orb.py.
Base y HEAD ed456c32355bea05b5c6e04bc4b889ce8bce8ef3; sin commit solicitado
explícitamente, se entrega working tree revisable con cambios A2/A3 preservados.
Nueva versión requerida para cualquier modificación de hipótesis durante A4.
Gates finales: 645 passed / 7 warnings / cero fallos-skips; focal 116 passed.
Ruff check/format, mypy, inspector y scanner PASS. Cobertura 91.308711%, crítica
sin reducción; logs/huellas/comparación en runtime/a3-freeze y docs/VERIFICATION.md.

## A3 — historial agotado localmente, 2026-09-15

Continuación sobre la misma base ed456c3 y cambios A2/A3 sin commit. Se revisaron
15 commits alcanzables, -S/-G/blame/show y versiones de archivos; logs y hashes
previos en runtime/a3-history. No hay nueva aprobación de RS/régimen/VWAP/ETF.
Bootstrap:169 excluye ETF explícitamente; FUT-001/002 dejan extensiones pendientes.
El siguiente paso es revisión humana de B1–B4 en docs/A3_PENDING_DECISIONS.md,
no otra búsqueda equivalente ni activación inferida. A3 BLOCKED, A4 no iniciado.
Tests existentes A3: 5 passed, 1 warning, exit 0; hashes y conservación PASS,
escaneo 161 candidatos/cero hallazgos. Código, configuración y tests sin cambios.

## A3 — entrega de auditoría bloqueada, 2026-09-15

Base `ed456c32355bea05b5c6e04bc4b889ce8bce8ef3`, árbol con A2 sin commit.
Se preservaron diff/estado previos en runtime/a3-audit. No confundir esa base
con el árbol actual ni hacer un commit que mezcle A2 bajo un título exclusivo A3.
Pendientes B1–B4: RS/SPY/QQQ, régimen, confirmación VWAP y universo ETF.
La pregunta de alcance solicita conservar exclusiones v0.1 o definir nueva versión;
sin decisión no se puede cerrar A3. Inventario/snapshot y siguiente paso en
docs/STRATEGY_1_A3_AUDIT.md. Tests nuevos auditan estado actual, no congelación.
A4 pendiente; cualquier cambio de reglas requiere nueva versión y revisión A3.
Verificación A3: 74 passed, 7 warnings, exit 0; Ruff check/format y mypy PASS;
cero secretos; sin fallos/skips. runtime/a3-audit/tests.log y tests.xml.

## Entrega A2 — 2026-09-15

Siete criterios de datos PASS, captura real SPY/QQQ HTTP 200 y AAPL previo reutilizado.
Reproducir con el comando de docs/MASSIVE_A2.md; raw inmutable y privado, sin Git.
Informe completo runtime/a2-massive/offline-final.json; manifiesto portable
 docs/massive-a2-manifest.json. El intento de red fallido se conserva.
Cambios mínimos: allowlist histórica AAPL/SPY/QQQ, identidad ETF en benchmarks,
auditor A2 y CLI explícita. Capturas antiguas sin symbol siguen siendo AAPL,
con endpoint y ticker validados; nunca fallback a otro proveedor.
Régimen no existe en v0.1: no inventar reglas. RS/VWAP siguen inactivos.
No continuar A3. Resultados de checks A2 en docs/VERIFICATION.md.
598 pruebas PASS, 7 warnings, cero fallos/skips; ruff check/format y mypy PASS.
Cobertura 91.142857%, crítica intacta; checks.json conserva huella y comparación.

## Cierre exclusivo A1 — 2026-09-15

Partida `adb2e10`, árbol limpio. Ambos criterios pendientes quedan **CLOSED**:
Massive seleccionable por configuración normal y batería focal final explícita.
No volver a diagnosticarlos como pendientes; no continuar con A2.

`DataConfig.provider="massive"` reutiliza `data.path`: directorio existente con
capture.json y páginas raw; no acepta manifest externo. Configuración valida
la ruta y el lector Massive existente valida contenido/checksums. load_bundle
resuelve fixtures/import/massive explícitamente y propaga MassiveDataError.
No descarga, no requiere clave Massive ni cambia disponibilidad histórica.
Ejemplo YAML y CLI: docs/MASSIVE_DATA_CONTRACT.md.

Pruebas finales con capturas fabricadas, sin raw real en tests: Massive completo
**69 passed / 0 fallos / 0 errores / 0 skips / 5 warnings / exit 0**;
configuración, importación y servicio **36 passed / 7 warnings / exit 0**.
Gate oficial **16/16 PASS**, **589 passed / 0 fallos / 0 errores / 0 skips /
7 warnings**; cobertura **90,70593149540518%**, crítica idéntica a la partida.
Huella de código común a focales y gates:
`b2c1ae5541d6f3f751ade6f579ed808a1be1c72e63eaa9160a3279ea3888ac80`.
Evidencia exacta en runtime/a1-massive-config-20260915 y docs/VERIFICATION.md.

Producción modificada únicamente en config.py y load_bundle de service.py.
Lector/cliente/auditor Massive, ORBStrategy, riesgo, ejecución, bróker, Alpaca,
persistencia, reglas observed, order_submission_enabled, uv.lock y manifiesto
histórico real sin cambios. Se conserva MASSIVE_HISTORICAL_RVOL_VERIFIED previo;
esta fase no repite ni amplía validación externa. Sin shadow, Demo Write ni órdenes.

## Publicación autorizada — 2026-09-15

Destino indicado por el usuario: https://github.com/epr3202/Bot-trading.git.
Remoto local `origin`; publicación de la rama actual en `refs/heads/main`.
Se conserva la rama local feat/phase3-readonly-evidence y el historial existente.
Antes de publicar: remoto vacío por `git ls-remote --symref`; 13 commits y
248 blobs hasta `710e3e9` escaneados sin secretos/rutas privadas. El incremento
documental se revisa y escanea por separado. Sin cambios de código ni repetición
de pruebas: huella idéntica a la batería de 574 pruebas y 16/16 gates.
La autorización del usuario cubre esta publicación; no habilita trading,
shadow o Demo Write. No se suben datos raw, claves ni estado local.
Los resultados de CI remoto deben verificarse por separado de los gates locales.

## Continuidad de la integración Massive

Partida limpia `262944f`; misma rama local feat/phase3-readonly-evidence.
Massive agregado como proveedor independiente histórico read-only. No se cambian
Alpaca, eToro, estrategia, riesgo, ejecución, configs ni lock. La clave dedicada
estaba presente en el proceso; no se leyó ningún perfil ni se guardó su valor.

Primer intento restringido CONNECTIVITY_FAILED antes de respuesta. Repetición
con permiso de red: un GET histórico, HTTP 200 a las 12:27:06.148056 UTC,
17.588 barras raw y 8.190 regulares; 21/21 sesiones válidas, objetivo 14/09.
**MASSIVE_HISTORICAL_RVOL_VERIFIED**, igualdad exacta de cinco métricas:
ORH 334.83, ORL 331.72, V5 1834725.760868, media 1690527.49202725,
RVOL 1.085297795818647139199521439. Sin latencia de datos inventada.

Raw inmutable: data/raw/massive/20260915T122702-6a68f76c.
Informe real: runtime/massive-audits/20260915T122702-6a68f76c/result.json.
Contrato, esquema, semántica documental y CLI: docs/MASSIVE_DATA_CONTRACT.md.
Solo manifiesto saneado en docs/massive-historical-manifest.json; no dataset en Git.
Código `8ed65eb`; 574 pruebas, 16/16 gates, cobertura 90,525210%, sin fallos/skips
ni reducción crítica. Comandos y huellas exactos en docs/VERIFICATION.md.
Baseline anterior preservado en runtime/massive-phase-20260915T071442/prior-*.
Gates finales estables en la misma carpeta, final-{verification.json,coverage.json,test-results.xml}.
Reauditoría offline: runtime/massive-audits/20260915T123151-9e27df3a/result.json;
misma aritmética y checksums. CSV real importado con 8.190 barras, gate preservado.

El hito solo acredita histórico AAPL. No acredita señales causales, latencia
realtime ni rentabilidad. El motor rechaza HISTORICAL_DOWNLOAD con
OBSERVED_AVAILABILITY_REQUIRED; cero candidatos/señales. No modificar observed,
warmup o estrategia para saltarlo. El nombre del plan no está en el endpoint;
se acredita acceso, no una suscripción concreta. Cierres extraordinarios y
correcciones históricas siguen siendo límites; DST/cierre temprano se prueban
localmente, no se observaron en esta ventana.

Esta fase termina en la validación histórica. No iniciar shadow ni Demo Write.
Mantener eToro DEMO_READ_VERIFIED previo, entries_armed=false,
external_mutations=DISABLED y order_submission_enabled=false.
Alpaca conserva su bloqueo externo anterior; no se volvió a consultar eToro.

## Antecedente — preparación para fase shadow, 2026-09-14

Partida limpia `43c9cc5b7d6366ee72d38dd17542ec7341e4e7e1`, misma rama local.
Resultado vigente: BLOCKED_BY_EXTERNAL_CONFIGURATION, motivo
ALPACA_CREDENTIALS_UNAVAILABLE; SHADOW_NOT_READY. Ambas variables ausentes.
El comando oficial de captura devuelve ese motivo antes de red, sin raw Alpaca.
Evidencia en runtime/alpaca-audits/20260914T195435-d5744088/result.json;
comprobaciones previas preservadas en runtime/shadow-readiness-20260914/prior-*.

Status/razón separados; timeout es conectividad, 429 es rate limit y la negativa
SIP no se registra como entitlement aprobado. Feed sin eco queda desconocido aun
en capturas antiguas; duplicados y volumen cero bloquean calidad. Auditoría genera
data-quality.json; parseos interrumpidos dejan conteos desconocidos. No cambian
estrategia, riesgo, transporte eToro, Python ni lock. Commit código `b7a17b7`;
`scripts/verify.py` final: **512 pruebas, 16/16 gates, 90,488615% de cobertura**,
sin fallos/skips y módulos críticos sin reducción. Evidencia exacta:
[VERIFICATION](docs/VERIFICATION.md).

Siguiente acción externa: titular del acceso ejecuta el comando desde un proceso
con las variables dedicadas heredadas, sin pegar secretos ni cambiar a IEX. Después
resolver evidencia explícita del feed y validar AAPL/21. Ampliación a 60 sesiones,
baseline real y preparación shadow siguen condicionados, no ejecutados. El gate
de disponibilidad histórica es un bloqueo adicional: no backdatear ni falsificar
observed para generar señales. Secuencia completa: [SHADOW_READINESS](docs/SHADOW_READINESS.md).

Se mantienen DEMO_READ_VERIFIED histórico, entries_armed=false,
external_mutations=DISABLED, order_submission_enabled=false y Demo Write NOT_TESTED.
No repetir lectura de cuenta, iniciar shadow ni continuar después de esta decisión.

## Antecedente — Alpaca histórico

La etiqueta antigua de insuficiencia por ausencia de credenciales queda corregida
por el estado vigente anterior; sus artefactos raw y resultados se preservan.

Se continuó desde 134844b y árbol limpio. Baseline y gates anteriores preservados en
runtime/alpaca-phase-20260914T184730. DEMO_READ_VERIFIED no se volvió a diagnosticar;
eToro audit-only mantiene ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL.

Alpaca incorporado como proveedor independiente sin SDK: data/alpaca_http.py solo
GET data.alpaca.markets/v2/stocks/bars; data/alpaca.py carga archivos a DataBundle;
data/alpaca_audit.py compara raw/Fraction con el cálculo Decimal del motor.
CLI explícita scripts/audit_alpaca_history.py; salida CSV/manifiesto compatible con
provider=import existente. Fixture sigue predeterminado. RiskEngine, ExecutionEngine,
el adaptador eToro y sus rutas no cambian. No se amplió MarketDataProvider.

Consulta inicial prevista AAPL/1Min/SIP/split: 2026-08-13 13:30Z a 2026-09-11 19:59Z
(end inclusivo), 20 sesiones previas más objetivo cerrado 11/09. Intento real:
ALPACA_CREDENTIALS_UNAVAILABLE antes de red, sin bytes ni feed efectivo.
Estado C: ALPACA_DATA_INSUFFICIENT_FOR_RVOL; no es evidencia de falta de entitlement.
Resultado original en runtime/alpaca-audits/20260914T185623-4eab7c52/result.json;
manifiesto saneado versionado en docs/alpaca-historical-manifest.json.
No solicitar claves ni buscarlas en perfiles/otros proyectos. El siguiente paso es
ejecutar el comando documentado desde un proceso con ALPACA_API_KEY/ALPACA_API_SECRET
ya disponibles, sin volver a consultar eToro. No comprar plan ni cambiar a IEX.

La aritmética ORH/ORL/RVOL existente se extrajo a ORBStrategy.opening_metrics, usada
también por process_session. No cambian fórmulas, filtros, ranking, riesgo o TTL.
La comparación histórica usa esa parte numérica y ejecuta process_session por
separado: el gate OBSERVED_AVAILABILITY_REQUIRED permanece. Tolerancia absoluta
1e-12 y relativa cero; resultado real NOT_RUN. Nunca se declara observed ni se
inventa latencia para pasar la prueba. Historical snapshots conservan correcciones
como posibilidad; no prueban primera recepción ni señales realtime.

38 pruebas nuevas Alpaca aprobadas: mapping, identidad de feed, tiempos, huecos,
duplicados, paginación, HTTP, cuotas, CSV y cálculo independiente. 15 pruebas previas
de estrategia/datos también aprobadas. Batería final: 491 pruebas, 16/16 gates;
cobertura 90,070065% y todos los módulos críticos mantienen exactamente la cobertura
previa. Código estable, Python/lock conservados; final-gates dentro del baseline
guarda las salidas exactas. Ver commits en VERIFICATION.
Scripts de gates y fixtures de tests retiran también las variables Alpaca, y scanner
incluye sus nombres. Datos raw solo en data/raw/alpaca; resultados en runtime.

Guardas mantenidas: entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED. No shadow en esta fase,
ni siquiera si un histórico llega a aprobar; WebSocket es un alcance posterior.
Documentación del esquema, contrato y estados en docs/ALPACA_DATA_CONTRACT.md.

## Hito anterior conservado — Market Data eToro

El usuario confirmó DEMO_READ_VERIFIED desde Bot 3, con conexión, autenticación e
identidad Demo verificadas y cero escrituras. Hito registrado en baseline.json,
sin repetir consultas de cuenta. X01 de las secciones históricas está superado;
no pedir claves ni reiniciar diagnóstico de conectividad.

Esta fase obtuvo siete respuestas HTTP 200 exclusivamente Market Data mediante
execute_read del conector eToro. La consulta local de instrumentos no pudo iniciarse
con el contexto de proceso del agente; no se atribuye al bot la captura MCP.
Datos reales, sin mocks de adquisición: AAPL/1001/Nasdaq, bid/ask, 1.000 minutos
asc/desc, 30 diarios y repetición de 10 minutos. No se consultó elegibilidad, cuenta,
portafolio ni otra ruta de trading. No se cambió la allowlist del transporte.

Resultado: ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL. Volumen de unidades desconocidas;
0/20 sesiones previas completas, 0/20 aperturas históricas. La ventana regular actual
no tiene huecos entre minutos ya cerrados, pero el histórico requerido no cabe en
el contrato de 1.000 velas sin fecha/cursor. ORH=334,54, ORL=331,72 y volume de
apertura=1.181.044 calculados independientemente sobre AAPL 2026-09-14. RVOL y
comparación numérica con el motor bloqueados; este rechaza con
OBSERVED_AVAILABILITY_REQUIRED, sin alterar ninguna regla ni falsear disponibilidad.

Raw: data/raw/etoro-market-20260914T164913. Informe/CSV/manifiestos y hashes:
runtime/market-audit-20260914T164913/final-analysis. Cuerpos raw inmutables, revisiones
separadas y sin datos privados en Git. `scripts/audit_etoro_market_data.py` reproduce
el análisis sin red; requiere directorio de salida nuevo. Diez regresiones nuevas
cubren exclusión de vela abierta, huecos/duplicados, denominador sin hoy, OHLC,
zonas y cierre temprano. Estado de gates en VERIFICATION.

Batería final: 453 pruebas sin fallos/skips, 16/16 gates, cobertura 90,686683%.
Huella estable y lock intacto; evidencia final en final-gates dentro de la carpeta
de auditoría. Commit local `2d6eec3` conserva el cambio previo de proxy/CA; el commit
de auditoría contiene este informe y el analizador sin red. No hay publicación.

Shadow NO INICIADO. Se mantienen entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED. El parser de quote
rechaza el timestamp sin offset observado; el análisis lo interpreta como UTC por
contrato y mide 43,076s hasta retorno de herramienta, por encima del gate de 3s.
Esto también impide tratar la captura como cotización fresca operativa.

Siguiente dependencia: volumen consolidado/ajustes acreditados y 21 sesiones de
minutos de un proveedor apto, preservando MarketDataProvider e importación existentes;
o aclaración contractual de eToro y cobertura demostrada. No reducir warmup ni usar
volumen diario/ticks para simular RVOL. Los bloqueos contables X04 siguen vigentes;
resolver datos tampoco autoriza Demo Write. Detalle en ETORO_MARKET_DATA_VALIDATION.

## Historia conservada — fases anteriores

Actualización 2026-09-14: el usuario solicitó adaptar el manejo de proxy del script
de oficios. Se revisó `oficios.py` en la carpeta de generación/recuperación sin
ejecutarlo ni importar credenciales. `create_http_client` aplica proxy del entorno
y prioridad CA local `certs/epm-root.cer` → `REQUESTS_CA_BUNDLE` → defaults HTTPX.
No se desactiva TLS ni se cambia configuración global. CA/proxy inválidos producen
error redactado sin fallback. Transportes inyectados no heredan el entorno; el
panel local mantiene conexión directa. No cambian guardas de escritura, identidad,
reservas, propiedad, recuperación ni datos/tiempos de disponibilidad.

Verificación: ocho pruebas nuevas aprobadas con
`.\scripts\uv.ps1 run --frozen pytest -q tests/test_corporate_network.py`.
Primer pase completo: 15/16 gates; dos pruebas nuevas parcheaban el símbolo
incorrecto de HTTPX. La guarda de sockets bloqueó la conexión externa y hubo
resolución DNS fallida del proxy ficticio; ninguna consulta de cuenta ni respuesta
externa. Se corrigió el aislamiento. Evidencia inicial conservada en
`runtime/proxy-verification-first.json`. Batería final:
`.\scripts\uv.ps1 run --frozen python scripts/verify.py`, salida 0;
16/16 gates, 443 pruebas sin errores/fallos/skips, cobertura 90,686683% y módulos
críticos por encima del 90%. Ruff check/format, mypy, escaneo de secretos, recorridos
offline, bloqueos negativos, build y sintaxis JS aprobados. Evidencia exacta en
`runtime/verification.json`, credenciales retiradas y código estable durante checks.

Construcción del cliente con entorno actual aprobada, sin solicitudes HTTP.
Proxy presente; CA corporativa no configurada ni encontrada en la carpeta de
referencia. Falta aportar CA autorizada mediante la ruta/variable documentada en
OPERATIONS_RUNBOOK y comprobar conectividad en un alcance autorizado. No se
realizaron lecturas de cuenta, operaciones externas, commits ni publicación.
Python 3.12.12 y uv.lock conservados. Los bloqueos históricos siguientes permanecen.

Proyecto existente C:/Users/epulgare/Nueva carpeta/Bot 3. Se mantuvieron Python
3.12.12, uv 0.12.12, uv.lock, ORB_RVOL_v0.1, 20 warmups, presupuesto, riesgo y TTL.
No hubo nuevo repositorio, migración de API, proveedor nuevo ni revisión independiente.
Revisión propia del agente; no se delegó esta fase.

Las dos capas ya están versionadas. Base A en main:
`6af05f1b16b8e3488a5cd959dc0e7f889b258fd6` (123 archivos idénticos al índice
original y su manifiesto, 358 pruebas en instalación aislada).
B en recovery/phase2-reviewed:
`ef8bf5564f6e15bd04ae084c18cd63dd27ba380b` (33 modificados + seis nuevos,
420 pruebas, importación y paquete offline).
C en feat/phase3-readonly-evidence:
`b51506a97771d04a5edfb45d46e8fac4c31f307f` (435 pruebas/16 gates).
La documentación de fase 2 que menciona identidad pendiente queda conservada en B
como historia; el bloqueo fue resuelto por el usuario. No volver a solicitarlo.

Fase 3 corrigió riesgos concretos: lookup exige exactamente un identificador;
una respuesta action=close no se contabiliza como apertura; status.id debe ser
entero y los estados 3/5/9/10 requieren evidencia de cantidad ejecutada. Los estados
9/10 conservan fills aunque su remanente sea terminal. El detalle v1 de cierre ya
no permite inferir remainingUnits a partir de la cantidad solicitada. La exposición
explícita del lookup de apertura continúa separada del libro, caja y PnL.

Lookup v2 sí documenta action=open/close, IDs de cuenta/orden/posición y estado.
OpeningData sigue siendo apertura; no existe closingData en el esquema consultado.
No extrapolar el enum v2 a statusID v1. Matriz de campos, diferencias guía/OpenAPI,
idempotencia por versión y preguntas de soporte NO ENVIADAS en ETORO_API_AUDIT.
La normalización contable de cierres y recuperación legacy sin ID siguen bloqueadas.

| Bloqueo | Responsable | Evidencia pendiente | Acción mínima |
|---|---|---|---|
| X01 Demo Read NOT_CONFIGURED | Titular de cuenta/aplicación | Clave de aplicación y clave de usuario Demo Read en el proceso; identidad/scopes/portfolio verificados por el bot | Configurarlas localmente según OPERATIONS_RUNBOOK y ejecutar el preflight existente una vez tras el cambio; no pegar secretos |
| X02 BLOCKED_DATA | Titular del acceso/dataset | CSV/Parquet autorizado, 21 sesiones completas, volumen comparable, ajustes/procedencia/tiempos; o acceso ya licenciado sin gasto | Aportar el archivo y manifiesto localmente; el candidato público de cuatro registros es insuficiente y su descarga falló con WinError 10061 |
| X04 Contabilidad externa BLOCKED | Soporte eToro y responsable de integración | Enlace v1→lookup, enum legacy, fills estables/revisiones, costes/moneda y completitud histórica | Obtener aclaraciones contractuales; revisar ejemplos redactados de operaciones existentes solo con acceso autorizado; no crear operaciones de prueba |
| Visual NOT_REPRODUCED | Responsable del entorno local | Arranque de depuración Chrome y captura actual | Investigar en un entorno permitido; esta fase agotó su único intento sin cambiar seguridad ni cerrar sesiones personales |
| X03 Mutaciones DISABLED | Futuro alcance explícito del usuario | Todos los gates operativos y autorización separados | No activar nada al resolver lectura o datos |
| X05 CI remoto/publicación | Usuario, si lo solicita en otro alcance | Destino y autorización explícitos | Ninguna acción ahora |

Preflight real del proceso: 2026-09-10T19:24:54Z, exit 2; ETORO_API_KEY y
ETORO_USER_KEY ausentes, sin .env. Ninguna consulta de cuenta. Las suites también
ejercitan el caso negativo con credenciales retiradas; no equivalen a reintentos de
la configuración real. El conector solo aportó catálogo/OpenAPI.

La búsqueda pública de datos fue acotada a los proveedores ya auditados. No se
adquirieron servicios, créditos ni suscripciones. No hay archivo real validado ni
ORH/ORL/RVOL real calculado. Un histórico final real no es sintético por carecer de
recepción histórica: puede permitir aritmética exploratoria, pero no sortear el
gate observed del motor ni demostrar latencia. Sin shadow ni tarea futura.

Panel HTTP aprobado; Chrome salió 1 a las 19:33:13Z por depuración no iniciada.
Servidor de comprobación cerrado y token retirado. No usar captura del bootstrap
como verificación actual. Las guardas de mutación siguen cubiertas por tests con
transporte espía, incluidos permisos antiguos: ninguna solicitud de escritura
llega a la red. La consulta del bróker no está conectada al runner operativo.

Evidencia local ignorada: runtime/phase3 (A aislada, B/C suites, huellas de capas,
preflight, descarga fallida y navegador). Evidencia portable y matriz Git en
docs/VERIFICATION.md y docs/GIT_WORKFLOW.md. El commit documental posterior a C
no cambia software. Consultar `git log --format=fuller` y `git status --short`
para el historial y estado reales. Sin remotos, publicación o mutación de cuenta.

Criterio de parada alcanzado: capas preservadas, revisión contractual focalizada
agotada y recorridos externos posibles intentados. No abrir otra ronda de motores,
fixtures o interfaz para sustituir las dependencias anteriores.
