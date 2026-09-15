# Continuidad — Massive histórico, 2026-09-15

Partida limpia `262944f`; misma rama local feat/phase3-readonly-evidence.
Massive agregado como proveedor independiente histórico read-only. No se cambian
Alpaca, eToro, estrategia, riesgo, ejecución, configs ni lock. La clave dedicada
estaba presente en el proceso; no se leyó ningún perfil ni se guardó su valor.

Primer intento restringido CONNECTIVITY_FAILED antes de respuesta. Repetición
con permiso de red: un GET histórico, HTTP 200 a las 12:27:06.148056 UTC,
17.588 barras raw y 8.190 regulares; 21/21 sesiones válidas, objetivo 14/09.
**MASSIVE_HISTORICAL_RVOL_VERIFIED**, igualdad exacta de cinco métricas:
ORH 334.83, ORL 331.72, V5 1834725.760868, media 1690527.49202725,
RVOL 1.085297795818647139199521439. Sin latencia de datos inventada.

Raw inmutable: data/raw/massive/20260915T122702-6a68f76c.
Informe real: runtime/massive-audits/20260915T122702-6a68f76c/result.json.
Contrato, esquema, semántica documental y CLI: docs/MASSIVE_DATA_CONTRACT.md.
Solo manifiesto saneado en docs/massive-historical-manifest.json; no dataset en Git.
Código `8ed65eb`; 574 pruebas, 16/16 gates, cobertura 90,525210%, sin fallos/skips
ni reducción crítica. Comandos y huellas exactos en docs/VERIFICATION.md.
Baseline anterior preservado en runtime/massive-phase-20260915T071442/prior-*.
Gates finales estables en la misma carpeta, final-{verification.json,coverage.json,test-results.xml}.
Reauditoría offline: runtime/massive-audits/20260915T123151-9e27df3a/result.json;
misma aritmética y checksums. CSV real importado con 8.190 barras, gate preservado.

El hito solo acredita histórico AAPL. No acredita señales causales, latencia
realtime ni rentabilidad. El motor rechaza HISTORICAL_DOWNLOAD con
OBSERVED_AVAILABILITY_REQUIRED; cero candidatos/señales. No modificar observed,
warmup o estrategia para saltarlo. El nombre del plan no está en el endpoint;
se acredita acceso, no una suscripción concreta. Cierres extraordinarios y
correcciones históricas siguen siendo límites; DST/cierre temprano se prueban
localmente, no se observaron en esta ventana.

Esta fase termina en la validación histórica. No iniciar shadow ni Demo Write.
Mantener eToro DEMO_READ_VERIFIED previo, entries_armed=false,
external_mutations=DISABLED y order_submission_enabled=false.
Alpaca conserva su bloqueo externo anterior; no se volvió a consultar eToro.

## Antecedente — preparación para fase shadow, 2026-09-14

Partida limpia `43c9cc5b7d6366ee72d38dd17542ec7341e4e7e1`, misma rama local.
Resultado vigente: BLOCKED_BY_EXTERNAL_CONFIGURATION, motivo
ALPACA_CREDENTIALS_UNAVAILABLE; SHADOW_NOT_READY. Ambas variables ausentes.
El comando oficial de captura devuelve ese motivo antes de red, sin raw Alpaca.
Evidencia en runtime/alpaca-audits/20260914T195435-d5744088/result.json;
comprobaciones previas preservadas en runtime/shadow-readiness-20260914/prior-*.

Status/razón separados; timeout es conectividad, 429 es rate limit y la negativa
SIP no se registra como entitlement aprobado. Feed sin eco queda desconocido aun
en capturas antiguas; duplicados y volumen cero bloquean calidad. Auditoría genera
data-quality.json; parseos interrumpidos dejan conteos desconocidos. No cambian
estrategia, riesgo, transporte eToro, Python ni lock. Commit código `b7a17b7`;
`scripts/verify.py` final: **512 pruebas, 16/16 gates, 90,488615% de cobertura**,
sin fallos/skips y módulos críticos sin reducción. Evidencia exacta:
[VERIFICATION](docs/VERIFICATION.md).

