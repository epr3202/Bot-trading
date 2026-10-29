# Auditoría local A7 y publicación — sin cierre del alcance

2026-10-29. **A7 PARTIAL / BLOCKED; entrega WIP. REAL trading fuera de capacidad.**
Sin implementación de correcciones. El resultado posterior del push y el SHA de
continuación se registran en `A7_PUBLICATION_20261029.md`; este informe no anticipa
éxito de publicación antes de ejecutar y comprobar el push.

## A. Árbol auditado y límites

Copia existente `Bot 3`: cwd y raíz Git coinciden (ruta absoluta solo en logs locales,
reemplazada por `<repo>` en evidencia publicable). Rama inicial
`feat/phase3-readonly-evidence`, upstream `origin/main`.
HEAD inicial: `575216da1fe94e147ed5ec32420d9feec3bec8f6`.
Remoto verificado: `https://github.com/epr3202/Bot-trading.git`.
Python verificado: 3.12.12, `.venv/Scripts/python.exe`; uv mediante `scripts/uv.ps1`,
cache/Python locales y lock congelado. Identidad Git existente configurada, sin
modificarla. Modelo/esfuerzo exactos: no verificados, no se atribuyen.

Leídos AGENTS → STATUS → HANDOFF → TASKS, instrucciones locales de brokers,
ejecución, persistencia y riesgo, documentos A7 y contratos locales riesgo/lifecycle.
`SCOPE.md` ausente: se usan exclusivamente los siete criterios del encargo.
No se revalidaron especificaciones online ni otros hitos. No se leyeron `.env`,
secretos o respuestas privadas de cuentas. No preflights, conexiones a proveedores,
WebSocket ni trading. Git es la excepción autorizada a la prohibición histórica.

[Manifiesto inicial](audits/a7-local-20261029/manifest.json): 193 archivos versionados
no secretos, incluidos los nueve modificados. SHA-256 del archivo exacto:
`1c1146e86acece296db2f6f794c14abd7c62c7a26385234bc1dcc04f25625d73`.
Huella de otros hitos solo para preservar, sin auditarlos funcionalmente.

## B. Inventario y comparación

Antes de pruebas/staging: **0 commits salientes, 0 staged, 0 untracked no ignorados,
9 unstaged**. Todos atribuibles a A7; 429 inserciones y 14 eliminaciones:

| Archivo | Trabajo existente seleccionado |
|---|---|
| `.env.example` | Cuatro variables proxy vacías |
| `scripts/probe_etoro_websocket.py` | Proxy explícito, redacción y TLS estricto |
| `tests/test_etoro_websocket_probe.py` | Negativos proxy/redacción/CA PEM y DER |
| `scripts/scan_secrets.py` | Patrón de contraseña proxy |
| `scripts/verify.py` | Retirada de variables proxy en checks |
| `STATUS.md`, `HANDOFF.md` | Continuidad histórica A7, sin edición durante auditoría |
| `docs/A7_WEBSOCKET.md`, `docs/VERIFICATION.md` | Diagnósticos y validaciones anteriores |

No hay cambios ajenos a A7 detectados. `src`, configuración productiva, dependencias,
lock y tests restantes no tienen diff inicial. No hay historial saliente anterior.
(a) Commit histórico indicado, (b) referencias remotas locales antes del fetch y
(c) remoto consultado ahora coinciden en `575216da1fe94e147ed5ec32420d9feec3bec8f6`.
Fetch: 14:05:14 UTC, exit 0. `git ls-remote origin`: 14:06:15 UTC, exit 0,
HEAD/main con ese SHA. Fallaron primero escritura FETCH_HEAD y conexión del sandbox;
los reintentos autorizados funcionaron sin modificar proxy/TLS/configuración global.
No pull, merge, rebase, force push, stash, reset, clean, restore ni checkout de archivos.

Evidencia ignorada conservada: `runtime/a7` (11 archivos), `a7-completion` (15),
`a7-quote-audit` (11), `a7-websocket` (18). `.env` y `certs/epm-root.cer` existen:
comprobación de existencia únicamente. No se publican originales privados, bases de
datos, raw, entornos o cachés. Logs nuevos en `runtime/a7-local-audit-20261029`.

## C. Contraste histórico

