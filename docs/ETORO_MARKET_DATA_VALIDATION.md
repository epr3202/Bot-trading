# Validación de Market Data eToro — 2026-09-14

**Market Data para ORB/RVOL: BLOCKED — ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL.**
Acceso a Market Data e identidad del instrumento: VERIFIED mediante siete GET reales
del conector eToro. No confundir esta procedencia con ejecución HTTP desde Bot 3.
El hito previo DEMO_READ_VERIFIED desde Bot 3 se conserva tal como lo comunicó el
usuario; no se repitieron identidad, permisos ni portafolio. El proceso del agente
no pudo iniciar su consulta de instrumentos con el contexto local disponible;
se registró esa limitación sin invalidar el hito ni buscar claves en otros sitios.

Se preservaron HEAD, diff, índice y huellas previas en
`runtime/market-audit-20260914T164913/`. No se modificó ORB_RVOL_v0.1 ni su motor.
Estado mantenido: entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED, writes=0.

## Contrato y lecturas observadas

Catálogo oficial MCP: API **v1.376.0**, catálogo **1.20.0**. Se consultaron los 11
endpoints de Market Data y contratos completos de instruments v2, rates v2,
candles v1 y exchanges v1. No se usó overview porque incluye elegibilidad de cuenta.
El catálogo indica cuota compartida 120/60s; se mantuvo el límite más conservador
del transporte existente. Ninguna consulta recibió 429 ni necesitó reintentos.

| GET de Market Data | Resultado observado |
|---|---|
| `/api/v2/market-data/instruments?symbols=AAPL&type=Stocks&pageSize=100` | HTTP 200; AAPL, Apple, Stocks, instrumentId=1001, exchangeId=4; hasNext=false |
| `/api/v1/market-data/exchanges?exchangeIds=4` | HTTP 200; Nasdaq |
| `/api/v2/market-data/rates?instrumentIds=1001` | HTTP 200; bid=334,84, ask=334,87, quoteType=realtime |
| `/api/v1/market-data/instruments/1001/history/candles/asc/OneMinute/1000` | HTTP 200; 1.000 velas |
| Misma ruta con `desc/OneMinute/1000` | HTTP 200; mismos timestamps en orden inverso, no otra página |
| Misma ruta con `asc/OneDay/30` | HTTP 200; 30 etiquetas diarias, 2026-08-03 a 2026-09-14 |
| Misma ruta con `desc/OneMinute/10` | HTTP 200; segunda observación acotada, ocho timestamps solapados |

Todos los cuerpos se recibieron sin truncar. UUID de solicitud, intervalo de llamada,
recepción y ruta están en acquisition.json. La hora exacta de recepción de la primera
consulta de instrumentos no se registró: queda null. No se reconstruyó retrospectivamente.
Las recepciones siguientes son finalización de herramienta, no latencia HTTP del bot.

La cotización lleva `date=2026-09-14T16:49:59.827`, sin offset. El contrato describe
ese campo como UTC: únicamente el análisis lo interpreta así, conservando el texto
original y la discrepancia. Recepción de herramienta: 16:50:42.903Z; diferencia
43,076s. `realtime` no demuestra frescura menor al gate de 3s. El parser actual del
bot rechaza ese payload con QUOTE_SCHEMA_INVALID por falta de zona explícita;
se reprodujo con los bytes reales en transporte local, sin nueva solicitud externa.
No se cambió el parser ni el umbral para obtener una aprobación.

## Sesión, continuidad y volumen

La ventana primaria va de 2026-09-11 19:51Z a 2026-09-14 16:50Z.
Las 1.000 velas tienen OHLC coherente, valores finitos, timestamps UTC alineados
al minuto y cero timestamps duplicados. Se observaron 790 fuera de sesión regular,
209 minutos regulares cuyo intervalo terminó y una vela regular aún en formación.
La regularidad se comprueba con America/New_York y el calendario fijado en uv.lock;
en estas fechas 09:30–16:00 NY corresponde a 13:30–20:00 UTC.

| Sesión NY | Minutos completos observados | Cobertura |
|---|---:|---|
| 2026-09-11 | 9/390 | Solo 15:51–15:59 NY; faltan 381 minutos anteriores a la ventana |
| 2026-09-14 | 200/390 | 09:30–12:49 NY; ningún hueco entre los minutos ya transcurridos; sesión aún abierta |

No se cuentan minutos futuros como pérdida del feed. No hay huecos dentro de la
ventana regular cubierta, pero ninguna sesión completa está disponible. La vela
16:50Z cambió entre capturas; no se interpreta una vela en formación como revisión
tardía de una vela final. No existe evidencia observada de garantía de finalidad.

