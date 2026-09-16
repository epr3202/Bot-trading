# A7 — continuación de cierre, PARTIAL/BLOCKED

## A7 — auditoria UTC/costes, PARTIAL/BLOCKED (2026-09-16)

La evidencia anterior era 81.588043 s, no 81588 s; ambiguedad de coma decimal.
Dos GET rates nuevos confirmaron retrasos de 35.860831 y 75.107782 s.
Recepcion HTTP registrada antes del parseo, UTC aware; limite 3 s intacto.
Costes value/amount normalizados dentro del adapter; fixture real sanitizado.
142 pruebas focales A7/A6 PASS. Gate externo QUOTE_STALE_OR_DELAYED;
cero ordenes/mutaciones; identidad DEMO y parser de costes PASS.
No se habilita el vertical de trading mientras falle frescura. No A8.
Detalle, cambios, comandos y evidencia: [auditoria A7](A7_QUOTE_COST_AUDIT.md).


2026-09-16. El usuario autorizó usar el estímulo sintético A6 para un smoke
exclusivamente Demo, con cotización, identidad, elegibilidad, costes y riesgo
externos verificados. Esta autorización resuelve la política del estímulo de
prueba; no convierte sus datos en observaciones de mercado ni modifica Strategy 1.

## Resultado externo concreto

Las dos credenciales existentes se cargaron con `uv --env-file .env`: PRESENT.
Sin modificar .env, crear claves, imprimir secretos ni usar credenciales MCP.
El primer diagnóstico falló con ETORO_READ_UNAVAILABLE en red restringida.
Los diagnósticos autorizados fuera de esa restricción conservaron TLS/CA.

Se verificaron externamente identidad DEMO y scope write Demo; AAPL resolvió a
instrumentId 1001, Stocks, exchangeId 4. Elegibilidad real: apertura/cierre
permitidos, subyacente long con leverage 1, stop permitido, mínimo 10 USD,
máximo 6151 unidades; unidades fraccionarias permitidas. No se utilizó esa
capacidad para inferir una precisión fraccionaria arbitraria ni enviar órdenes.

La consulta de costes hipotéticos para una unidad devolvió transactionFee 1 USD,
markup 0, marketSpread 0.06 y overnightFee 0. Es una estimación de apertura,
**no prueba de costes finales ni de una reserva completa de ida y vuelta**.
La respuesta usa `value`; el esquema consultado publica `amount`. Se conserva
la discrepancia y no se sustituye un valor ausente por cero.

La primera lectura de quote falló por timestamp sin zona. El esquema getRates
define UTC; se corrigió únicamente esa representación, sin cambiar su instante.
El último diagnóstico, 2026-09-16T14:39:21Z, recibió:

| Campo | Observado |
|---|---|
| quote_type | realtime |
| event_at | 2026-09-16T14:37:59.810000+00:00 |
| bid / ask | 333.8 / 333.83 |
| antigüedad al comprobar | 81.588043 segundos |
| máximo de riesgo | 3 segundos |
| resultado | BLOCKED / QUOTE_STALE_OR_DELAYED |
| mutaciones de trading | 0 |

La etiqueta realtime no sustituye el control de edad. No se usa received_at como
event_at ni se amplía el umbral para conseguir una orden. Evidencia local:
runtime/a7-completion/readiness-20260916T143921.json; intentos anteriores conservados.
El script diagnóstico termina normalmente con exit 0 al persistir su informe;
su resultado funcional es BLOCKED, no una aceptación de smoke.

Comando ejecutado:

```powershell
.\scripts\uv.ps1 run --frozen --env-file .env python runtime/a7-completion/probe.py
```

Este es un diagnóstico local de lectura, **no un runner de trading ni el smoke
de aceptación A7**. No se creó ninguna posición que requiera cierre. No existen
provider orderId/positionId/close orderId nuevos; no se inventan esos campos.

## Cambio de estados y persistencia

Se reutiliza el port ExecutionBroker. PreparingBroker es una extensión opcional
para brokers que validan antes de enviar; SimulatorBroker y el runner A6 no cambian.
EtoroDemoAdapter.prepare realiza las comprobaciones con la intención APPROVED
durable y reserva vigente. Devuelve una capacidad efímera de envío y metadata
saneada: instrumentId, unidades, dirección, referencia UUID, fecha y modo Demo.
Executor persiste esa metadata antes de pasar a SUBMITTING.

| Significado | Estado/evidencia existente |
|---|---|
| PREPARED | APPROVED durable; evento PREPARED y metadata `prepared:<intent_id>` |
| Rechazo demostrado anterior al envío | REJECTED + evento REJECTED_PRE_SEND; reserva liberada transaccionalmente |
| Intento inminente | SUBMITTING durable antes de invocar el envío preparado |
| Respuesta correlacionada | ACKNOWLEDGED con broker_order_id; todavía no FILLED |
| Resultado externo ambiguo | UNKNOWN; reserva conservada, entradas pausadas, sin reenvío |
| Ejecución confirmada | FILLED únicamente tras reconciliación existente |

El transporte incrementa mutation_attempts inmediatamente antes de despachar
una mutación. El adaptador clasifica como RejectedBeforeSend solo excepciones
anteriores a ese punto. Después del intento, timeout, HTTP 500 o respuesta
inválida siguen siendo ambiguos. Errores inesperados de preparación se sanean
a PRE_SEND_PREPARATION_FAILED; no se guarda su texto privado.

Crash durante preparación deja APPROVED, que recovery caduca como EXPIRED;
no hay UNKNOWN externo ni reenvío. Crash durante POST conserva UNKNOWN. Tras
respuesta perdida antes de guardarla, la referencia durable permite lookup y
recuperación del mismo orderId/positionId en pruebas de contrato.

