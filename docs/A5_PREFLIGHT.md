# A5 — preflight eToro DEMO de solo lectura

Estado 2026-09-16: **A5 CLOSED / DEMO_READ_VERIFIED** con preflight real propio.
CLI sin instrumentación: 12:55:35.171934Z, exit 0, PASS; tres GET/HTTP 200,
identidad Demo, 16 scopes, credit virtual y AAPL resueltos. Evidencia local
runtime/a5-preflight/demo-read-verified.json. No A6, órdenes ni Demo Write.
El hito histórico comunicado se conserva y ahora hay evidencia del proceso propio.

## Revisión previa y alcance

Se leyeron AGENTS → STATUS → HANDOFF → TASKS, contexto, arquitectura, cambios,
pendientes, decisiones y ETORO_API_AUDIT antes de modificar el transporte.
El cliente existente es GuardedTransport/httpx; Credentials obtiene exclusivamente
ETORO_API_KEY y ETORO_USER_KEY del entorno. No carga .env ni hereda credenciales MCP.
Ya existían perform_preflight, PreflightEvidence, EtoroMarketDataProvider,
DemoAuthorization, JsonFormatter/redact y `bot etoro preflight --read-only`.
Se revisaron consumidores del preflight (CLI/tests), adaptador, modelos Instrument/
OrderIntent/Position, Strategy 1 v1/configuración A3, manifiesto A2, errores HTTP,
pruebas de contratos y CI offline con secretos retirados y sockets externos bloqueados.

La implementación reutiliza esas piezas. brokers/preflight.py orquesta el informe;
la CLI serializa JSON y guarda evidencia opcional. No construye EtoroDemoAdapter,
OperationService, señales ni órdenes. No modifica Strategy 1, datos, riesgo,
reservas, propiedad, recuperación, configuración congelada, dependencias o lock.

## Contrato verificado y decisiones

