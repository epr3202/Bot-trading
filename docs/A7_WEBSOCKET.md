# A7 — WebSocket: spike bloqueado antes de autenticacion

2026-09-16. **Migracion NOT_INTEGRATED; A7 PARTIAL/BLOCKED.**

## Revision contractual

BOOTSTRAP_SPEC seccion 3 exige eToro como fuente de precios ejecutables y
event_time separado de received_at. RISK_POLICY exige cotizacion <=3 s,
spread <=0,3%, desviacion y divergencia <=0,5%; no prescribe REST.
ADR 002 separa datos y broker; ADR 001/005/006 conservan Demo-only,
lifecycle y autorizacion temporal. Ninguno exige que quote_at provenga de
GET rates. `git log --all -G 'quote_at|REST|ejecutables'` sobre esos contratos
remite al baseline 6af05f1; las menciones REST de ETORO_API_AUDIT describen
el adaptador existente, no una invariancia de riesgo.

Decision autorizada, pendiente de viabilidad e integracion:
“eToro continúa siendo la fuente de precio operativo; se cambia el transporte
de REST polling a WebSocket streaming para satisfacer el contrato de frescura
sin modificar RiskEngine.” No se afirma que la sustitucion ya este realizada.
Massive conserva su responsabilidad historica. No se regeneran hashes A3.

## Contrato oficial revisado

- [Autenticacion](https://api-portal.etoro.com/core/websocket/authentication):
  Authenticate con id UUID y data.apiKey/userKey; ACK correlacionado y success=true.
- [Topicos](https://api-portal.etoro.com/core/websocket/topics): Subscribe con
  topics y snapshot; envelope messages, topic instrument:1001, type
  Trading.Instrument.Rate, content JSON string con Bid/Ask/Date/PriceRateID.
- [Rates](https://api-portal.etoro.com/core/websocket/notifications/websockets/instrument-rates):
  Date es timestamp del precio; PriceRateID es identificador, no secuencia
  monotona documentada. El timestamp original se conserva, no se sustituye
  por recepcion ni se inventa quoteType del wire.
- [Control](https://api-portal.etoro.com/core/websocket/notifications/websockets/control-channel-request-response):
  Authenticate/Subscribe/Unsubscribe; no mutaciones de trading en este cliente.

AAPL/1001 procede de la resolucion A5/A7 ya observada. SPY/QQQ siguen siendo
referencias de barras para RS; el smoke autorizado solo necesita AAPL como
instrumento de ejecucion. No se inventaron otros IDs ni suscripciones privadas.

## Implementacion limitada a fase 1

`scripts/probe_etoro_websocket.py` es un diagnostico aislado. Conexion a host/path
fijos, TLS/CA y proxy existentes, redirect_limit=0 y HTTP 101 obligatorio antes
de enviar Authenticate. No loguea payload de autenticacion, headers libres ni
excepciones con secretos. Solo exporta datos de mercado permitidos y diagnostico
sanitizado. No importa runner, adapter ni RiskEngine; no puede enviar ordenes.

Estados del spike: DISCONNECTED -> CONNECTING -> AUTHENTICATING -> SUBSCRIBING;
READY requiere ACK de suscripcion y evento fresco. Error/timeout implica
DEGRADED y cierre final DISCONNECTED. No proporciona ninguna autorizacion al
dominio. Parser rechaza JSON ambiguo, precios invalidos y timestamps sin zona;
conserva Date crudo, event_time UTC, received_at y check_time. Registra edad,
spread, duplicados temporales y eventos fuera de orden. PriceRateID no se
interpreta como contador. La precision submicrosegundo cruda se conserva como
texto; el calculo datetime es microsegundo, aun no validado con mensajes reales.

El spike NO implementa reconnect automatico ni cache concurrente de produccion.
Tampoco inyecta quotes al provider/adapter/runner. Estas fases y sus tests de
aceptacion quedan pendientes del gate externo; no hay fallback a REST en el
spike. El adaptador REST previo permanece intacto y bloqueado para trading externo.

Se usa websocket-client==1.8.0 solamente mediante uv --with, en entorno aislado;
pyproject/uv.lock siguen intactos, incluido el hash congelado por A3. La eventual
dependencia productiva necesita resolver esta compatibilidad explicitamente;
no se actualiza ni regenera el snapshot para ocultar un cambio.

## Evidencia externa

Cuatro conexiones diagnosticas independientes devolvieron HTTP 403 durante
el handshake, entre 20:00:31Z y 20:01:55Z. No son reconnects automaticos.
ETORO_API_KEY: PRESENT. ETORO_USER_KEY: PRESENT.
El ultimo cuerpo saneado identifica **Proxy WebGateway | EPM**; contiene
referencias a proxy/policy/blocked/upgrade. No se obtuvo HTTP 101. El rechazo
antecede a Authenticate: no demuestra invalidez de credenciales ni rechazo
de permisos por eToro. La regla administrativa exacta no esta identificada.
No se cambio proxy, CA, host, ruta ni politica para sortear el bloqueo.

Evidencia local ignorada, conservada sin reemplazos:
`runtime/a7-websocket/{first-observation,handshake-diagnosis,network-classification,handshake-message}/summary.json`.

| Medida | Resultado |
|---|---|
| Autenticacion / suscripcion observadas | No / no |
| Eventos reales / frescos | 0 / 0 |
| Edad minima/maxima, spread operativo | No medibles |
| Reconnect automatico | 0, no implementado en el spike |
| Duplicados / fuera de orden | Sin muestras; no se valida su ausencia |
| POST/PUT/PATCH/DELETE, ordenes | 0 |
| Vertical slice / apertura / cierre | No iniciados |

La ventana planeada era 120 s; termino anticipadamente en el handshake.
Las conexiones ocurrieron despues de las 16:00 America/New_York: tampoco
constituyen una observacion de viabilidad durante mercado regular abierto.
No hay fixture de mensaje real porque no se recibio ninguno. Los tests usan
ejemplos fabricados explicitamente, nunca evidencia de conectividad.

Comando del ultimo intento, desde la raiz:

```powershell
.\scripts\uv.ps1 run --frozen --env-file .env --with websocket-client==1.8.0 python scripts/probe_etoro_websocket.py --output runtime/a7-websocket/handshake-message
```

Exit Python 2; launcher PowerShell 1. Elegir otra carpeta para repetir, sin
sobrescribir la evidencia. Primero se necesita que la politica de red permita
el upgrade WebSocket hacia ws.etoro.com:443/ws; despues repetir en mercado
abierto y comprobar autenticacion, suscripcion y frescura sostenida.

## Pendiente y criterios

No se cumplen los DoD de migracion ni A7: faltan mensajes reales, fixture,
adaptacion al port, cache atomica, reconnect con reauth/resubscribe/nueva quote,
prueba de quote WS llegando a RiskEngine, readiness completo y ciclo Demo
reconciliado. No se habilita una ruta mutante por aprobar tests del parser.
Strategy 1, RiskEngine, limites, A6, src completo, configs, snapshot y lock
se comparan contra baseline de este incremento. Resultados exactos de gates
en VERIFICATION y runtime/a7-websocket/verification.json al finalizar.