El contrato de `volume` dice únicamente «Trading volume during the candle period».
No acredita acciones, contratos, ticks, dinero, venues, consolidación ni ajustes.
Empíricamente: 952 valores positivos y 48 ceros; todos los valores son enteros
representados como números decimales. Mínimo 0, máximo 476.139, suma 13.987.876.
La suma coincide con el volumen agregado del grupo; los 209 minutos regulares
completados tienen volumen positivo. Estas propiedades prueban coherencia aritmética,
**no identifican las unidades ni la cobertura del campo**. Se mantiene volume_kind=unknown.
No se cotejó contra otro feed ni se atribuyó consolidación por similitud numérica.

## Historia y cálculo independiente

`candlesCount` tiene máximo 1000; direction es orden, no paginación. El contrato no
admite start/end/date/cursor. La doble captura lo confirma para esta ventana; no
se probaron parámetros inventados ni counts fuera de contrato. Para la evaluación
del 14/09 se necesitan las 20 sesiones previas del 14/08 al 11/09, excluyendo festivos,
más evaluación: **8.190 minutos regulares**. Se obtuvieron **0/20 sesiones previas
completas y 0/20 ventanas previas de apertura**. Los 30 datos diarios no reconstruyen
los primeros cinco minutos y no son sustituto para el denominador RVOL.

El cálculo independiente usa Decimal sobre los cuerpos guardados, sin invocar el
motor para obtener estas cifras. Apertura del 14/09, [09:30,09:35) NY:

| Minuto NY | High | Low | Volume, unidades desconocidas |
|---|---:|---:|---:|
| 09:30 | 334,54 | 333,87 | 363.738 |
| 09:31 | 334,06 | 333,16 | 107.026 |
| 09:32 | 333,43 | 331,72 | 476.139 |
| 09:33 | 333,10 | 331,98 | 109.244 |
| 09:34 | 333,18 | 332,56 | 124.897 |

ORH=max(high)=**334,54**; ORL=min(low)=**331,72**; suma de volume=**1.181.044**.
RVOL=1.181.044/media de 20 aperturas anteriores: **no calculable**, denominador ausente
y semántica de volumen desconocida. No se usa volumen diario ni una ventana reducida.

Comparación contra el motor existente mediante CSV y manifiesto reales:
importación aprobada; ORBStrategy rechaza con OBSERVED_AVAILABILITY_REQUIRED,
selección vacía y cero señales. La comparación numérica ORH/ORL/RVOL con una salida
del motor queda BLOCKED porque no produce candidato válido. No se afirmó paridad
numérica ni se falsearon synthetic, observed, final, ajustes o volumen para obtenerla.
Todas las filas derivadas conservan recepción de descarga y final=false por ausencia
de garantía de finalidad. Esto limita decisiones, no convierte los precios en sintéticos.

## Artefactos y reproducción

Datos privados de investigación fuera de Git, sin redistribución:

- Raw inmutable: `data/raw/etoro-market-20260914T164913/`, siete cuerpos y acquisition.json.
- Resultado: `runtime/market-audit-20260914T164913/final-analysis/` contiene audit.json,
  manifest.json, regular-minutes.csv e import-manifest.json.
- manifest.json enumera origen, instrumento, rutas, granularidad, zona, timestamps,
  limitaciones y SHA-256 de todos los datos raw y derivados. Es un manifiesto de
  auditoría; import-manifest.json usa el esquema del importador existente.
- SHA-256 candles-asc.json: `0e453e072905390e7132e34e8614e61c99cff92b9a6dac7e51d33c2e05221290`.
- SHA-256 regular-minutes.csv: `2a869259e2d47376ef466ff5828985b430091e6e5e14396f981d33607fbcae2f`.

Los hashes corresponden al cuerpo textual MCP en UTF-8 con LF terminal, no a bytes
HTTP comprimidos. Las revisiones se conservan en archivos separados. Ningún raw
se reescribe; se confirmó igualdad de huellas antes/después del análisis.

Repetir solo el análisis local eligiendo una carpeta de salida nueva:

```powershell
.\scripts\uv.ps1 run --frozen python scripts/audit_etoro_market_data.py --input data/raw/etoro-market-20260914T164913 --output runtime/market-audit-repeat-01
```

**Shadow: NOT_STARTED_DATA_QUALITY_BLOCKED.** Cero señales de mercado operativas,
cero órdenes externas. La ejecución local del motor con rechazo no es shadow.
Bloqueos restantes: semántica/consolidación del volumen, histórico de minutos,
ajustes, disponibilidad/finalidad, frescura y formato temporal de cotizaciones.
La interfaz MarketDataProvider y la importación de otro proveedor se conservan;
no se adquirió servicio ni se cambió la estrategia para acomodar a eToro.

Fuentes: contratos completos del catálogo oficial conservados en runtime; referencias
[candles](https://api-portal.etoro.com/api-reference/market-data/get-instrument-candle-history),
[rates](https://api-portal.etoro.com/api-reference/market-data/retrieve-bidask-rates-for-one-or-more-instruments),
[horarios y festivos Nasdaq 2026](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule).
Las páginas eToro no fueron accesibles mediante navegador en esta fase; la evidencia
contractual usada es el catálogo MCP, no contenido supuesto de esas páginas.
