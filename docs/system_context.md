## A7 WebSocket: spike bloqueado por handshake HTTP 403

Revision contractual permite eToro WebSocket conservando el gate de 3 s.
Diagnostico aislado: el handshake devuelve HTTP 403 con pagina Proxy WebGateway
EPM, antes de Authenticate; cero eventos, suscripciones u ordenes. No se ha
integrado el stream al runner ni se ha cambiado codigo productivo, riesgo,
Strategy 1, A6, Massive, contratos congelados o uv.lock. Reconnect productivo
y validacion en mercado abierto pendientes; no declarar migracion PASS.
Detalle: docs/A7_WEBSOCKET.md (desde docs: A7_WEBSOCKET.md).
A7 PARTIAL/BLOCKED: upgrade WebSocket rechazado por la infraestructura de red.

# Contexto del sistema

## A7 — continuación: preparación y diagnóstico externo, PARTIAL/BLOCKED

Se distingue rechazo previo al envío de UNKNOWN: preparación con intención
APPROVED, metadata durable y liberación de reservas solo con cero intentos de
mutación demostrados. Crash durante POST sigue UNKNOWN y nunca reenvía.
El usuario autorizó estímulo sintético A6 exclusivamente para el smoke Demo.
Identidad/scopes/elegibilidad/costes hipotéticos observados con credenciales
existentes PRESENT. La cotización externa falló: 81.588043s frente a máximo 3s.
Costes usa value frente a amount del esquema; contabilidad de cierre pendiente.
Cero órdenes/mutaciones. No se conectó aún el runner ni se habilitó Demo Write.
Detalles y partes pendientes: [continuación A7](A7_COMPLETION_ATTEMPT.md).
Las afirmaciones históricas de core intacto o UNKNOWN para todo rechazo quedan
actualizadas por este incremento; Strategy 1, riesgo, A6 y esquema se conservan.

## A7 — seguridad implementada, ejecución externa pendiente

Se implementa la clasificación autoritativa de acceso Demo y la verificación
fresca en adaptador/transporte. No se habilita todavía trading externo: faltan
datos operativos, elegibilidad efectiva y contabilidad/recovery de cierres.
REAL continúa fuera de capacidad; no hay configuración que lo habilite.
La solicitud A7 sustituye su prohibición histórica, sin dar por resueltos esos
gates. Estado PARTIAL/BLOCKED y evidencia en [A7](A7_DEMO_ONLY.md).

## A6 — sesión interna simulada

El nuevo runner conecta Strategy 1 congelada con contexto Demo, elegibilidad,
riesgo, intención durable, ejecución local y reconciliación/cierre. Identidad y
cotizaciones son contratos simulados explícitos: no nueva evidencia externa A5.
No carga .env ni consulta eToro. A7 y runner conectado continúan pendientes;
A5 real y datos A2–A4 se conservan. [A6](A6_SESSION.md).

## A5 — preflight Demo read-only, 2026-09-16

La autorización A5 permite identidad, portfolio Demo y metadata de instrumento,
solo mediante GET explícitos. El servicio separado reporta scopes observados,
credit virtual e identidad sanitizada; no ejecuta Strategy 1 ni habilita órdenes.
Prueba externa propia PASS: claves existentes en .env cargadas con uv --env-file
.env, tres GET/HTTP 200, identidad Demo/scopes/credit/AAPL verificados. A5 CLOSED.
El diagnóstico anterior solo comprobó el entorno exportado y queda superado. [A5](A5_PREFLIGHT.md).

## A4 — replay temporal autorizado y reproducción real PASS

replay_as_of_v1 separa procedencia historical_download de visibilidad lógica
observed; no cambia la estrategia congelada ni las capturas A2. Cada vista expone
solo barras disponibles al reloj. Dos runs reales coinciden exactamente, con cero
operaciones por RVOL_BELOW_THRESHOLD después de evaluar AAPL. Detalle y limitaciones
en [A4_READINESS](A4_READINESS.md), contrato en [REPLAY_AS_OF_V1](REPLAY_AS_OF_V1.md).
Las notas A4 pendiente/bloqueada inferiores son antecedentes de esta autorización.

## Strategy 1 v1 — decisiones definitivas A3

ORB_RVOL_v1.0 incorpora RS contra SPY y QQQ, ambos obligatorios y reference-only.
Régimen/VWAP confirmation desactivados; universo common_stock, sin ETF operables.
Configuración congelada configs/strategy-1-v1.yaml y snapshot A3 verificable.
V0.1 conserva compatibilidad. Histórico Massive no se transforma en observed.
Las decisiones actuales sustituyen los bloqueos históricos siguientes; A4 pendiente.

## A3 — alcance pendiente de definición

A3 está BLOCKED: v0.1 excluye ETF y no tiene filtros RS/régimen/VWAP activos.
No hay versión final congelada para A4; el snapshot A3 solo documenta lo existente.
Se requiere resolver la diferencia con la solicitud ampliada, sin reinterpretar
la validación de datos A2 como definición de reglas. [Auditoría](STRATEGY_1_A3_AUDIT.md).

## Alcance A2 actual

A2 valida suficiencia histórica real de AAPL/SPY/QQQ; no cambia la disponibilidad
operativa de esas barras. Capturas locales permiten reproducción sin credenciales;
solo descarga explícita requiere la clave Massive del entorno. RS/VWAP son
funciones de investigación y no hay filtro de régimen definido en v0.1.
[Evidencia y límites](MASSIVE_A2.md). Las notas siguientes describen el cierre A1.

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
