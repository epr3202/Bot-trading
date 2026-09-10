# Auditoría eToro

Verificación documental: 2026-09-10 15:01:45 UTC. Catálogo MCP oficial API **v1.375.0**,
skill de catálogo **1.19.1**. Fuentes y esquemas completos en
`etoro_spec_snapshot.json` y `etoro_close_spec_snapshot.json`, obtenidos mediante
get-tags → get-all-routes → get-route-spec. Solo llamadas de catálogo/especificación;
cero llamadas de identidad/cuenta, cero cotizaciones conectadas y cero escrituras.

Puntos oficiales consultados: [portal](https://api-portal.etoro.com/),
[índice](https://api-portal.etoro.com/llms.txt),
[autenticación](https://api-portal.etoro.com/core/getting-started/authentication),
[builders](https://builders.etoro.com/). La versión mayor de una ruta no demuestra
compatibilidad de payloads: se eligen contratos concretos y se prueban separados.

| Operación | Método y ruta permitidos | Tratamiento |
|---|---|---|
| Identidad mínima | GET `/api/v1/me` | Conserva demoCid, scopes y huella local; descarta perfil personal |
| Portafolio virtual | GET `/api/v1/trading/info/demo/portfolio` | clientPortfolio; verifica listas y CID si aparece |
| Instrumentos | GET `/api/v2/market-data/instruments` | symbols/type/pageSize/pageToken; resolver identidad, no inventar ID |
| Bid/ask | GET `/api/v2/market-data/rates` | instrumentIds, date, quoteType; parcial/delayed se valida |
| Velas | GET `/api/v1/market-data/instruments/{id}/history/candles/asc/OneMinute/{count}` | máximo 1000, volumen/finalidad no certificados |
| Costes | POST `/api/v2/trading/info/demo/costs` | lectura semántica, no orden |
| Elegibilidad | POST `/api/v2/trading/info/demo/eligibility` | lectura, producto/stop/mínimos según respuesta |
| Crear entrada | POST `/api/v2/trading/execution/demo/orders` | cuenta Demo, referencia UUID persistida; ACK no fill |
| Consultar | GET `/api/v2/trading/info/demo/orders:lookup` | orderId/referenceId; accountId comprobado |
| Cancelar | DELETE `/api/v2/trading/execution/demo/orders/{id}` | CANCEL_PENDING hasta evidencia |
| Protección | PATCH `/api/v2/trading/demo/positions/{id}` | stopLossRate/stopLossType=fixed, verificar después |
| Cerrar posición | POST `/api/v1/trading/execution/demo/market-close-orders/positions/{id}` | InstrumentID/UnitsToDeduct; propietario demostrado |
| Consultar cierre | GET `/api/v1/trading/info/demo/close-orders/{id}` | no inferir enums ni cantidad cerrada de openingData |

Autenticación elegida: x-api-key + x-user-key y x-request-id; no mezcla con Authorization
Bearer. El contrato también describe OAuth, pero no se implementa refresco ni se heredan
credenciales del MCP. Preflight solo consulta me y ruta Demo, rechaza scopes reales o
ambiguos y exige permiso Demo explícito. Si las claves no revelan scopes verificables,
queda BLOCKED; no solicitar privilegios reales como solución. La lectura del campo
credit no equivale por sí sola a equity/cash utilizables para sizing: falta orquestación
verificada de reservas, pendientes y posiciones. Preflight no habilita entradas.

Entrada v2 usa action=open, transaction=buy, instrumentId, leverage=1, settlementType
`real`, units, orderCurrency=usd y stopLossRate/stopLossType según el esquema.
**En ese campo del contrato, `real` identifica el subyacente
frente a CFD; no es un modo de dinero real.** Solo aparece dentro del payload enviado
a una ruta Demo. Las configuraciones de modo real siguen rechazadas. Elegibilidad debe
confirmar subyacente efectivo, límites, minPositionAmount y porcentajes de stop. La
precisión de unidades y todas las condiciones jurisdiccionales aún necesitan evidencia
de cuenta/instrumento. Defaults sintéticos nunca son evidencia suficiente para Demo.

Las cuotas se limitan por grupos en QuotaBudget: default/market/portfolio/lookup y
execution/costs/eligibility; se aplica también un presupuesto global conservador y se
reserva capacidad para prioridad de gestión. Las especificaciones contienen límites por
ruta (habitualmente 60/60s para lecturas, 20/60s para operaciones dedicadas); no asumir
que pools diferentes concedan cuota independiente. Lecturas: hasta tres intentos con
backoff/jitter y Retry-After numérico/HTTP-date. Escrituras: un único intento; errores
ambiguos producen SubmissionUnknown, jamás nuevo ID para forzar reenvío.

Idempotencia: el esquema documenta referencias y lookup; no se certifica una duración
de garantía end-to-end. Un 404 de lookup no prueba rechazo tras timeout. Cierre v1 no
ofrece aquí semántica de estado/referencia suficiente para reconstrucción garantizada;
su query conserva incertidumbre. Esta discrepancia bloquea el runner Demo de sesiones.

Estados v2 mapeados explícitamente por status.id en etoro_demo.py; desconocidos →
UNKNOWN. Cumulative positionExecutions se valida; múltiples posiciones para una orden
exigen reconciliación especializada y se bloquean. PATCH ACK no demuestra stop instalado.
No se afirma atomicidad de stop/apertura ni ejecución garantizada de cierre programado.

Estado de capacidades: contratos documentados y pruebas mock locales; **NOT_CONFIGURED**
para cuenta, **sin DEMO_READ_VERIFIED ni DEMO_WRITE_VERIFIED**. Datos candles insuficientes
para veinte sesiones RVOL: sin cursor/fecha histórica y volumen consolidado no demostrado.
La primera activación exige claves propias, presupuesto aceptado, datos compatibles,
elegibilidad/stop, reconciliación y permiso local temporal ligados a cuenta/sesión/config.