Sigue vigente la ausencia de runner externo y la barrera MockTransport. Cambió el
spike: proxy explícito, confianza sistema+certifi+CA local, fallo por CA ausente y
pruebas. Sigue NOT_INTEGRATED. Las notas antiguas «spike sin cambios» describen una
etapa anterior; no describen el diff actual. UNKNOWN para todo rechazo ya estaba
superado en HEAD por `RejectedBeforeSend`.

Nueve resúmenes históricos inspeccionados contienen cero eventos/mutaciones.
El último, `tls-policy-20260921/summary.json`, comenzó el 21/09 a las 15:47:45 UTC:
HTTP 403, sin autenticación/suscripción y frescura no medible. Se exportan solo
campos permitidos en [resúmenes](audits/a7-local-20261029/historical-sanitized.json).
Respaldan el antecedente, **no acreditan conectividad o bloqueo actuales**.
La atribución específica a CONNECT/TLS/política del gateway permanece histórica,
sin revalidación de instrumentación o credenciales.

Los [registros de tests históricos](audits/a7-local-20261029/historical-tests-sanitized.json)
contienen 905/912 passed, fechas y huellas distintas. También se conserva el primer
registro **2 failed / 903 passed**, con código cambiado durante checks. No se hereda
ningún PASS. Las 34 pruebas TLS históricas no se atribuyen como nueva ejecución
separada: el archivo del spike sí está incluido en la batería actual.
Los retrasos REST 35.860831/75.107782 s siguen como documentación histórica,
sin nueva consulta ni lectura de respuestas privadas. Frescura actual no confirmada.

## D. Hallazgos y validación focal

- Criterio 1: `execution/session.py:23` y `:36` fijan SimulatorBroker;
  `service.py:217` bloquea sesión Demo conectada. `brokers/transport.py:245`, `:366`
  y `:424` fijan mutaciones a MockTransport exacto. No hay ciclo externo completo.
- Criterios 2–5: `brokers/identity.py:27`, `transport.py:267` y `:346` exigen identidad
  Demo fresca, scope write, vínculo de cuenta/credencial/sesión/config y caducidad.
  `etoro_demo.py:149` converge en el guard para submit/cancel/close/protect. Origen
  fijo, rutas Demo enumeradas; `config.py:44` solo admite cuatro modos y prohíbe
  extras. `settlementType=real` es campo del activo en ruta Demo, no modo REAL.
- Criterio 6: `execution/engine.py:94`, `:146`, `:163`, `:218` conservan riesgo,
  intención/reserva durable, rechazo previo medido, UNKNOWN, deduplicación/recovery.
  `risk/engine.py:248` revisa disponibilidad/frescura; `store.py:218` y `:349`
  conservan persistencia. `etoro_demo.py:165`, `:511`, `:547` verifican propiedad,
  cantidad y protección. ACK no es fill. Cierre contable externo sigue sin acreditar.

Selección: identidad (negativos/composición SQLite), pre-send (reservas/crash),
transporte (allowlist/autorización) y spike modificado. Suplemento: seis variantes
contra transporte no mock y un caso de cierre que conserva UNKNOWN sin inventar
fill/coste/exposición restante. No suite completa ni `scripts/verify.py` ejecutados.
Adaptador importado como fixtures: no se atribuye su archivo completo como ejecutado.
Tampoco se ejecutaron completos test_demo_session o test_demo_quote_cost_audit.

Antes de ejecutar: conftest, tests y fixtures revisados; conexión externa bloqueada,
MockTransport/NetworkSpy y WebSocket ficticio. Proceso hijo retiró credenciales,
proxies y variables de inyección; fijó offline, UV_NO_ENV_FILE y desactivó autoload
de plugins. Sin cambiar entorno global ni leer `.env`.

| Comprobación desde raíz | UTC de fin | Resultado actual |
|---|---|---|
| pytest focal, cuatro archivos | 14:06:25 | exit 0, 190 passed, 0 failed/skipped, 1 warning NumPy/calendar |
| Dos nodos de test_phase2_broker | 14:08:26 | exit 0, 7 passed, 0 failed/skipped |
| Ruff check, cuatro Python modificados | 14:07:43 | exit 0 |
| Ruff format --check, mismos archivos | 14:07:28 | exit 0, cuatro ya formateados |
| Escáner existente y autocomprobación | 14:07:22 | exit 0, 193 candidatos, 0 hallazgos |
| git diff --check | 14:06:56 | exit 0, avisos CRLF→LF sin cambio de bytes |

