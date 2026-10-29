# A7 — WebSocket: spike bloqueado antes de autenticacion

## Reobservacion 2026-09-21

### Revision de funciones y certificado (15:46-15:47 UTC)

Se compararon nuevamente los valores efectivos cargados por uv --env-file con
el usuario literal de get_proxies y el orden de busqueda/normalizacion de clave
de growatt.py: usuario, contrasena, host y puerto coinciden (solo booleanos
registrados). websocket-client 1.8.0 recibe la tupla sin cambios y genera
Proxy-Authorization Basic para CONNECT, no para el destino eToro.

El certificado existe en `certs/epm-root.cer` dentro del proyecto, PEM, 1580 bytes,
CA Empresas Publicas de Medellin, vigencia 2024-04-16 a 2044-04-11.
SHA-256: 5fa9781a648a17dc435ffa15721b2b35e0192efcbe35e555d4721b36949ac684.
La configuracion Growatt referencia E:\certs\epm-root.cer, ausente en esta maquina;
no se afirma identidad binaria con ese archivo inaccesible. La CA local si
valida el certificado presentado por el gateway en la conexion observada.

Diferencias corregidas en tls_context del spike: ruta anclada al proyecto,
independiente del cwd; confianza combinada sistema + certifi (el bundle publico
usado por Requests) + EPM; acepta PEM/DER y falla explicitamente si falta la CA.
Antes solo se cargaba la CA corporativa y habia fallback implicito si faltaba.
No se modifico el certificado, .env, sistema global, src ni lock; certifi ya
pertenece al lock existente. Se mantienen CERT_REQUIRED y check_hostname.

Dos observaciones read-only con instrumentacion passthrough de la biblioteca:
CONNECT aprobado (la biblioteca exige HTTP 200), TLSv1.3 verificado, issuer EPM,
161 autoridades de confianza cargadas. El rechazo HTTP 403 ocurre despues,
durante el upgrade WebSocket. La pagina declara literalmente:
**WebSocket Block — Upgrade to WebSocket is blocked.** Generada por McAfee Web
Gateway EPM. Esto identifica la causa observada; no afirma que el proxy haya
validado la identidad del usuario, aunque acepto el tunel con sus credenciales.

Evidencia local sanitizada, ambas con 0 eventos y 0 mutaciones:
`runtime/a7-websocket/tls-review-20260921/{summary,network-stages}.json` y
`runtime/a7-websocket/tls-policy-20260921/{summary,network-stages}.json`.
No se simularon respuestas: los wrappers observaron retornos reales de CONNECT,
TLS y la excepcion de upgrade. No se activo trace ni guardaron headers secretos.
Siguiente paso externo: permitir WebSocket upgrade para ws.etoro.com:443/ws en
la politica del gateway; despues repetir el probe. No sortear la politica.
34 pruebas focales PASS; detalle y limites de validacion en VERIFICATION.md.

### Proxy autenticado explicito (15:33 UTC)

Por solicitud del usuario se reviso `growatt.py` del directorio de red indicado.
Usa proxy HTTP EPM con usuario/contrasena; no usa NTLM en ese mecanismo.
Se trasladaron exclusivamente esos valores al .env local ignorado por Git,
sin mostrarlos ni modificar el origen. Variables: ETORO_PROXY_HOST,
ETORO_PROXY_PORT, ETORO_PROXY_USER y ETORO_PROXY_PASSWORD; ejemplo sin valores
en .env.example. Cargar deliberadamente con `uv --env-file .env`.

El spike usa http_proxy_host/port y http_proxy_auth=(usuario, contrasena),
con host/puerto permitidos proxy.epm.com.co:8080. No introduce credenciales
en la URL eToro ni headers WebSocket. Configuracion parcial falla antes de
conectar; NO_PROXY heredado no evita el proxy explicito. Sin valores dedicados,
se conserva el comportamiento previo de configuracion heredada del entorno.
TLS/CA, origen eToro, prohibicion de redirects y ausencia de trading intactos.
Redaccion cubre usuario, contrasena, representacion URL y Basic base64;
verify.py retira estas variables de los procesos de checks.

Referencia del mecanismo de la biblioteca:
[proxy autenticado](https://websocket-client.readthedocs.io/en/latest/examples.html#connecting-through-a-proxy).
No se cambiaron dependencias ni hashes A3. El mecanismo solo aplica al spike;
no se ha integrado al transporte REST o al runner.

Prueba externa con configuracion explicita: HTTP 403, pagina Proxy WebGateway
EPM, antes de Authenticate; 0 eventos y 0 mutaciones. No acredita autenticacion
aceptada del proxy ni validez de las claves eToro. Sigue pendiente identificar
la regla de red. Evidencia: runtime/a7-websocket/proxy-auth-20260921/summary.json.
Comando: el mismo probe con --offline --frozen --env-file .env y
--output runtime/a7-websocket/proxy-auth-20260921. Python exit 2 / launcher 1.

### Observacion previa al ajuste de proxy (15:14 UTC)

Contrato y ADR revisados nuevamente, incluido historial Git: se exige eToro,
no REST rates como origen obligatorio de quote_at. Documentacion oficial de
Authenticate y Topics consultada nuevamente; no se implementa un schema supuesto.
El spike existente se conserva sin cambios y no se integra al runner.

El intento con resolucion online de uv fallo al acceder a PyPI (conexion 10061),
antes de ejecutar el probe. Se reutilizo websocket-client==1.8.0 desde cache
con `--offline`, sin modificar pyproject, lock ni configuracion global.
El primer probe termino con ConnectionRefusedError en el entorno restringido.
El segundo, fuera de esa restriccion y conservando proxy/TLS, recibio HTTP 403
con pagina **Proxy WebGateway | EPM**, a las 15:14:13 UTC, antes de Authenticate.
No se atribuye el rechazo a credenciales invalidas ni a permisos eToro.

Evidencia nueva, sin sobrescribir capturas anteriores:
`runtime/a7-websocket/recheck-20260921/summary.json` y
`runtime/a7-websocket/recheck-20260921-network/summary.json`.
Ambas claves PRESENT; autenticacion y suscripcion no alcanzadas; 0 eventos,
0 eventos frescos, 0 reconexiones automaticas y 0 mutaciones. Edades, bid/ask,
spread y frescura al decidir no medibles; duplicados/out-of-order sin muestra.
No hay fixture real, migracion PASS ni vertical slice externo.

Comando del segundo probe (exit Python 2 / launcher 1):

```powershell
.\scripts\uv.ps1 run --offline --frozen --env-file .env --with websocket-client==1.8.0 python scripts/probe_etoro_websocket.py --output runtime/a7-websocket/recheck-20260921-network
```

Se detiene la integracion en el gate externo solicitado. Siguiente dependencia:
la red debe permitir el upgrade a ws.etoro.com:443/ws; luego repetir observacion
durante mercado abierto antes de implementar cache/reconnect e inyeccion al runner.
No se cambia el proxy para eludir la denegacion. Sin fallback REST permisivo,
sin ordenes, sin cambios en Strategy 1, RiskEngine, Massive o hashes A3.
Checks de esta reobservacion: docs/VERIFICATION.md.

A7 PARTIAL/BLOCKED: HTTP 403 del proxy EPM antes de Authenticate; sin quotes reales.

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
