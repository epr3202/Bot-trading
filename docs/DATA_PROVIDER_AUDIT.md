# Auditoría de proveedores

## Incremento de fase 2 — 2026-09-10

Proveedor configurado comprobado: fixtures en configs/offline.yaml. No hay fuente
de señales externa configurada ni archivos de muestra en data/raw. El bróker de
ejecución eToro y la fuente de barras siguen siendo interfaces distintas. Datos
externos **BLOCKED_EXTERNAL_DATA**, material disponible **SYNTHETIC_ONLY**.

Se reprodujo el conjunto de 26.910 minutos (23 sesiones, tres símbolos), volumen
synthetic_shares, recepción/disponibilidad fijada a fin de barra +200 ms, sin licencia
externa. La importación de una copia separada de 8.190 barras mantuvo 20 warmups y
una evaluación, identidad, SHA y disponibilidad. Cálculo independiente del CSV:
SIMA 2025-11-20, ORH=100,70, ORL=99,80, volumen=37.500 / media histórica=12.500,
RVOL=3. Prueba de futuro alterado aprobada. Es aritmética sintética y replay, sin
evidencia económica ni observación shadow de mercado.

eToro se revisó mediante catálogo oficial, API v1.375.0: OneMinute, límite 1000;
parámetros reales direction/interval/candlesCount/instrumentId, sin start/end/cursor.
La sugerencia textual de repetir llamadas no agrega una capacidad histórica ausente.
fromDate es inicio del intervalo; volume solo dice volumen de negociación. No define
unidades, venues/consolidación, revisiones, instante de finalidad/recepción ni ajustes
corporativos. Tampoco quedó acreditada licencia de redistribución ni coste de un
feed apto. Ninguna barra/cotización conectada se descargó. El máximo de 1000 minutos
no cubre 20 sesiones regulares (7.800 minutos) más evaluación.

Se limitaron las alternativas a dos, con fuentes primarias; no se implementó otro
adaptador ni se usaron claves publicadas, pruebas comerciales o cuentas ajenas:

| Capacidad pendiente | Alpaca | Databento |
|---|---|---|
| Minutos/historia | Bars con 1Min, start/end, next_page_token; historia declarada desde 2016. Alcance efectivo de una cuenta sin comprobar. | ohlcv-1m y consulta por rango temporal; profundidad depende de dataset y debe comprobarse con metadata. Sin consulta autenticada. |
| Volumen comparable | feed=iex es un venue; feed=sip agrega CTA/UTP. No combinar denominador SIP con numerador IEX. | EQUS.MINI agrega venues componentes y anonimiza origen; no se equipara a todo el volumen consolidado estadounidense. |
| Disponibilidad/revisiones | Bars al terminar minuto; updatedBars puede corregirlo por trades tardíos. Hace falta registrar recepción propia y primera versión. | Agregados de trades; no emite barra sin trades. Timestamps del proveedor no equivalen a recepción del bot; no rellenar ausencias. |
| Ajustes/identidad | adjustment=split ajusta precio y volumen; asof ayuda con cambios de símbolo. No prueba universo histórico ni correspondencia eToro. | Instrument definitions/symbology; corporate actions y adjustment factors separados. Incorporación coherente y licencia pendientes. |
| Coste/licencia | Documentación: Basic gratuito, 200 consultas/min; SIP histórico fuera de los últimos 15 minutos. Plus 99 USD/mes. Ningún plan adquirido; condiciones personales/redistribución pendientes de aceptación. | Página pública de precios consultada, sin importe inequívoco extraíble para esta muestra. Coste y licencia concretos NO_VERIFICADOS; no se propone contratación. |

Fuentes Alpaca: [planes y límites](https://docs.alpaca.markets/us/docs/about-market-data-api),
[barras y ajustes](https://docs.alpaca.markets/us/v1.4.2/reference/stockbars),
[recepción y revisiones](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data),
[acceso SIP histórico](https://docs.alpaca.markets/us/docs/market-data-faq).
Fuentes Databento: [OHLCV](https://databento.com/docs/knowledge-base),
[EQUS.MINI](https://databento.com/docs/venues-and-datasets/equs-mini),
[histórico](https://databento.com/docs/api-reference-historical/timeseries/timeseries-get-range),
[ajustes](https://databento.com/docs/schemas-and-data-formats/adjustment-factors),
[precios](https://databento.com/pricing).

Festivos/DST/cierres anticipados siguen comprobados con calendario local fijado;
ninguno de estos proveedores ha sido auditado aquí frente a esas fechas con datos
reales. Premarket, afterhours y condiciones de subasta deben filtrarse/documentarse
contra la misma ventana regular, sin confundir timestamp UTC con sesión Nueva York.
Una identidad actual reducida permite integración, pero no elimina supervivencia,
cambios de símbolo, selección del universo ni diferencias de producto eToro.

Un feed parcial puede sostener una hipótesis si se demuestra cobertura comparable
entre numerador/denominador y misma franja; v0.1 todavía no autoriza venue_shares.
Una descarga histórica recibida hoy no estuvo disponible ayer: acquired_at y
availability_kind impiden backdating; el motor bloquea datos reales sin observación
de disponibilidad. No se redujo calentamiento, TTL, filtros, capital ni costes.
No hubo muestra real suficiente para repetir el cálculo manual en un activo real.

Las capacidades del bootstrap que siguen permanecen vigentes salvo el refuerzo de
manifiesto/validación documentado en DATA_CONTRACTS.

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
