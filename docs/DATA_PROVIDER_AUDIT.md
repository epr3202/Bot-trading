# Auditoría de proveedores

Estado: SYNTHETIC_ONLY; investigación RESEARCH_BLOCKED_DATA. Fecha de consulta pública:
2026-09-10 UTC. Ninguna lectura de cuenta, suscripción ni escritura externa por este módulo.

| Fuente | Implementación y capacidad | Evidencia/limitación |
| --- | --- | --- |
| FixtureProvider v1 | 26.910 barras de un minuto; 3 símbolos sintéticos; 23 sesiones completas | 20 warmups + 20/21/24 noviembre 2025. Volumen synthetic_shares. Sin red. |
| CSV/Parquet local | Importación, esquema Decimal/timestamps, checksum, cobertura y calidad | El usuario aporta licencia, volumen y disponibilidad verificables; no hay históricos reales incorporados. |
| eToro instrumentos | Adaptador documentado en brokers/market_data.py | v2 admite paginación real pageToken. IDs se resuelven; fixture IDs no sirven. |
| eToro cotizaciones | Bid/ask, timestamp y quoteType documentados; resultados parciales posibles | Retraso realtime/delayed debe examinarse; no equivale a volumen negociado consolidado. |
| eToro candles | Endpoint documentado OneMinute, hasta 1000 velas | No fecha inicial/cursor documentados. Repetir peticiones no consigue veinte sesiones. Semántica consolidada del volumen no demostrada. |

Contrato eToro inspeccionado por agente de bróker: versión 1.375.0, instantánea local
`docs/etoro_spec_snapshot.json`. El campo volume descrito genéricamente como volumen
de negociación y ejemplos cero no prueban consolidación ni idoneidad para RVOL/VWAP.
`EtoroMarketDataProvider.load()` debe devolver el bloqueo de volumen/cobertura en vez
de crear un DataBundle válido con precios o ticks como acciones negociadas.

Fuentes oficiales: [velas eToro](https://api-portal.etoro.com/api-reference/market-data/get-instrument-candle-history),
[bid/ask eToro](https://api-portal.etoro.com/api-reference/market-data/retrieve-bidask-rates-for-one-or-more-instruments),
[índice oficial](https://api-portal.etoro.com/llms.txt). Ver ETORO_API_AUDIT para autenticación,
guardas y discrepancias de cuotas; aquí no se certifican llamadas conectadas.

Una fuente externa adecuada debe aportar acciones estadounidenses comunes, minutos
regulares completos, al menos veinte sesiones previas por fecha investigada, volumen
consolidado de acciones y significado comprobable, ventanas históricas con fecha/cursor,
tratamiento coherente de splits, zonas horarias y recepción/latencia utilizable. También
necesita cobertura fuera de muestra y universo punto-en-el-tiempo para evaluar sesgos.
MarketDataProvider es el punto de extensión; no se incorporan adaptadores vacíos ni se
adquieren servicios. La compatibilidad entre fuente de señales y precios ejecutables
eToro requiere medir diferencias, spread y retraso antes de activar Demo.
