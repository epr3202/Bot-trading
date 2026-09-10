# Contratos de datos

Fuentes de verdad: `domain/models.py`, `data/importer.py`, `data/providers.py` y
`data/calendar.py`. `MarketDataProvider.load() -> DataBundle` está separado de cualquier
adaptador que envíe órdenes. `FixtureProvider` no tiene transporte ni credenciales.

## Barras e identidad

`Instrument` contiene symbol, exchange MIC, currency, asset_class, stable_id opcional y
broker_id opcional. Los símbolos SIMA/SIMB/SIMC son inventados y se identifican como
`synthetic:*`; nunca se asigna un ID eToro inventado. El importador rechaza símbolos
ambiguos entre mercados/divisas. Resolver identidad, acción/ADR/ETF y negociabilidad
Demo requiere evidencia separada del bróker.

Cada `Bar` inmutable tiene instrumento, OHLC y volume Decimal finitos, source,
interval_seconds=60, final, revision, event_time, received_at y available_at. La barra
etiquetada 09:30 representa [09:30,09:31). Todos los tiempos deben tener zona y se
normalizan a UTC. Una barra final no puede recibirse antes de su fin. available_at
no puede preceder received_at. Se rechazan OHLC incoherentes, precios no positivos,
volúmenes negativos y timestamps sin zona. Cero volumen es representable para calidad;
una ventana histórica de apertura de volumen cero invalida el RVOL.

Calendario XNYS de exchange-calendars fijado en uv.lock; rango admitido 2000–2035.
Las sesiones usan America/New_York; la presentación puede convertir a America/Bogota.
La apertura UTC cambia con DST. Los tests cubren 7/10 marzo 2025, Navidad y el cierre
de 13:00 NY del 28 noviembre 2025. Cierres extraordinarios futuros necesitan verificar
y actualizar el calendario; una versión instalada no prueba un calendario futuro.

## CSV/Parquet y manifiesto

`import_market_data(Path(datos), Path(manifiesto))` lee únicamente. No escribe ni
rellena raw. Se exige SHA-256 de los bytes exactos antes de parsear. CSV conserva los
valores como texto para conversión Decimal explícita; Parquet usa su esquema declarado.
Columnas mínimas: symbol, exchange, currency, asset_class, event_time, received_at,
available_at, open, high, low, close, volume, source, final. revision es opcional (0).

Manifiesto JSON validado por `DataManifest`: schema_version, source, synthetic,
volume_kind, adjustments, license, provenance, sha256, coverage_start, coverage_end,
rows, calendar, point_in_time_universe, availability_evidence, quality. Los tiempos de
cobertura son inicio mínimo y fin máximo, ambos inclusive como límites de cobertura
(las barras siguen siendo intervalos semiabiertos). Conteo, fuente y cobertura deben
coincidir. Licencia y disponibilidad son declaraciones del importador, no certificación.

Ejemplo de tipos: volume_kind admite synthetic_shares, consolidated_shares, venue_shares,
unknown; adjustments admite unadjusted, split_adjusted, unknown. ORB/RVOL v0.1 acepta
synthetic_shares o consolidated_shares, rechaza volumen parcial/desconocido y ajustes
desconocidos. No se compara una historia consolidada con sesión parcial de otro feed.
Datos split_adjusted requieren precios y volúmenes ajustados consistentemente por quien
produce el manifiesto; el importador no puede probar el tratamiento corporativo.

`quality_issues` marca SESSION_GAPS, DUPLICATE_OR_REVISION, OUT_OF_ORDER, LATE_REVISION,
INCOMPLETE_BAR, NON_SESSION_DATA y OUTSIDE_REGULAR_SESSION. No completa huecos. La
estrategia exige todas las barras regulares de las 20 sesiones previas; la primera
versión final recibida se conserva para decisiones y revision>0 no reescribe el pasado.
Cambios de datos/versiones requieren nuevo checksum y resultado, conservando raw.

No almacenar datos privados en Git. Los fixtures se generan por aritmética versionada
en código y un descriptor en tests/fixtures, no son datos del mercado. Sin universo
histórico punto-en-el-tiempo, el sesgo de supervivencia sigue siendo una limitación.

En fase 2 el manifiesto añade availability_kind (synthetic, observed,
historical_download, unknown), acquired_at y feed_id. Synthetic y synthetic_shares
deben coincidir. Licencia, procedencia y evidencia no pueden estar vacías; cobertura
requiere zona horaria y orden temporal. Una descarga histórica necesita acquired_at;
el importador rechaza received_at anterior a ese momento. No transforma automáticamente
el timestamp del evento en disponibilidad. Solo la declaración observed puede llegar
a decisiones reales v0.1, y aún requiere auditar su evidencia fuera del esquema.

stable_id/broker_id opcionales ahora sobreviven a CSV/Parquet; no se inventan cuando
faltan. Un símbolo idéntico con identidad distinta sigue siendo ambiguo. `data validate`
conserva los campos del manifiesto y añade audit con sesiones, retrasos medidos,
calidad, volumen, aptitud y bloqueos. Aprobar el esquema no aprueba los datos externos.

`uv run python scripts/verify_import.py` crea una copia sintética nueva: 8.190 barras,
20 sesiones previas y una evaluación de SIMA. Comprueba CSV → manifiesto → importador →
CLI validate → CLI backtest sin cambiar reglas. Calcula ORH/ORL/RVOL independientemente
desde CSV y perturba barras futuras. Guarda configuración y evidencia en runtime;
informes en reports/runs/synthetic-import. No es una muestra real ni shadow observado.
Los informes rechazan mezclar manifiestos synthetic=true/false en un mismo directorio.
