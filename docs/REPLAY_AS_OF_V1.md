# Contrato temporal replay_as_of_v1

Autorización explícita del usuario, 2026-09-15: separar procedencia del dataset y
visibilidad en el reloj lógico de investigación. Este contrato vive exclusivamente
en `backtesting/replay.py`; no modifica Strategy 1, su YAML, snapshot o guardas.

## Procedencia y relojes

`historical_download` identifica la procedencia original. Las capturas A2, sus
hashes y las barras originales conservan received_at/available_at de la descarga.
Cada ReplayRecord conserva la Bar original y una disponibilidad lógica separada.

Prioridad por registro:

1. Timestamp explícito de publicación/disponibilidad, si está documentado y
   mapeado para ese registro. Un valor inválido bloquea; nunca cae al cierre.
2. Sin ese timestamp, cierre efectivo de barra únicamente con semántica documentada.
3. Sin ambas evidencias: `REPLAY_AVAILABILITY_CONTRACT_MISSING`.

A2 tiene exactamente campos t/o/h/l/c/v/n/vw, sin timestamp de publicación por
registro. `received_at` de capture.json corresponde a recepción HTTP de una página
histórica, no a publicación contemporánea de cada barra. La documentación local
MASSIVE_DATA_CONTRACT y la [especificación oficial Custom Bars](https://massive.com/docs/rest/stocks/aggregates/custom-bars)
definen t como inicio Unix en milisegundos. La solicitud A2 fija range/1/minute;
por ello el cierre efectivo es `UTC(t) + 60 segundos`, incluido el último minuto
de sesión. Semántica identificada: `unix_ms_interval_start_plus_60s`.

Este cierre es la disponibilidad **modelada autorizada para replay**, no una
afirmación de publicación real del proveedor en ese instante. El histórico es una
instantánea split-adjusted y puede incorporar correcciones; no se certifica su
contenido tal como habría sido publicado en vivo. No se simula ni infiere latencia
HTTP, entitlement realtime o universo punto-en-el-tiempo.

## Boundary y Strategy 1

`ReplayAsOf.view(replay_clock)` devuelve únicamente registros con
`available_at <= replay_clock`. Los anteriores a esa condición son invisibles.
El reloj debe tener zona y no puede retroceder. Eventos con igual disponibilidad
se entregan como un lote atómico, ordenado por available_at, event_time y símbolo.
Duplicados, identidades ambiguas, revisiones y barras no finales bloquean;
no se elige silenciosamente una versión del registro.

Solo al revelar un registro se construye su Bar de vista: available_at es lógico
y received_at significa entrega lógica en ese instante. Ambos son distintos de
la recepción original, preservada en ReplayRecord y availability.jsonl. No se
mutan objetos fuente. Un snapshot ya entregado no cambia al avanzar el reloj.
El manifiesto de la vista declara observed y mantiene historical_download en
provenance; el manifiesto fuente y el reporte final conservan historical_download.
`observed` aquí significa visible en replay, nunca una captura realtime verificada.

Strategy 1 sigue ejecutando OBSERVED_AVAILABILITY_REQUIRED sin modificaciones.
Como su API es por sesión, el boundary la llama en el cutoff y en cada lote de
disponibilidad de la ventana de entradas mientras existan candidatos pendientes.
La selección inicial queda fija. Se conserva la primera señal o rechazo terminal
de cada símbolo; un benchmark posterior no reabre una candidata RS rechazada.
Una señal retroactiva o una selección cambiante provoca error visible.

## Motor de fills

El motor existente conserva `minute-next-open-v1`, riesgo, costes, reservas,
TTL, unicidad y salidas. El simulador de ejecución tiene acceso a precios para
modelar fills al siguiente open; esa capacidad interna no entrega OHLC de barras
futuras a Strategy 1. Una orden solo se llena en un open estrictamente posterior
a su envío. Los valores close/low para valoración/stops se procesan a la
disponibilidad lógica del registro, también cuando una publicación explícita se
retrasa. Los supuestos de ejecución por barras siguen siendo aproximaciones.
La llamada sin boundary conserva su rechazo original del histórico.

## Persistencia e identidad A4

`scripts/run_a4.py run --output <directorio-nuevo>` valida primero los SHA-256
aprobados de A2/A3, configuración/fuentes congeladas, capturas/páginas, calidad,
identidades y alineación AAPL/SPY/QQQ. No hay entrada alternativa de fixtures,
descarga ni selección automática de otro dataset. Un esquema temporal nuevo
requiere mapeo revisado; no se ignoran campos desconocidos.

Se reutilizan BacktestResult, save_report y append_experiment. Cada directorio
contiene JSON completo del run, HTML existente, experiments.jsonl y
availability.jsonl. El último registra símbolo, evento, recepción/disponibilidad
originales, disponibilidad lógica, fundamento y procedencia por registro.
Su SHA-256 se guarda dentro de run_metadata del resultado.

El manifiesto guarda por separado procedencia, referencia/hash A2, política,
semántica temporal, zonas UTC/NY, calendario, Strategy 1/configuración completa,
snapshot A3, parámetros del motor, rango/sesiones y símbolos/benchmarks. Guarda
commit base y SHA-256 del árbol efectivo, archivos y lock; el commit solo no
identifica los cambios A2/A3 sin commit. Python 3.12.12 obligatorio, Decimal
local de precisión 28 y configuración/semilla del motor explícitas.

La comparación exige dos archivos distintos, verifica SHA-256 del registro de
disponibilidad y compara todo el resultado funcional, no solo agregados. Únicas
exclusiones: run_metadata.execution.started_at y finished_at. Ni run_id ni tiempos
de señales/operaciones ni su orden se excluyen. El run_id funcional coincide para
inputs idénticos; los directorios separan invocaciones sin sobrescribir resultados.

La ausencia de operaciones puede ser un resultado legítimo si Strategy 1 evaluó
los datos y rechazó por sus reglas congeladas. Un rechazo de disponibilidad o
entrada incorrecta nunca se considera éxito de A4.

## Validación

Pruebas de contrato con datos fabricados: `tests/test_replay_as_of.py`.
Cubren límites temporales inclusivos, prioridad de publicación, contrato ausente,
mutación futura, orden, observación solo dentro del boundary, fuentes originales,
rechazo terminal RS, determinismo con trades no vacíos, identidad y persistencia.
Esas pruebas no son evidencia de adquisición o backtest de mercado A4.
La evidencia real, comandos y resultados se registran en A4_READINESS y VERIFICATION.
