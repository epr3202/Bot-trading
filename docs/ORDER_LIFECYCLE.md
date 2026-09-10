# Órdenes y recuperación

Fuente: `execution/models.py`, `execution/engine.py`, `persistence/store.py`.
La estrategia produce Signal; RiskEngine decide; Executor persiste OrderIntent y
reservas antes de SUBMITTING y de tocar BrokerAdapter. UUIDv5 estable separa intención
de entrada, cierre y referencias de gestión. Un índice SQLite impide segunda entrada
de estrategia/versión/sesión/símbolo. No existe garantía exactly-once del bróker.

Estados: CREATED → APPROVED → SUBMITTING → ACKNOWLEDGED → PARTIALLY_FILLED → FILLED.
REJECTED, EXPIRED y CANCELLED son terminales, salvo evidencia tardía de fill tras
cancelación/caducidad. CANCEL_PENDING no libera exposición. UNKNOWN bloquea duplicados
y conserva reservas hasta evidencia. La tabla TRANSITIONS es la autoridad de cambios.
Un HTTP 200 o 202 nunca equivale por sí solo a una posición ejecutada.

SQLite esquema 1 usa WAL, synchronous=FULL y BEGIN IMMEDIATE. Intención, fill acumulado,
reserva, posición y PnL se actualizan transaccionalmente. Cantidad/precio acumulados
permiten calcular el incremento sin contabilizar dos veces eventos repetidos. Un cambio
de ID, regresión de cantidades/costes, sobrellenado o posición ajena aborta la transacción.
Bloqueo OS sin expiración excluye dos ejecutores; muerte del proceso lo libera.

Reinicio: entradas desarmadas, SUBMITTING se vuelve UNKNOWN y las intenciones aprobadas
sin envío caducan. Consulta órdenes conocidas, incluidos terminales susceptibles a fills
tardíos. No vuelve a enviar una apertura ambigua. PnL/diario e IDs sobreviven al reinicio.
Una posición solo se administra si su intención de origen y fill demuestran propiedad.
No se deduce propiedad por ticker, dirección, etiqueta humana o parecido de cantidades.

PAUSE_ENTRIES, CANCEL_PENDING_ENTRIES, FLATTEN_OWNED y parada son operaciones distintas.
Cerrar cancela primero entradas parciales propias, verifica cantidad y crea una sola
intención de salida por posición. UNKNOWN de cierre exige reconciliar, nunca otra venta
para forzar el resultado. Si no queda exposición ni estados activos puede informarse flat.

Fase 2: apertura/lookup/cancelación v2, cierre v1 y protección v2 conservan contratos
separados. Todo envío conectado está deshabilitado en GuardedTransport, incluso con
un permiso anterior. Los escenarios de gestión solo despachan a httpx.MockTransport
exacto, sin pasar por un cliente de red. Pausar no elimina la exposición existente.

`EtoroDemoAdapter._query_close` correlaciona CID Demo, ID de orden persistido, posición,
intención de apertura, orden de apertura e instrumento. Valida referenceID si aparece;
su ausencia no se sustituye por el identificador de trazas. Un cierre sin orderId
recuperable sigue UNKNOWN; no consulta un ticker parecido ni reenvía. El historial v1
se revisó, pero no garantiza que orderId sea el cierre ni define atribución de fees
o identidad estable de ejecuciones parciales: no se incorporó como solución ficticia.

Fase 3 corrige la inferencia anterior: una fila v1 documenta unidades cerradas y
occurred, pero no garantiza acumulación ni exposición restante. No se calcula
remainingUnits restando esa fila a la cantidad solicitada, que podría ser solo
una parte de la posición. La observación de exposición procede del campo explícito
remainingUnits de lookup v2. Varias filas v1 carecen de garantía acumulativa y se
bloquean. statusID sigue sin enum público; TODOS sus números conservan
UNKNOWN. rate/proceeds no certifican comisiones ni contabilidad final. El lookup v2
de apertura aporta state=open/closed, remainingUnits y lastUpdate; openingData.units
sigue siendo entrada, jamás se contabiliza como cierre.

Lookup v2 contempla action=open/close; el normalizador de entradas exige open y
status.id entero. Estados 3/5/9/10 sin cantidad ejecutada verificable se bloquean;
9/10 mantienen fills y el remanente terminal. Cierres v2 sin contrato contable final
no se convierten artificialmente en entradas. Ver matriz de Fase 3 en ETORO_API_AUDIT.

Position conserva `units` contables, `observed_units`, `observed_at` y
`accounting_complete`. Cero observado con libro pendiente conserva capital/riesgo y
bloquea nuevas entradas y otra salida. No inventa precio, ingreso ni comisión. Los
campos nuevos tienen defaults para leer los JSON del esquema SQLite 1 existente.
Snapshots antiguos, contradictorios o incrementos inesperados de exposición abortan
la transacción. La ausencia en un portafolio/404 no aporta ninguna observación.

Fills acumulados confirmados por el contrato local actualizan unidades, precio medio,
PnL y comisiones en una transacción, incluyendo costes tardíos sin nuevo fill. La
revisión de precio acumulado sin cambio de cantidad queda bloqueada para revisión
contable; no se descarta silenciosamente. Stop y cierre horario/manual comparten la
misma intención persistida por posición. La reconciliación fallida impide FLAT_CONFIRMED
incluso si el libro local ya muestra cero. El runner externo continúa BLOCKED.
