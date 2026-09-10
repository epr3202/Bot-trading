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

Demo: apertura/lookup/cancelación v2 documentadas; cierre v1 y protección v2 tienen
contratos separados. Los enums de cierre v1 y la recuperación por referencia tras
respuesta perdida no están suficientemente documentados; el adaptador conserva
incertidumbre. El runner Demo permanece bloqueado hasta resolver esa gestión de sesión.
La caducidad del permiso de entrada no caduca automáticamente el permiso de gestión,
pero ambos dependen de identidad Demo, credenciales y propiedad comprobadas.
