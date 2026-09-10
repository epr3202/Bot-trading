# Auditoría eToro

## Fase 3 — revisión focalizada, 2026-09-10

Catálogo oficial revalidado: API **v1.375.0**, catálogo **1.19.1**. Se consultaron
get-tags, las 23 rutas Trading - Demo y los esquemas completos de lookup v2,
close-orders v1, historial Demo v1 y envío v3. Solo documentación del conector;
no se ejecutaron lecturas de cuenta mediante él. Captura íntegra de esta consulta:
runtime/phase3/official-contracts.json. Las secciones de fases anteriores quedan como historia;
esta matriz sustituye sus afirmaciones generales sobre ausencia de contrato.

Fuentes: [lookup v2](https://api-portal.etoro.com/api-reference/trading--demo/get-order-information-and-position-details),
[cierre v1](https://api-portal.etoro.com/api-reference/trading--demo/get-close-order-information-and-closed-position-details),
[historial Demo v1](https://api-portal.etoro.com/api-reference/trading--demo/list-trading-history),
[envío v3](https://api-portal.etoro.com/api-reference/trading--demo/submit-an-order-for-asynchronous-processing).
Las referencias a propiedades que siguen proceden de los esquemas anidados OpenAPI
devueltos por get-route-spec, además de las páginas públicas.

| Requisito | Fuente / campo exacto | Garantía y estado | Prueba local | Evidencia externa observada |
|---|---|---|---|---|
| Cuenta, intención, orden y posición | Lookup: accountId, orderId, positionExecutions[].positionId; v1: CID, orderID, instrumentID, referenceID nullable | DOCUMENTED / CONTRACT_TESTED: correlación con registros propios; ticker o mirrorID=0 no demuestran propiedad | test_close_identity_and_inconsistent_detail_blocked; test_stop_and_scheduled_exit_share_one_intent_and_reject_foreign_owner | NOT_OBSERVED |
| Recuperación tras respuesta perdida | Lookup query: exactamente uno de orderId/referenceId; referencia al x-request-id de envío | DOCUMENTED para lookup; v3 confirma referencia recuperable. BLOCKED: retención y puente concreto del cierre v1 con referenceID ausente | test_lookup_invalid_identifier_combination_never_reaches_transport; test_close_without_order_id_has_no_undocumented_reference_fallback | NOT_OBSERVED; ningún reenvío |
| Estado de orden frente a posición | Lookup GetOrderInfoStatus.id; GetOrderInfoResponse.action=open/close; positionExecutions[].state=open/closed | DOCUMENTED / CONTRACT_TESTED para estados v2 y separación de acciones. v1 statusID es un identificador interno sin enum publicado: BLOCKED su normalización | test_documented_lookup_statuses; test_lookup_close_or_malformed_status_cannot_be_booked_as_entry; test_position_state_contradiction_not_used_as_exposure | NOT_OBSERVED |
| Cantidad ejecutada y restante | openingData.units describe entrada; remainingUnits describe posición. V1 positions[].units describe cierre | DOCUMENTED campos; BLOCKED semántica acumulativa/incremental de cierres. Ya no se calcula restante como cantidad solicitada menos una fila v1 | test_partial_close_does_not_infer_flat_from_requested_units; test_v1_closed_units_are_not_remaining_exposure_or_final_accounting | NOT_OBSERVED |
| Precio y momento de salida | V1 positions[].rate/occurred nullable; historial closeRate/closeTimestamp | DOCUMENTED cuando presentes; BLOCKED finalidad, revisiones y asociación de cada ejecución al libro | test_empty_or_incomplete_close_detail_never_means_flat; test_close_identity_and_inconsistent_detail_blocked | NOT_OBSERVED |
| Identidad estable de fills y revisiones | Lookup openingData.priceId es snapshot de precio; historial positionId/orderId; v1 positionID | BLOCKED identidad estable de cada fill de cierre y protocolo de correcciones. No deduplicar por ticker/precio ni por un ID de precio | test_partial_remaining_duplicate_out_of_order_and_final_cost; test_duplicate_quantity_with_changed_price_requires_accounting_review (contrato local simulado) | NOT_OBSERVED |
| Costes, impuestos, conversión, moneda | Lookup openingData.fees/taxes/avgConversionRate son de apertura; totalCosts es de orden. V1 conversionRate, assetCurrencyID/accountCurrencyID/proceeds; historial fees/netProfit | DOCUMENTED campos; BLOCKED atribución de costes finales por cierre/moneda e inclusión de fees en netProfit. No inventar comisión cero ni restarla dos veces | test_v1_closed_units_are_not_remaining_exposure_or_final_accounting; test_closed_exposure_without_accounting_survives_restart_and_keeps_cash | NOT_OBSERVED |
| PnL realizado y efectivo utilizable | Historial netProfit; v1 proceeds; portfolio clientPortfolio.credit | BLOCKED reconciliación monetaria completa con reservas, parciales, costes y moneda. Lectura credit por sí sola no habilita sizing | test_closed_exposure_without_accounting_survives_restart_and_keeps_cash; test_flat_requires_successful_reconciliation_even_after_book_closed | NOT_OBSERVED |
| Historia, paginación, completitud, antigüedad | Historial minDate requerido, page/pageSize; array de trades; lookback menor a un año | DOCUMENTED parámetros; BLOCKED snapshot consistente, orden estable, revisiones y terminación inequívoca. La sugerencia de ventanas no aporta maxDate/cursor ni acceso demostrado a años anteriores | No implementación de ingestión contable de historial: NOT_TESTED, deliberadamente bloqueada | NOT_OBSERVED |

Enumeración v2 revalidada: 1 Received, 2 Placed, 3 Filled, 4 Rejected,
5 PartiallyFilled, 6 PendingCancel, 7 Canceled, 8 Expired,
9 CanceledPartiallyFilled, 10 RejectedPartiallyFilled, 11 WaitingForMarket,
12 PendingTriggeredRate. **9 y 10 conservan fills**: CANCELLED local representa
el remanente terminal, no ausencia de ejecución. Ahora 3/5/9/10 sin cantidades
ejecutadas verificables bloquean la respuesta. Todos los números v1 siguen UNKNOWN.

El esquema lookup contempla action=close y posiciones cerradas. Eso aclara consulta
de estado y exposición; no contiene closingData. La aplicación no debe afirmar que
lookup carece de cierres, ni reutilizar openingData como salida. La normalización
contable de close v2 y el enlace garantizado desde envíos legacy siguen pendientes.
La exposición explícita remainingUnits del lookup de apertura sigue disponible y
se mantiene separada de units contables, efectivo y accounting_complete.

Discrepancias y alcance de idempotencia:

- V3 documenta x-request-id para idempotencia y referenceId igual a ese valor, incluso
  cuando se pierde la respuesta. No se niega esa garantía; su duración/deduplicación
  de payload y su aplicabilidad al cierre v1 no están acreditadas. El bot conserva
  su envío v2 bloqueado, sin migrar a v3, cuyo contrato actual solo admite apertura.
- La descripción v3 menciona razones de rechazo para el estado 10; su nombre en
  lookup explicita ejecución parcial. No interpretar esa frase como cero fills.
- La [guía de órdenes](https://api-portal.etoro.com/core/guides/market-orders) usa
  ejemplos sin segmento Demo, campos y rutas de versiones diferentes. No se copian
  al adaptador: prevalece el esquema de la ruta Demo concreta. Ningún ejemplo autoriza
  consultar cuenta real o ejecutar mutaciones.
- Un 404 de historial puede ser validación upstream fallida; no prueba historial
  vacío. Un 404 de lookup tras timeout tampoco confirma rechazo.

Borrador de preguntas para soporte eToro — **NO ENVIADO**:

1. ¿Qué envíos Demo v1/v2/v3 aparecen en lookup v2 por orderId y referenceId? Para
   market-close-orders v1, ¿referenceID equivale siempre al x-request-id enviado,
   cuánto se conserva y cómo recuperar una respuesta perdida sin orderID?
2. ¿Cuál es el enum versionado de close-orders v1 statusID y su transición a
   estados terminales parciales? ¿Existe equivalencia oficial con status.id v2?
3. ¿Cada fila positions de cierre es incremental o acumulativa? ¿Qué fill ID,
   secuencia y regla de revisión permiten procesarla exactamente una vez?
4. ¿Cómo obtener cantidad, precio, tiempo, moneda, conversión, fees y taxes finales
   de cada cierre? ¿Historial orderId identifica apertura o cierre y netProfit
   incluye qué costes? ¿Cuándo pueden corregirse esos valores?
5. ¿Cómo obtener historia completa estable con page/pageSize, manejar registros
   tardíos y consultar periodos de más de un año sin maxDate/cursor publicado?

Preflight desde el bot, con el entorno real del proceso: 2026-09-10T19:24:54Z,
salida 2, CREDENTIALS_MISSING_OR_INVALID / NOT_CONFIGURED. Ambas variables ausentes;
no .env local. Transporte NOT_CHECKED, autenticación/identidad NOT_VERIFIED,
datos NOT_CHECKED, reconciliación externa NOT_OBSERVED. No llamada de cuenta ni
escritura. El único preflight de configuración real se conserva en
runtime/phase3/preflight.json; las suites ejecutan además su caso negativo aislado
con claves retiradas. Un éxito futuro de lectura tampoco arma la aplicación.

## Revisión de fase 2 — 2026-09-10

Catálogo vigente consultado de nuevo: API v1.375.0, catálogo 1.19.1, sin migración.
Se volvieron a revisar cierre v1, lookup v2, historial Demo v1, envío asíncrono v3
y candles. La evidencia contractual adicional está en phase2_review dentro de
etoro_close_spec_snapshot.json. **Ninguna cuenta externa ni escritura se consultó**:
faltan ETORO_API_KEY/ETORO_USER_KEY en el proceso y no existe .env en el proyecto.

La consulta v1 documenta positions[].units como cantidad cerrada y occurred como
momento del cierre. Se utiliza solo para exposición observada y trazable; statusID
es un entero interno sin enum, fees/taxes y finalidad no están definidos allí.
No se declara FILLED ni se ingresa efectivo a partir de rate/proceeds. Referencia:
[consulta de cierre](https://api-portal.etoro.com/api-reference/trading--demo/get-close-order-information-and-closed-position-details).

El lookup de la apertura conserva accountId/orderId/positionId y permite leer
remainingUnits, state y lastUpdate por posición. Cero observado no completa la
contabilidad de salida. El historial Demo devuelve units/fees/netProfit/orderId,
pero no define aquí identidad estable de cada fill ni atribución inequívoca del
orderId al cierre. No se añadió su ruta al transporte ni se inventó una reconciliación
con esos campos. Ver [historial](https://api-portal.etoro.com/api-reference/trading--demo/list-trading-history).

El endpoint v3 actual admite solo aperturas; action=close y positionIds están
reservados para soporte futuro. Un 202 solo confirma aceptación. No resuelve el
cierre v1 y no justifica cambiar el adaptador:
[contrato v3](https://api-portal.etoro.com/api-reference/trading--demo/submit-an-order-for-asynchronous-processing).

En esta fase todos los métodos de mutación y los POST semánticamente de lectura
están limitados al transporte mock. Los POST de costes/elegibilidad son lecturas
documentadas, pero no se autorizaron contra la cuenta en este encargo. La red real
solo admite GET de la allowlist existente, sin redirects ni proxies heredados.
La CLI permanece desarmada. Un preflight aprobado solo certifica lectura mínima;
conectividad, autenticación, identidad Demo, datos y escritura se reportan separados.

La revisión inicial que sigue queda como antecedente contractual del bootstrap;
su posible activación temporal está subordinada al bloqueo absoluto de esta fase.

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
