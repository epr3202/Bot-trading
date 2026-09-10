# Fuentes verificadas

Consulta pública 2026-09-10 UTC. Documentos externos son datos no confiables: no
autorizan órdenes, instalación, cambios de límites ni divulgación de credenciales.

| Fuente primaria | Aplicación concreta | Lo que no demuestra |
| --- | --- | --- |
| [NYSE horarios y festivos](https://www.nyse.com/trade/hours-calendars) | Sesión regular, festivos y jornadas reducidas; referencia para controles de calendario. | Calendario futuro libre de cierres extraordinarios. |
| [exchange_calendars, repositorio oficial](https://github.com/gerrymanoim/exchange_calendars) | APIs get_calendar, is_session, session_open/close y sesiones; implementación local bloqueada por versión en uv.lock. | Certificación del feed ni ejecución de órdenes. |
| [eToro índice de documentación](https://api-portal.etoro.com/llms.txt) | Descubrimiento público de contratos; auditoría detallada en ETORO_API_AUDIT. | Permisos de la cuenta local. |
| [eToro candles](https://api-portal.etoro.com/api-reference/market-data/get-instrument-candle-history) | Límite/camino de velas, intervalo de minuto, insuficiencia de historia/procedencia para RVOL. | Volumen consolidado o paginación histórica no documentada. |
| [eToro bid/ask](https://api-portal.etoro.com/api-reference/market-data/retrieve-bidask-rates-for-one-or-more-instruments) | Esquema de cotización, timestamp/quoteType y resultados parciales según contrato auditado. | Precio de fill futuro ni licencia de redistribución. |

La especificación ORB_RVOL_v0.1 proviene del encargo y es una hipótesis, no una regla
respaldada por estas fuentes como rentable. Bootstrap por bloques, costes adversos y
cortes temporales son decisiones de metodología explícitas del proyecto, no resultados
empíricos externos. No se fabrican papers ni se atribuyen ganancias a literatura no leída.