El 2026-09-16 se consultaron los contratos oficiales mediante get-route-spec:
getMe, getTradingInfoDemoPortfolio y getSecurities. Referencia previa preservada:
[snapshot](etoro_spec_snapshot.json). La [autenticación oficial](https://api-portal.etoro.com/core/getting-started/authentication)
documenta claves de usuario separadas por entorno y permiso Read/Write.
Las consultas de catálogo no constituyen acceso a cuenta ni evidencia de conexión.

| Orden | Operación permitida | Verificación |
|---|---|---|
| 1 | GET /api/v1/me | demoCid entero positivo; scopes Demo explícitos; sin scopes reales, wildcard, formato desconocido o CID Demo igual al real |
| 2 | GET /api/v1/trading/info/demo/portfolio | clientPortfolio.credit finito y no negativo; listas válidas; CID coincidente donde aparece |
| 3 | GET /api/v2/market-data/instruments | símbolo del manifiesto A2, type=Stocks, pageSize=100; exactamente un resultado, hasNext=false, IDs positivos |

`me` describe identificadores de ambas cuentas; la mera presencia de realCid no
significa usar dinero real. No hay un booleano universal `isDemo`. La evidencia
conjunta exigida es demoCid + scope Demo + lectura válida de la ruta Demo. Un
portfolio vacío carece de CID propio: se conserva esa limitación y se exige todo
lo anterior. Ausencia, contradicción, JSON con claves duplicadas o estado HTTP
inesperado fallan cerrados. No se consulta ninguna ruta de cuenta real.

Los scopes documentados corresponden al token OAuth; si la autenticación por
claves no los devuelve, se bloquea sin inferirlos de la configuración. Los scopes
presentados son observados; el listado de inferidos queda vacío. Un scope Write
observado no prueba ejecución ni habilita mutaciones. UNKNOWN nunca equivale a
Demo; scopes reales/ambiguos fallan sin avanzar al portfolio. El informe mantiene
UNKNOWN cuando no se ha probado inequívocamente el entorno completo.

`credit` se presenta como crédito virtual del portfolio, sin inventar moneda ni
equipararlo al efectivo reconciliado utilizable para sizing. La API de metadata es
compartida: no existe una variante Demo de instrumentos. Se consulta después de
verificar Demo con las mismas credenciales. AAPL procede de
docs/massive-a2-manifest.json, no de un ID eToro hardcodeado. Se valida resolución
de metadata de la acción de investigación; no elegibilidad de cuenta, subyacente,
stops, precisión, volumen o RVOL. SPY/QQQ siguen como referencias, no operables.

El preflight restringe irreversiblemente su instancia de transporte a las tres
rutas GET anteriores antes del primer envío. Bloquea POST/PUT/PATCH/DELETE/HEAD,
POST de costes/elegibilidad, otras rutas GET y cualquier host alternativo; también
en MockTransport y aunque hubiese autorización previa. Conserva TLS, proxy/CA,
allowlist, cuotas, retries acotados de lectura y rechazo de redirects existentes.
La instancia se cierra al terminar; no se reutiliza para un runner.

## Ejecución reproducible y evidencia

Las claves existentes en .env se cargan explícitamente antes de iniciar Python;
no se generan, modifican ni muestran valores. Desde la raíz del repositorio:

```powershell
.\scripts\uv.ps1 run --frozen --env-file .env bot etoro preflight --read-only --config configs/strategy-1-v1.yaml --evidence runtime/a5-preflight/demo-read-verified.json
```

Elegir un archivo nuevo en cada ejecución: apertura exclusiva, sin sobreescribir
evidencia. `--instrument-manifest` permite indicar otro manifiesto A2 válido;
el default es el manifiesto aprobado existente. No descarga ni carga barras.
Salida JSON legible: conectividad, entorno, verificación Demo, scopes, crédito,
instrumento, protección de mutaciones, resultado, timestamp UTC, configuración,
rutas intentadas (incluidos retries) y estados HTTP recibidos. Exit Python 0 solo
para PASS completo; 2 para fallo. Una respuesta HTTP acredita conectividad, no
autenticación ni seguridad Demo por sí misma.

Se omiten perfil, portfolio completo, CID original, headers y huella de claves.
El identificador usa hash con sal aleatoria por sesión, no correlacionable entre
runs. Se redactan ambas claves incluso si una respuesta las refleja. Los errores
HTTP/red usan razones estáticas. El JSON local con crédito queda bajo runtime
ignorado; no publicar ni versionar datos de cuenta. `writes=0` expresa la barrera
del cliente; no pretende sustituir una auditoría independiente del servidor.

Antecedente superado (solo entorno exportado): 2026-09-16T12:38:58.942252+00:00, exit Python **2**,
CREDENTIALS_MISSING_OR_INVALID. Ambas variables ausentes en este proceso;
operaciones=[], writes=0, identidad UNKNOWN, sin cash ni instrumento consultados.
Evidencia local: runtime/a5-preflight/process-evidence-20260916.json y
process-result-20260916.json (comando, disponibilidad booleana y exit exacto).
El primer intento está preservado en attempt-20260916.json; el wrapper PowerShell
reportó 1 para ese fallo, por lo que el segundo registró explícitamente el exit
del proceso Python, 2. No se obtuvieron ni copiaron secretos del conector.

## Validación y pendientes

Tests focales y gates exactos en [VERIFICATION](VERIFICATION.md). Los tests nuevos
usan HTTP fabricado y cubren éxito, REAL/UNKNOWN/ausente/ambiguo, efectivo inválido,
metadata parcial/duplicada, 401/403/429, timeout/red, JSON inválido/duplicado,
redirect, estado inesperado, rechazo de todos los métodos mutantes y secretos.
El test real reproducible es el comando explícito anterior, separado de pytest y
CI offline. No se desactiva su barrera de sockets ni se introducen skips engañosos.

No quedan criterios A5 pendientes. Para repetir, elegir un nombre de evidencia
nuevo y un entorno con conectividad al origen aprobado. Un futuro fallo mantiene
FAIL sin rebajar validaciones. A6, shadow, órdenes y Demo Write permanecen fuera
de alcance; observar trade.demo:write no valida ni habilita escrituras.

## Continuación: diagnóstico de carga y ejecución real

| Comprobación | Resultado |
|---|---|
| Directorio real | C:/Users/epulgare/Nueva carpeta/Bot 3 |
| Archivo esperado por la aplicación | Ninguno: Credentials.from_environment usa os.getenv exclusivamente |
| Archivo elegido explícitamente | .env de la raíz; existente, ignorado por Git, no modificado |
| Nombres exactos en archivo | ETORO_API_KEY: PRESENT; ETORO_USER_KEY: PRESENT |
| Entorno antes / después de cargar | Ambas MISSING antes; ambas PRESENT después de uv --env-file .env |
| Momento de carga | uv prepara el entorno del hijo antes de iniciar Python/CLI y el formatter de logs |
| Launcher | No cambia cwd; solo UV_CACHE_DIR, UV_PYTHON_INSTALL_DIR y PYTHONUTF8; delega argumentos a uv |
| Selección alternativa | UV_ENV_FILE y UV_NO_ENV_FILE ausentes inicialmente; YAML no selecciona archivos de secretos |
| CLI / Python directo | Ambos leen variables exportadas; sin carga implícita de .env |
| pytest / verify.py | Retiran credenciales; pytest bloquea sockets externos, por diseño |

La documentación OPERATIONS_RUNBOOK ya indicaba que .env no se carga
automáticamente. No había un defecto en el loader: faltaba seleccionar el archivo
al invocar uv. La corrección fue operacional/documental, sin framework, dependencia,
fallback, cambio de defaults o modificación del launcher. La ruta relativa .env
funcionó; se usa desde la raíz y no depende de búsquedas implícitas de archivos.

Se ejecutó el comando originalmente pedido con UV_ENV_FILE=.env únicamente en
el proceso lanzador. runtime/a5-preflight/demo-read.json conserva el fallo real de
red: tres intentos GET /api/v1/me, ninguna respuesta HTTP, ETORO_READ_UNAVAILABLE.
Diagnóstico posterior: ConnectError → ConnectionRefusedError, WinError 10061;
ambas claves PRESENT, CA local PRESENT, .env sin cambios. No era un 401/403 ni
un rechazo de credenciales del proveedor. No se desactivó TLS ni se cambió proxy.

La ejecución autorizada fuera de la restricción de red tuvo PASS a las 12:55:02Z;
la CLI sin instrumentación confirmó PASS a las 12:55:35Z, exit 0. El entorno
restringido aportaba proxies; el entorno externo autorizado no los aportaba. No se
modificaron variables globales ni configuración de seguridad para obtener el PASS.
Se preservaron los intentos fallidos; por eso el PASS usa demo-read-verified.json.

Evidencia local ignorada por Git:

- env-diagnostic.json: presencia de nombres y ausencia inicial en el entorno.
  Su primer intento con ruta absoluta falló en uv; la carga relativa posterior
  quedó confirmada por los diagnósticos de red y el preflight PASS.
- demo-read-network.json.diagnostic.json: claves PRESENT, error WinError 10061,
  exit Python 2 y comprobación interna env_file_unchanged=true.
- demo-read-network-unrestricted.json y .diagnostic.json: PASS, exit 0,
  claves PRESENT, sin errores de transporte, env_file_unchanged=true.
- demo-read-verified.json: evidencia definitiva de CLI sin instrumentación,
  configuración/estrategia, referencia de identidad sanitizada, scopes observados,
  credit virtual, instrumento y exactamente tres GET con HTTP 200.

La comprobación real observó trade.demo:read y trade.demo:write, además de scopes
de lectura; ninguno real o wildcard. Solo se ejercitaron lecturas. El importe y
la referencia privada de cuenta quedan en runtime, no en documentación versionable.
El crédito no equivale a efectivo reconciliado para sizing; moneda no provista.

| Criterio A5 | Evidencia de aceptación |
|---|---|
| Preflight real disponible y conectividad | CLI exit 0 / overall PASS; tres HTTP 200 |
| Exclusivamente read-only | Tres GET de la allowlist; writes=0 |
| Identidad Demo explícita | demoCid/scopes/ruta Demo y validaciones PASS; CID solo en memoria |
| REAL falla | Tests focales de scopes reales e identidad real-only, sin lectura posterior |
| UNKNOWN falla | Tests de tipo ausente/desconocido/ambiguo, sin fallback Demo |
| Scopes inspeccionables | 16 observados en /me; inferidos=[] |
| Cash virtual consultado | clientPortfolio.credit finito y no negativo; PASS externo |
| Instrumento Strategy 1 | AAPL del manifiesto A2; ID eToro 1001, Stocks, exchangeId 4 |
| Protección mutante automatizada | Tests de POST/PUT/PATCH/DELETE/HEAD y GET fuera de allowlist |
| Pruebas adecuadas | 202 focales PASS; 61 casos A5 incluidos; suite previa 719 PASS |
| Secretos protegidos | Output redactado; .env no modificado/ignorado; escaneo final sin hallazgos |
| Comando reproducible | uv --env-file .env, config v1 y --evidence explícitos |
| Evidencia real sanitizada | demo-read-verified.json, timestamp 2026-09-16T12:55:35.171934Z |
| Documentación actualizada | A5, runbook, contexto, decisiones, changelog, pendientes, continuidad y checks |
| A6 fuera de alcance | Sin runner, señales, órdenes ni activación; Strategy 1 intacta |
| Diff limitado/revisado | Continuación solo documental y artefactos runtime ignorados; código previo preservado |