**Límite inevitable:** SQLite y HTTP no forman una transacción atómica. Si el
proceso muere después de guardar SUBMITTING pero antes del primer byte, el nuevo
proceso no puede demostrar si hubo envío: conserva UNKNOWN y reconcilia. No se
afirma que ese intervalo desapareció. Los rechazos con proceso vivo y las
muertes durante preparación sí se distinguen inequívocamente.

La preparación opcional actual cubre entradas. Cierres conservan el port y sus
validaciones; un rechazo demostrado anterior a su POST también queda REJECTED.
No se añade reintento de un close rechazado ni se libera exposición de la posición.

## Red y seguridad

GuardedTransport admite explícitamente `demo_preview=True` solo para POST COSTS
y ELIGIBILITY, con identidad/portfolio Demo fresco antes de la consulta. No
habilita ninguna ruta mutante, aunque el caller use el argumento en ORDERS.
Los métodos mutantes siguen restringidos al MockTransport exacto. No cambia
el origen, rutas Demo, permisos, restricción A5 irreversible, TLS ni redirects.
No hay endpoint, modo o flag de trading REAL.

## Contratos y partes aún no implementadas

Se revalidaron catálogo eToro v1.379.0 y nueve especificaciones de identidad,
elegibilidad, costes, apertura v1/v2, lookup, cierre e historial; además rates
v1/v2. Las rutas consultadas no están marcadas deprecated. Se mantiene apertura
v2 existente; no se migra a v1 sin necesidad. Solo consultas de documentación
mediante MCP. Esquemas en runtime/a7-completion/official-contracts.json.

Close v1 confirma submission con HTTP 200, no cierre. Su consulta sigue
publicando statusID sin enum, referenceID nullable y campos de ejecución
opcionales. Lookup v2 expone estado/exposición, pero openingData no es un fill
de cierre. No se inventaron costes finales ni inferencias de caja/flat.

Pendientes concretos:

1. Resolver cotizaciones ejecutables con edad <=3s; el estímulo sintético no
   autoriza sustituirlas por precios fabricados ni timestamps de recepción.
2. Normalizar y verificar los costes observados y la reserva de ida/vuelta.
3. Implementar/validar full close y contabilidad/recovery externos sin inferir
   un fill a partir de HTTP 200 o de un enum no documentado.
4. Conectar el punto de broker del runner A6, habilitar el transporte mutante
   exclusivamente mediante ese flujo y entregar el smoke opt-in completo.
   Estas tres capacidades **no están implementadas** en esta continuación.
5. Ejecutar open → reconcile → close → reconcile con provider IDs persistidos.

La falta de cierre no se atribuye a credenciales ausentes. La autorización de
smoke persiste; no requiere que el usuario vuelva a darla. A7 sigue BLOCKED
por evidencia/contratos pendientes y el trabajo de integración indicado.

## Verificación y entrega

Baseline: 383 passed, 5 warnings, 27.64s. Regresión tras preparar antes de
SUBMITTING: 383 passed, 5 warnings, 25.32s. Nuevas pruebas focales: 20 passed,
3.15s, incluyendo rechazo/reservas, timeout/500/respuesta inválida, crash/restart,
quote UTC y protección de previews. Gates finales en [VERIFICATION](VERIFICATION.md).
Se preservan Strategy 1, riesgo, esquema SQLite, A6, configuración y lockfile.
No A8, nuevas estrategias, dashboard, publicación ni commits.

## Definition of Done de esta continuación

PASS de contratos no significa una operación externa. Aceptación global BLOCKED.

| # | Criterio | Resultado y evidencia |
|---|---|---|
| 1 | Runner genera mutación Demo externa | BLOCKED: no conectado; quote no elegible |
| 2 | Identidad Demo antes de mutar | PASS: guards; identidad externa verificada en diagnóstico |
| 3 | REAL, cero mutaciones | PASS: regresión A7 |
| 4 | UNKNOWN, cero mutaciones | PASS: regresión A7 |
| 5 | Error identidad, cero mutaciones | PASS: regresión A7 |
| 6 | Configuración no habilita REAL | PASS: origen/allowlist/modos cerrados |
| 7 | Elegibilidad previa | PASS: código/tests y observación real AAPL |
| 8 | Riesgo A6 activo | PASS: motor intacto y pruebas |
| 9 | Apertura externa autoritativa | BLOCKED: no enviada |
| 10 | Open orderId externo persistido | BLOCKED: solo prueba de contrato |
| 11 | PositionId externo persistido | BLOCKED: solo prueba de contrato |
| 12 | Recovery de apertura | PASS: test_restart_uses_durable_reference_without_duplicate_post; contrato mock |
| 13 | Cierre externo usa positionId persistido | BLOCKED: no smoke externo |
| 14 | Close HTTP 200 no implica CLOSED | PASS: pruebas existentes preservadas |
| 15 | Close reconciliado | BLOCKED: contrato contable y ejecución pendientes |
| 16 | Estado final local coincide con Demo | BLOCKED: no roundtrip externo |
| 17 | Rechazo pre-send distinto de ambiguo | PASS: 20 tests nuevos; límite crash SQLite/HTTP explícito |
| 18 | UNKNOWN no reenvía ciegamente | PASS: pruebas timeout/crash/duplicados |
| 19 | Suite A6 | PASS: 39 |
| 20 | Suite A7 | PASS: 84 |
| 21 | Suite completa | PASS: 842, 16/16 gates |
| 22 | Evidencia externa de ejecución saneada | BLOCKED: solo diagnóstico de lectura saneado |
| 23 | Documentación actualizada | PASS |
| 24 | REAL fuera de capacidad | PASS: ninguna ruta mutante de red habilitada |