Siguiente acción externa: titular del acceso ejecuta el comando desde un proceso
con las variables dedicadas heredadas, sin pegar secretos ni cambiar a IEX. Después
resolver evidencia explícita del feed y validar AAPL/21. Ampliación a 60 sesiones,
baseline real y preparación shadow siguen condicionados, no ejecutados. El gate
de disponibilidad histórica es un bloqueo adicional: no backdatear ni falsificar
observed para generar señales. Secuencia completa: [SHADOW_READINESS](docs/SHADOW_READINESS.md).

Se mantienen DEMO_READ_VERIFIED histórico, entries_armed=false,
external_mutations=DISABLED, order_submission_enabled=false y Demo Write NOT_TESTED.
No repetir lectura de cuenta, iniciar shadow ni continuar después de esta decisión.

## Antecedente — Alpaca histórico

La etiqueta antigua de insuficiencia por ausencia de credenciales queda corregida
por el estado vigente anterior; sus artefactos raw y resultados se preservan.

Se continuó desde 134844b y árbol limpio. Baseline y gates anteriores preservados en
runtime/alpaca-phase-20260914T184730. DEMO_READ_VERIFIED no se volvió a diagnosticar;
eToro audit-only mantiene ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL.

Alpaca incorporado como proveedor independiente sin SDK: data/alpaca_http.py solo
GET data.alpaca.markets/v2/stocks/bars; data/alpaca.py carga archivos a DataBundle;
data/alpaca_audit.py compara raw/Fraction con el cálculo Decimal del motor.
CLI explícita scripts/audit_alpaca_history.py; salida CSV/manifiesto compatible con
provider=import existente. Fixture sigue predeterminado. RiskEngine, ExecutionEngine,
el adaptador eToro y sus rutas no cambian. No se amplió MarketDataProvider.

Consulta inicial prevista AAPL/1Min/SIP/split: 2026-08-13 13:30Z a 2026-09-11 19:59Z
(end inclusivo), 20 sesiones previas más objetivo cerrado 11/09. Intento real:
ALPACA_CREDENTIALS_UNAVAILABLE antes de red, sin bytes ni feed efectivo.
Estado C: ALPACA_DATA_INSUFFICIENT_FOR_RVOL; no es evidencia de falta de entitlement.
Resultado original en runtime/alpaca-audits/20260914T185623-4eab7c52/result.json;
manifiesto saneado versionado en docs/alpaca-historical-manifest.json.
No solicitar claves ni buscarlas en perfiles/otros proyectos. El siguiente paso es
ejecutar el comando documentado desde un proceso con ALPACA_API_KEY/ALPACA_API_SECRET
ya disponibles, sin volver a consultar eToro. No comprar plan ni cambiar a IEX.

La aritmética ORH/ORL/RVOL existente se extrajo a ORBStrategy.opening_metrics, usada
también por process_session. No cambian fórmulas, filtros, ranking, riesgo o TTL.
La comparación histórica usa esa parte numérica y ejecuta process_session por
separado: el gate OBSERVED_AVAILABILITY_REQUIRED permanece. Tolerancia absoluta
1e-12 y relativa cero; resultado real NOT_RUN. Nunca se declara observed ni se
inventa latencia para pasar la prueba. Historical snapshots conservan correcciones
como posibilidad; no prueban primera recepción ni señales realtime.