[checks.json](audits/a7-local-20261029/checks.json) contiene comandos completos,
wrappers, cwd sanitizado, HEAD/manifiesto, fechas, exit codes y salidas. Incluye
fallos iniciales Git y errores del invocador Windows/quoting antes del reintento;
no se presentan como PASS. La creación inicial del informe mediante apply_patch
no terminó y se canceló; se creó este archivo nuevo mediante PowerShell.

## E. Siete criterios

| # | Estado | Evidencia y límite |
|---|---|---|
| 1 | ❌ | Incumplimiento observado: runner externo ausente y red mutante bloqueada. Evidencia externa insuficiente; no se enviaron órdenes para completarlo. |
| 2 | ✅ | test_demo_only_identity.py:87 y :117: REAL/UNKNOWN/error rechazan cuatro operaciones, cero mutaciones. Ejecutados. |
| 3 | ✅ | Tests :245 y :267, config/transport inspeccionados: modos y rutas REAL rechazados. |
| 4 | ✅ | Tests :161, :185, :254: identidad cambiante, cuenta, claves, sesión, config, caducidad y entorno engañoso no evitan guard. Suplemento verifica transporte no mock. |
| 5 | ✅ | Test :87: configuración/credenciales ficticias válidas y permiso previo; REAL rechazada sin mutación, no por claves ausentes. |
| 6 | ❌ | Evidencia externa insuficiente: composición local/recovery PASS (:276; pre-send :53, :94, :200), pero runner/cierre externo no acreditados. No se observa retirada de controles. |
| 7 | ✅ | 197 casos focales actuales PASS; REAL fuera de capacidad. No equivale a integración externa ni CI PASS. |

## F. Publicación

Rama nueva `audit/a7-local-20261029T140900Z`. Selección explícita de nueve archivos
existentes más informe/evidencias. Sin staging ajeno ni necesidad de índice temporal.
Resultado VERIFIED/BLOCKED, SHA local/remoto, commits, archivos y comprobación se
registran tras ejecutar el push en `A7_PUBLICATION_20261029.md` y logs locales.

Escáner revisado: tracked/untracked de texto no ignorado, patrones de claves y rutas
sensibles; autocomprobación con cadenas ficticias pasó. No basta para blobs staged,
historia o todo formato de secreto: se complementa con diff y escaneo exacto de
blobs salientes antes de publicar. No se comparan valores secretos de `.env`.

Único workflow `.github/workflows/ci.yml`: push/PR ejecutan checks/tests offline,
doctor/demo-offline y build; contents:read, sin deployment ni trading. Automatismos
privados externos al repositorio no verificados. No efecto no autorizado identificado
en la automatización inspeccionada. Sin PR, merge, push a main, cambios de permisos,
visibilidad o configuración global. Push exitoso no implica CI PASS.

## G. Preservación

[Comparación](audits/a7-local-20261029/preservation.json): 193 archivos iniciales
idénticos byte a byte al preparar entrega; se repite después del push en recibo local.
No código/tests/configuración/dependencias/lock/snapshots/documentos previos editados.
STATUS/HANDOFF se publican tal como estaban; TASKS no se cambia. Solo se crean
informe y evidencias. Git cambia rama/índice/objetos/referencias como parte de entrega.
Tests generan SQLite/locks/evidencia ficticia UUID bajo runtime/test-artifacts y
cachés/bytecode ignorados; no se borran. Secretos no leídos ni tocados, sin hash atribuido.

## H. Continuación

Usar rama y SHA confirmado en `A7_PUBLICATION_20261029.md`. Python 3.12.12, uv local
Windows, lock congelado y aislamiento en checks.json. El spike documentado usa
websocket-client 1.8.0 mediante uv --with, sin dependencia productiva integrada.
CA local, configuración de red/credenciales, raw/estado privado y evidencias originales
quedan deliberadamente fuera. No reutilizar autorizaciones de sesión caducadas.

Siguiente comprobación mínima A7, no ejecutada: en entorno autorizado, revalidar
primero gate read-only WebSocket/frescura con TLS intacto y sin órdenes. Después
corresponderá resolver runner/cierre contable bajo encargo autorizado. Publicación
no resuelve HTTP 403 ni garantiza conexión; no autoriza evadir políticas, infraestructura
nueva ni REAL. **A7 no se declara cerrado.**

Riesgos observados: runner/cierre externo no verificado (session.py:36, transport.py:424).
El spike requiere CA local excluida y sigue NOT_INTEGRATED (probe_etoro_websocket.py).

Backlog sugerido fuera de A7: ninguno.
