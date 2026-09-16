## A7 WebSocket: spike bloqueado por handshake HTTP 403

Revision contractual permite eToro WebSocket conservando el gate de 3 s.
Diagnostico aislado: el handshake devuelve HTTP 403 con pagina Proxy WebGateway
EPM, antes de Authenticate; cero eventos, suscripciones u ordenes. No se ha
integrado el stream al runner ni se ha cambiado codigo productivo, riesgo,
Strategy 1, A6, Massive, contratos congelados o uv.lock. Reconnect productivo
y validacion en mercado abierto pendientes; no declarar migracion PASS.
Detalle: docs/A7_WEBSOCKET.md (desde docs: A7_WEBSOCKET.md).
A7 PARTIAL/BLOCKED: upgrade WebSocket rechazado por la infraestructura de red.

# Índice de tareas pendientes

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
Detalles y partes pendientes: [continuación A7](A7_COMPLETION_ATTEMPT.md).
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
Diseño, pruebas, matriz DoD y límites: [A7](A7_DEMO_ONLY.md).
Checks exactos: [VERIFICATION](VERIFICATION.md).
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
Detalles: [A6](A6_SESSION.md); comandos y checks: [VERIFICATION](VERIFICATION.md).
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
Detalle, diagnóstico y comando: [A5](A5_PREFLIGHT.md); checks exactos: [VERIFICATION](VERIFICATION.md).

## A5 — implementado localmente; validación externa pendiente, 2026-09-16

Preflight separado de Strategy 1: identidad/scopes Demo, portfolio virtual y
resolución del símbolo A2; tres rutas GET, informe JSON saneado y evidencia local.
REAL/UNKNOWN/ambiguo fallan cerrados; mutaciones bloqueadas incluso en mocks.
Intento propio 12:38:58Z: exit Python 2, ambas claves eToro ausentes, cero requests.
No declarar A5 DONE hasta obtener PASS externo y evidencia sanitizada desde el
proceso con credenciales Demo Read. El hito histórico comunicado se conserva.
A6/shadow/Demo Write no iniciados. Detalles y comando: [A5](A5_PREFLIGHT.md).
Checks exactos en [VERIFICATION](VERIFICATION.md). Cambios previos A2–A4 preservados, sin commit.
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

[Informe y comandos](A4_READINESS.md), [contrato](REPLAY_AS_OF_V1.md),
[verificación](VERIFICATION.md). A2/A3/raw preservados. La disponibilidad
es lógica/modelada, no evidencia realtime. No quedan criterios A4 pendientes.
Las secciones A4 BLOCKED/PENDING inferiores son antecedentes superados.
Shadow, eToro Demo Write, nuevas estrategias y optimización no se inician.

## A4 — BLOCKED por contrato temporal A2/A3, 2026-09-15

Inspección terminada: hashes de las tres capturas A2 y congelación A3 PASS.
Strategy 1 v1 rechaza los datos Massive historical_download con
OBSERVED_AVAILABILITY_REQUIRED; las recepciones son posteriores a la sesión.
No se implementan fases 2–5 ni se presentan cero operaciones como replay válido.
A2 CLOSED y A3 DONE se conservan; las notas A4 PENDING inferiores son antecedentes.
Detalle y propuesta mínima fuera de alcance: [A4_READINESS](A4_READINESS.md).
Evidencia local runtime/a4-readiness/evidence.json.
Regresión focal: 63 passed, 5 warnings, cero fallos/skips; comandos en VERIFICATION.
Siguiente dependencia: decisión explícita del responsable sobre contrato temporal
de investigación; no retrofechar datos ni cambiar Strategy 1 dentro de A4.
Sin cambios productivos, raw, configuración, lock, eToro, commits o publicación.

## A3 — DONE / A4 — PENDING, 2026-09-15

B1–B4 resueltos por decisión explícita del responsable e incorporados a
ORB_RVOL_v1.0. Configuración, snapshot, RS causal y pruebas en
[especificación final](STRATEGY_1_A3_AUDIT.md); resultados en VERIFICATION.
Los bloqueos históricos inferiores están superados para A3. Régimen, VWAP, ETF
y otras variantes de investigación siguen siendo posibles tareas futuras con
nueva versión; no se activan ni se optimizan dentro de v1. A4 no se inicia.

## A3 — búsqueda histórica terminada; decisiones pendientes

B1–B4 permanecen PENDIENTE tras revisar 15 commits y todas las referencias locales.
E1 acredita políticas iniciales; E2 acredita helpers/tipos; E3 persiste para las
reglas completas solicitadas. Revisar/aprobar las opciones explícitas B1–B4 en
[A3_PENDING_DECISIONS](A3_PENDING_DECISIONS.md). No se implementaron propuestas.
A4 sigue pendiente y no se inicia. El inventario previo y los cambios A2 se preservan.

## A3 — BLOCKED, 2026-09-15

- B1: política SPY/QQQ y regla de entrada por fuerza relativa sin definir.
- B2: indicadores, timeframe, lookbacks y umbrales de régimen inexistentes.
- B3: VWAP HLC3 existe, pero su confirmación de entrada no está especificada.
- B4: solicitud acciones/ETF frente a common_stock exclusivo en estrategia/riesgo.

Responsable: usuario; confirmar exclusión explícita de los cuatro puntos para
congelar v0.1 o aportar decisiones para una nueva versión. No se congeló una
configuración ni se marcó DONE. [Fuentes y parámetros](STRATEGY_1_A3_AUDIT.md).
A4 permanece pendiente/bloqueada; no consume el snapshot de auditoría como versión final.
La solicitud actual autoriza auditar A3 y supera la nota histórica de A2 inferior.

## A2 — completado para datos, 2026-09-15

Siete criterios PASS con Massive real AAPL/SPY/QQQ, 21 sesiones y reproducción
offline. [Evidencia A2](MASSIVE_A2.md). No queda bloqueo de datos A2.
Régimen no definido en Strategy v0.1; no se atribuye validación a ese filtro.
A3 no autorizado ni iniciado. Las notas de A1 siguientes son históricas.

## A1 — ambos criterios cerrados, 2026-09-15

La selección de Massive por configuración y la ejecución focal final completa
ya están CLOSED: proveedor massive con directorio explícito y sin fallback;
69 pruebas Massive y 36 de configuración/importación/servicio aprobadas.
Gate global 589 pruebas, 16/16 PASS, sin reducción de cobertura crítica.
Evidencia en [VERIFICATION](VERIFICATION.md). No volver a abrir esos dos puntos.
A2 no se aborda ni se marca completado; ningún otro pendiente se elimina aquí.

[TASKS](../TASKS.md) es la fuente de verdad de tareas. [HANDOFF](../HANDOFF.md)
identifica responsables y siguientes acciones. La secuencia condicionada de esta
fase y sus bloqueos figura en [SHADOW_READINESS](SHADOW_READINESS.md).

Pendientes previos de Alpaca, fuera de este cierre: variables dedicadas en el proceso, evidencia
del feed SIP, AAPL/21 sesiones y calidad/paridad. Ampliación, baseline real y
preparación shadow quedan detrás de esos gates, sin autorización de arranque.
