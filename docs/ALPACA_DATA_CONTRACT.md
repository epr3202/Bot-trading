# Alpaca histórico — contrato y auditoría

Estado observado el 2026-09-14: **ALPACA_DATA_INSUFFICIENT_FOR_RVOL**.
Motivo: ALPACA_CREDENTIALS_UNAVAILABLE en el proceso del agente, antes de cualquier
petición. No se obtuvieron barras; feed efectivo desconocido, no se ha comprobado
entitlement y no se declara necesario pagar una suscripción. El manifiesto saneado
versionado es [alpaca-historical-manifest.json](alpaca-historical-manifest.json).
ORH, ORL, RVOL y comparación real: NOT_RUN. Los números de tests son fabricados.

## Arquitectura y uso

`data/alpaca_http.py` permite únicamente GET a
`https://data.alpaca.markets/v2/stocks/bars`; no admite URL/path/método arbitrarios.
Usa ALPACA_API_KEY y ALPACA_API_SECRET, enviados solo como APCA-API-KEY-ID y
APCA-API-SECRET-KEY. Nunca usa claves eToro ni carga .env automáticamente.
TLS obligatorio; admite ALPACA_CA_BUNDLE, certificado local corporativo o
REQUESTS_CA_BUNDLE y proxy del proceso; transportes inyectados no heredan proxy.
No hay SDK, rutas de cuenta, trading, WebSocket ni fallback de feed.

`data/alpaca.py::AlpacaHistoricalProvider.load()` lee capturas verificadas y devuelve
el DataBundle del MarketDataProvider existente. No tiene red. La estrategia,
RiskEngine y ExecutionEngine no dependen de Alpaca. Fixture permanece predeterminado,
eToro permanece como bróker Demo y sus datos como audit-only. No se cambió DataConfig:
el CSV/manifiesto generado también se consume mediante el proveedor `import` existente.

Captura explícita desde un proceso que ya tenga las variables dedicadas configuradas:

```powershell
.\scripts\uv.ps1 run --frozen python scripts/audit_alpaca_history.py --capture --feed sip --target 2026-09-11
```

No incluir claves en el comando, Git, informes o mensajes. El programa imprime la
ruta de evidencia. Sin `--target` elige la última sesión cuyo cierre tiene al menos
15 minutos de antigüedad. Cada captura crea un directorio nuevo bajo `data/raw/alpaca`
y cada análisis uno nuevo bajo `runtime/alpaca-audits`; nunca reemplaza una captura.
Para repetir análisis local: `--input RUTA_DE_CAPTURA`, sin `--capture`. El feed,
la sesión y los parámetros efectivos se toman de la captura y se verifican contra
el contrato. No se transforman usando opciones de CLI del nuevo proceso.
`--feed iex` permite integración expresamente solicitada; no se usa en esta captura.
Nunca produce un hito SIP ni valida RVOL consolidado.

## Consulta y semántica documental

Primera consulta prevista: AAPL, 1Min, feed=sip, adjustment=split, currency=USD,
sort=asc, asof=2026-09-11. Incluye las veinte sesiones previas desde 2026-08-13 y la
sesión objetivo 2026-09-11. Inicio 13:30Z del primer día; end=19:59Z del último,
pues el límite final del API es inclusivo. Limit=10000 por página; siempre se sigue
next_page_token aunque una página tenga menos filas. Máximo local 50 páginas.
El parámetro feed se fija en cada página; no se omite ni cambia entre reintentos.