38 pruebas nuevas Alpaca aprobadas: mapping, identidad de feed, tiempos, huecos,
duplicados, paginación, HTTP, cuotas, CSV y cálculo independiente. 15 pruebas previas
de estrategia/datos también aprobadas. Batería final: 491 pruebas, 16/16 gates;
cobertura 90,070065% y todos los módulos críticos mantienen exactamente la cobertura
previa. Código estable, Python/lock conservados; final-gates dentro del baseline
guarda las salidas exactas. Ver commits en VERIFICATION.
Scripts de gates y fixtures de tests retiran también las variables Alpaca, y scanner
incluye sus nombres. Datos raw solo en data/raw/alpaca; resultados en runtime.

Guardas mantenidas: entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED. No shadow en esta fase,
ni siquiera si un histórico llega a aprobar; WebSocket es un alcance posterior.
Documentación del esquema, contrato y estados en docs/ALPACA_DATA_CONTRACT.md.

## Hito anterior conservado — Market Data eToro

El usuario confirmó DEMO_READ_VERIFIED desde Bot 3, con conexión, autenticación e
identidad Demo verificadas y cero escrituras. Hito registrado en baseline.json,
sin repetir consultas de cuenta. X01 de las secciones históricas está superado;
no pedir claves ni reiniciar diagnóstico de conectividad.

Esta fase obtuvo siete respuestas HTTP 200 exclusivamente Market Data mediante
execute_read del conector eToro. La consulta local de instrumentos no pudo iniciarse
con el contexto de proceso del agente; no se atribuye al bot la captura MCP.
Datos reales, sin mocks de adquisición: AAPL/1001/Nasdaq, bid/ask, 1.000 minutos
asc/desc, 30 diarios y repetición de 10 minutos. No se consultó elegibilidad, cuenta,
portafolio ni otra ruta de trading. No se cambió la allowlist del transporte.

Resultado: ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL. Volumen de unidades desconocidas;
0/20 sesiones previas completas, 0/20 aperturas históricas. La ventana regular actual
no tiene huecos entre minutos ya cerrados, pero el histórico requerido no cabe en
el contrato de 1.000 velas sin fecha/cursor. ORH=334,54, ORL=331,72 y volume de
apertura=1.181.044 calculados independientemente sobre AAPL 2026-09-14. RVOL y
comparación numérica con el motor bloqueados; este rechaza con
OBSERVED_AVAILABILITY_REQUIRED, sin alterar ninguna regla ni falsear disponibilidad.

Raw: data/raw/etoro-market-20260914T164913. Informe/CSV/manifiestos y hashes:
runtime/market-audit-20260914T164913/final-analysis. Cuerpos raw inmutables, revisiones
separadas y sin datos privados en Git. `scripts/audit_etoro_market_data.py` reproduce
el análisis sin red; requiere directorio de salida nuevo. Diez regresiones nuevas
cubren exclusión de vela abierta, huecos/duplicados, denominador sin hoy, OHLC,
zonas y cierre temprano. Estado de gates en VERIFICATION.

Batería final: 453 pruebas sin fallos/skips, 16/16 gates, cobertura 90,686683%.
Huella estable y lock intacto; evidencia final en final-gates dentro de la carpeta
de auditoría. Commit local `2d6eec3` conserva el cambio previo de proxy/CA; el commit
de auditoría contiene este informe y el analizador sin red. No hay publicación.

Shadow NO INICIADO. Se mantienen entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED. El parser de quote
rechaza el timestamp sin offset observado; el análisis lo interpreta como UTC por
contrato y mide 43,076s hasta retorno de herramienta, por encima del gate de 3s.
Esto también impide tratar la captura como cotización fresca operativa.

Siguiente dependencia: volumen consolidado/ajustes acreditados y 21 sesiones de
minutos de un proveedor apto, preservando MarketDataProvider e importación existentes;
o aclaración contractual de eToro y cobertura demostrada. No reducir warmup ni usar
volumen diario/ticks para simular RVOL. Los bloqueos contables X04 siguen vigentes;
resolver datos tampoco autoriza Demo Write. Detalle en ETORO_MARKET_DATA_VALIDATION.

## Historia conservada — fases anteriores

Actualización 2026-09-14: el usuario solicitó adaptar el manejo de proxy del script
de oficios. Se revisó `oficios.py` en la carpeta de generación/recuperación sin
ejecutarlo ni importar credenciales. `create_http_client` aplica proxy del entorno
y prioridad CA local `certs/epm-root.cer` → `REQUESTS_CA_BUNDLE` → defaults HTTPX.
No se desactiva TLS ni se cambia configuración global. CA/proxy inválidos producen
error redactado sin fallback. Transportes inyectados no heredan el entorno; el
panel local mantiene conexión directa. No cambian guardas de escritura, identidad,
reservas, propiedad, recuperación ni datos/tiempos de disponibilidad.

Verificación: ocho pruebas nuevas aprobadas con
`.\scripts\uv.ps1 run --frozen pytest -q tests/test_corporate_network.py`.
Primer pase completo: 15/16 gates; dos pruebas nuevas parcheaban el símbolo
incorrecto de HTTPX. La guarda de sockets bloqueó la conexión externa y hubo
resolución DNS fallida del proxy ficticio; ninguna consulta de cuenta ni respuesta
externa. Se corrigió el aislamiento. Evidencia inicial conservada en
`runtime/proxy-verification-first.json`. Batería final:
`.\scripts\uv.ps1 run --frozen python scripts/verify.py`, salida 0;
16/16 gates, 443 pruebas sin errores/fallos/skips, cobertura 90,686683% y módulos
críticos por encima del 90%. Ruff check/format, mypy, escaneo de secretos, recorridos
offline, bloqueos negativos, build y sintaxis JS aprobados. Evidencia exacta en
`runtime/verification.json`, credenciales retiradas y código estable durante checks.

Construcción del cliente con entorno actual aprobada, sin solicitudes HTTP.
Proxy presente; CA corporativa no configurada ni encontrada en la carpeta de
referencia. Falta aportar CA autorizada mediante la ruta/variable documentada en
OPERATIONS_RUNBOOK y comprobar conectividad en un alcance autorizado. No se
realizaron lecturas de cuenta, operaciones externas, commits ni publicación.
Python 3.12.12 y uv.lock conservados. Los bloqueos históricos siguientes permanecen.

Proyecto existente C:/Users/epulgare/Nueva carpeta/Bot 3. Se mantuvieron Python
3.12.12, uv 0.12.12, uv.lock, ORB_RVOL_v0.1, 20 warmups, presupuesto, riesgo y TTL.
No hubo nuevo repositorio, migración de API, proveedor nuevo ni revisión independiente.
Revisión propia del agente; no se delegó esta fase.

Las dos capas ya están versionadas. Base A en main:
`6af05f1b16b8e3488a5cd959dc0e7f889b258fd6` (123 archivos idénticos al índice
original y su manifiesto, 358 pruebas en instalación aislada).
B en recovery/phase2-reviewed:
`ef8bf5564f6e15bd04ae084c18cd63dd27ba380b` (33 modificados + seis nuevos,
420 pruebas, importación y paquete offline).
C en feat/phase3-readonly-evidence:
`b51506a97771d04a5edfb45d46e8fac4c31f307f` (435 pruebas/16 gates).
La documentación de fase 2 que menciona identidad pendiente queda conservada en B
como historia; el bloqueo fue resuelto por el usuario. No volver a solicitarlo.

Fase 3 corrigió riesgos concretos: lookup exige exactamente un identificador;
una respuesta action=close no se contabiliza como apertura; status.id debe ser
entero y los estados 3/5/9/10 requieren evidencia de cantidad ejecutada. Los estados
9/10 conservan fills aunque su remanente sea terminal. El detalle v1 de cierre ya
no permite inferir remainingUnits a partir de la cantidad solicitada. La exposición
explícita del lookup de apertura continúa separada del libro, caja y PnL.