El contrato identifica sip como fuente estadounidense consolidada e iex como un
solo mercado. Sin suscripción realtime, el histórico SIP puede consultarse con end
de al menos 15 minutos de antigüedad. Esto es capacidad documentada, no prueba de
acceso de esta cuenta. Respuesta HTTP exitosa con feed explícito constituye la
identidad contractual del feed; el cuerpo habitual **no repite el nombre del feed**.
El manifiesto distingue ese fundamento de una atestación independiente. Si hay
un campo feed contradictorio se bloquea; ninguna página IEX puede mezclarse con SIP.
[Parámetros de barras](https://docs.alpaca.markets/us/reference/stockbars),
[acceso y feeds](https://docs.alpaca.markets/us/docs/market-data-faq).

Las barras agregan operaciones elegibles: timestamp de inicio del intervalo,
volume suma de tamaños en acciones, n cuenta de operaciones elegibles para volumen.
Las condiciones de negociación pueden actualizar volumen sin actualizar precios;
el VWAP usa un subconjunto compatible con sus reglas. No se infiere que toda
operación publicada contribuya a todos los campos. No se emite barra cuando faltan
operaciones/precios elegibles. `split` ajusta precios y volumen de forma consistente;
no ajustamos nuevamente. IEX conserva unidades de acciones pero cobertura de un
venue; nunca se etiqueta como volumen consolidado.
[Agregación oficial](https://docs.alpaca.markets/us/docs/market-data-faq).

## Esquema y comprobaciones

| Alpaca | Contrato interno / evidencia |
|---|---|
| bars.AAPL[].t | event_time UTC, con zona explícita, alineado al minuto; [t,t+1m) |
| o / h / l / c | open / high / low / close Decimal; positivos, finitos y OHLC coherente |
| v | volume Decimal no negativo; SIP consolidated_shares, IEX venue_shares |
| n | Entero no negativo si aparece; se conserva raw y se registra presencia |
| vw | Decimal positivo finito si aparece; raw y presencia; no es señal |
| Recepción HTTP de página | received_at=available_at real de descarga; nunca t+200ms |
| feed y adjustment de consulta | feed_id=alpaca:sip:1Min:split o alpaca:iex:1Min:split |

availability_class=HISTORICAL_DOWNLOAD; DataManifest.availability_kind=
historical_download. `final=true` identifica intervalo histórico cerrado en la
instantánea, no finalidad irreversible ni primera versión observada. No prueba
disponibilidad a la apertura. Las correcciones futuras requieren capturas nuevas.

Se filtra por el calendario XNYS ya utilizado por el sistema, expresado en
America/New_York: apertura <= t < cierre real de la sesión. Cierres tempranos usan
210 minutos cuando corresponde; no se impone 390. Se enumeran las 21 sesiones y
todos los timestamps ausentes. Un hueco se marca UNKNOWN_NO_HALT_EVIDENCE: no se
atribuye automáticamente a halt, fallo del feed o ausencia de trades elegibles.
No se rellena. La evidencia actual no contiene barras ni halts que contrastar.

Duplicados exactos se deduplican preservando todas las páginas raw; versiones
distintas del mismo minuto bloquean. Timestamps fuera de orden, símbolo distinto,
intervalos fuera de consulta, feed mixto, checksum distinto o cursor incompleto
bloquean. No se usa una página parcial como histórico completo.

401 no se reintenta; 403 genérico no prueba entitlement. Solo la negativa explícita
de suscripción SIP produce ALPACA_SIP_ENTITLEMENT_REQUIRED. 429 respeta Retry-After
o X-RateLimit-Reset, con tres intentos máximo; espera superior a 60s/indeterminada
bloquea indicando espera pendiente. Quota restante cero también aplaza la página
siguiente. Redirecciones, errores de transporte y otros HTTP fallan sin fallback.
Los cuerpos de error no se imprimen ni persisten; razones públicas son estáticas.

## Cálculo y comparación

Solo con 21 sesiones completas se calcula fuera del motor sobre claves raw usando
Fraction: cinco volúmenes de cada apertura, media de las veinte previas excluyendo
hoy, RVOL del objetivo, máximo high y mínimo low. El motor calcula sobre Bar/Decimal.
Tolerancia absoluta **1e-12**, relativa **0** para ORH, ORL, RVOL y ambos volúmenes.

Se extrajo la aritmética ya existente a ORBStrategy.opening_metrics; process_session
usa esa misma función. No se modificaron fórmula, filtros, warmup, orden de
rechazos, ranking, riesgo, TTL ni ejecución. La comparación histórica llama ese
componente numérico y también ejecuta process_session: datos reales descargados
siguen rechazados con OBSERVED_AVAILABILITY_REQUIRED. No se falsea observed para
forzar señales. La coincidencia numérica no certifica replay causal ni rentabilidad.
Una regresión altera deliberadamente el resultado del motor y exige MISMATCH.

Estados: A solo si SIP contractual, 21 sesiones y métricas coincidentes con captura
real; B solo ante negativa explícita de acceso SIP; C si faltan datos o propiedades.
Capturas mock se etiquetan CONTRACT_TEST, nunca A. IEX tiene su estado insuficiente
específico. No se inicia shadow ni se arma el bróker en ningún resultado.

## Persistencia y formato del manifiesto

`alpaca-capture-v1` (local): origin, endpoint, method, provider, target, params,
feed_requested/effective, acquisition_class, availability_class, timestamps y pages.
Cada página registra file, SHA-256, parámetros exactos, feed y received_at. Los
cursores se conservan localmente para reproducir la cadena. Estado COMPLETE exige
terminación explícita con next_page_token=null. INCOMPLETE nunca se importa.

`alpaca-audit-v1` (saneable): consulta sin credenciales/cursores, feed y fundamento,
sesiones/conteos, semántica, hashes de páginas/captura/CSV/informe, métricas,
tolerancia, limitaciones y guardas. `alpaca-attempt-v1` registra intentos bloqueados
sin respuesta: feed_effective=null, raw_sha256 vacío, métricas null y motivo exacto.
No confundir un hash de result.json con un checksum de datos de mercado inexistentes.
Estos son los esquemas versionados; el código valida identidad y consistencia
cruzada antes de construir el DataManifest existente. No se amplió ese contrato.

Solo código, tests, contrato y manifiesto saneado se versionan. Raw, CSV y reportes
locales quedan ignorados por Git. No se ha autorizado redistribuir un dataset ni
comprado plan. eToro DEMO_READ_VERIFIED se conserva; entries_armed=false,
external_mutations=DISABLED, order_submission_enabled=false, Demo Write NOT_TESTED.