Lookup v2 sí documenta action=open/close, IDs de cuenta/orden/posición y estado.
OpeningData sigue siendo apertura; no existe closingData en el esquema consultado.
No extrapolar el enum v2 a statusID v1. Matriz de campos, diferencias guía/OpenAPI,
idempotencia por versión y preguntas de soporte NO ENVIADAS en ETORO_API_AUDIT.
La normalización contable de cierres y recuperación legacy sin ID siguen bloqueadas.

| Bloqueo | Responsable | Evidencia pendiente | Acción mínima |
|---|---|---|---|
| X01 Demo Read NOT_CONFIGURED | Titular de cuenta/aplicación | Clave de aplicación y clave de usuario Demo Read en el proceso; identidad/scopes/portfolio verificados por el bot | Configurarlas localmente según OPERATIONS_RUNBOOK y ejecutar el preflight existente una vez tras el cambio; no pegar secretos |
| X02 BLOCKED_DATA | Titular del acceso/dataset | CSV/Parquet autorizado, 21 sesiones completas, volumen comparable, ajustes/procedencia/tiempos; o acceso ya licenciado sin gasto | Aportar el archivo y manifiesto localmente; el candidato público de cuatro registros es insuficiente y su descarga falló con WinError 10061 |
| X04 Contabilidad externa BLOCKED | Soporte eToro y responsable de integración | Enlace v1→lookup, enum legacy, fills estables/revisiones, costes/moneda y completitud histórica | Obtener aclaraciones contractuales; revisar ejemplos redactados de operaciones existentes solo con acceso autorizado; no crear operaciones de prueba |
| Visual NOT_REPRODUCED | Responsable del entorno local | Arranque de depuración Chrome y captura actual | Investigar en un entorno permitido; esta fase agotó su único intento sin cambiar seguridad ni cerrar sesiones personales |
| X03 Mutaciones DISABLED | Futuro alcance explícito del usuario | Todos los gates operativos y autorización separados | No activar nada al resolver lectura o datos |
| X05 CI remoto/publicación | Usuario, si lo solicita en otro alcance | Destino y autorización explícitos | Ninguna acción ahora |

Preflight real del proceso: 2026-09-10T19:24:54Z, exit 2; ETORO_API_KEY y
ETORO_USER_KEY ausentes, sin .env. Ninguna consulta de cuenta. Las suites también
ejercitan el caso negativo con credenciales retiradas; no equivalen a reintentos de
la configuración real. El conector solo aportó catálogo/OpenAPI.

La búsqueda pública de datos fue acotada a los proveedores ya auditados. No se
adquirieron servicios, créditos ni suscripciones. No hay archivo real validado ni
ORH/ORL/RVOL real calculado. Un histórico final real no es sintético por carecer de
recepción histórica: puede permitir aritmética exploratoria, pero no sortear el
gate observed del motor ni demostrar latencia. Sin shadow ni tarea futura.

Panel HTTP aprobado; Chrome salió 1 a las 19:33:13Z por depuración no iniciada.
Servidor de comprobación cerrado y token retirado. No usar captura del bootstrap
como verificación actual. Las guardas de mutación siguen cubiertas por tests con
transporte espía, incluidos permisos antiguos: ninguna solicitud de escritura
llega a la red. La consulta del bróker no está conectada al runner operativo.

Evidencia local ignorada: runtime/phase3 (A aislada, B/C suites, huellas de capas,
preflight, descarga fallida y navegador). Evidencia portable y matriz Git en
docs/VERIFICATION.md y docs/GIT_WORKFLOW.md. El commit documental posterior a C
no cambia software. Consultar `git log --format=fuller` y `git status --short`
para el historial y estado reales. Sin remotos, publicación o mutación de cuenta.

Criterio de parada alcanzado: capas preservadas, revisión contractual focalizada
agotada y recorridos externos posibles intentados. No abrir otra ronda de motores,
fixtures o interfaz para sustituir las dependencias anteriores.
