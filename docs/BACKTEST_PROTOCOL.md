# Protocolo de investigación

## A4 — autorización temporal vigente, 2026-09-15

Se aprueba replay_as_of_v1: historical_download permanece como procedencia; observed
significa visibilidad en el reloj lógico solo dentro del boundary. Publicación
explícita tiene prioridad; A2 carece de ella por barra y usa cierre efectivo
documentado t+60s. No se altera Strategy 1 ni OBSERVED_AVAILABILITY_REQUIRED.
Recibos originales preservados y vistas filtradas available_at <= replay_clock.

Este contrato sustituye la prohibición histórica inferior para el replay A4
aprobado, sin habilitar rutas operativas ni alterar la carga histórica normal.
Cero operaciones por RVOL insuficiente tras evaluación válida puede ser un resultado
reproducible; cero operaciones por rechazo de disponibilidad sigue sin aprobar A4.
Contrato, pruebas y límites: [REPLAY_AS_OF_V1](REPLAY_AS_OF_V1.md).

## Restricción de esta fase — 2026-09-14

Baseline real NOT_STARTED por ALPACA_CREDENTIALS_UNAVAILABLE. Primero deben pasar
AAPL/SIP/21, paridad independiente y calidad; solo después se amplía al universo
propuesto de diez símbolos y al menos 60 sesiones completas. No se ejecuta el
comparador de variantes `controlled_comparison` en esta fase.

Se mantienen fijos opening_range_minutes=5, warmup_sessions=20,
min_previous_close=10, min_average_dollar_volume=50000000, min_rvol=2,
max_selected=10 y entry_window_minutes=60; versión ORB_RVOL_v0.1, sin indicadores.
El motor rechaza historical_download como disponibilidad observada. Resolver ese
bloqueo requiere evidencia compatible, nunca backdating ni rebajar el gate.

Tras aprobar datos/disponibilidad: baseline 1x, 2x y 3x de todos los coeficientes
monetarios de CostConfig y spread_bps/slippage_bps de BacktestConfig, misma estrategia
y riesgo. Base existente: comisión por lado/unidad 0,005 USD, deslizamiento total
por unidad 0,02 USD, spread 2 bps y slippage adicional 1 bp; fijos/mínimos/tasa
notional/impacto cuadrático 0. Son supuestos del simulador sin calibración eToro.
Se recalcula sizing conservando límites; no se fuerza igual número de operaciones.
Los tests 1x/2x/3x comprueban contabilidad sintética, no sensibilidad real.

Mínimo a reportar: trades, ganadoras/perdedoras, win rate, PnL bruto/neto, media y
mediana por trade, profit factor, drawdown, exposición, turnover, duración media,
mayor ganadora/perdedora, concentración por símbolo/día y sensibilidad a costes.
Campos no calculados son null con motivo. No interpretar cero señales por rechazo
de disponibilidad como backtest válido. El reporte ampliado real sigue pendiente.

Separación temporal exclusivamente; 60 sesiones (incluidos warmups) es exploratorio.
Congelar fechas de desarrollo/validación/OOS antes de mirar resultados y registrar
cada ejecución, sin optimización. Sin historial suficiente no hay OOS defendible.
Sharpe solo sobre serie diaria apropiada con jornadas sin trades, nunca anualizando
trades como días. Etiquetas permitidas con datos reales: HISTORICAL_RESULT_OBSERVED
u OUT_OF_SAMPLE_RESULT_OBSERVED; ninguna equivale a ventaja o rentabilidad validadas.
La [decisión de fase](SHADOW_READINESS.md) conserva todos los bloqueos.

Motor ejecutable: `backtesting/engine.py`; mismos ORBStrategy/RiskEngine que el recorrido
offline, sin transporte al bróker. Modelo minute-next-open-v1. No hay históricos de
mercado incluidos: los resultados de fixtures llevan **SYNTHETIC — NO EVIDENCE OF
PROFITABILITY**, estado RESEARCH_BLOCKED_DATA. La prueba demuestra ingeniería.

## Tiempo y ejecución

Selección utiliza solo finales disponibles al corte. Señales usan recepción; envío
ocurre available_at+latency_ms. Una orden aceptada reserva caja/riesgo/cupo y se llena
en el primer open estrictamente posterior. Con barras no hay cotización intraminuto:
para evaluar riesgo al enviar se usa último cierre disponible más fricción explícita.
Esto es una aproximación de investigación, incompatible con usarla como evidencia de
cotización ejecutable Demo. Un retraso de doce segundos produce SIGNAL_EXPIRED, no un
aumento oculto de TTL. Las órdenes pendientes caducan al acabar la ventana de entrada.

Eventos comparten reloj: se resuelve el cierre/stop de la barra anterior antes del open
siguiente. Para una posición ya abierta, low<=stop implica salida al menor entre stop
y open de esa barra, menos fricción. Incluso si la barra toca precios favorables, no
se atribuye un recorrido optimista. Un fill se revisa contra riesgo previsto; exceso
produce incidente y salida simulada inmediata. La ausencia de barras puede dejar
órdenes sin fill o posiciones abiertas; el reporte muestra la exposición, nunca flat
inventado. La próxima apertura disponible posterior al cierre programado permite cerrar.

Spread y slippage_bps se aplican adversamente a ambos lados. CostConfig es la única
fuente de comisiones: fijo, mínimo, unidad, notional y término cuadrático no negativo.
slippage_per_unit se reparte mitad por lado; bps de slippage son un escenario adicional.
La reserva de riesgo es conservadora y puede incluir fricción ya presente en el ask;
el PnL realizado solo descuenta precios reales del modelo y fees una vez. Se separan
fees, spread_slippage y costes totales. Sin costes conocidos se bloquea investigación.
No se garantizan stops, liquidez, suspensiones, ejecución ni transferibilidad de precios.

## Reproducción y medición

run_id depende de hash de datos, estrategia/riesgo/costes/ejecución, calendario y commit.
Se guarda semilla/modelo; si el llamador no aporta commit, queda UNRECORDED_WORKTREE.
Equity por cierre de sesión incluye jornadas sin operaciones y marca exposición no
resuelta al último precio observado. Se informan retorno, drawdown y duración por
sesiones, Sharpe de retornos diarios (252), esperanza USD/R, operaciones, win rate,
profit factor, rotación, costes, exposición media y tiempo sumado de posiciones.
Este último puede superar 1 con posiciones solapadas. Drawdown intradía puede ser mayor
que el muestreado a cierre y se etiqueta esa limitación. Sin pérdidas profit factor
es infinity si hay ganancias; sin operaciones o varianza suficiente, métricas son null
con motivo. No hay flujos externos en el portfolio de backtest.

`session_block_bootstrap` remuestrea bloques circulares de sesiones (no trades), semilla
fija e intervalo descriptivo 2,5–97,5%. Con tres sesiones sintéticas no hay inferencia
estadística válida. PnL por instrumento y curvas por sesión hacen visible concentración.
Ningún máximo entre experimentos demuestra superioridad.

## Experimentos y ventanas

`controlled_comparison` devuelve ORB base, ORB+RVOL, costes x2, latencia 2s y latencia
12s. No busca todas las combinaciones. `append_experiment` guarda cada ejecución en
JSONL local append-only. Declarar hipótesis/coste antes de mirar test; cambios posteriores
convierten ese test en exploratorio. `walk_forward_windows` separa desarrollo, validación
y test por sesiones ordenadas, con test no solapado y avance del tamaño del test.
Los warmups preceden cada ventana y no puntúan; no se hace split aleatorio por minuto.
v0.1 cierra intradía, por lo que no hay labels de posiciones superpuestos entre días
salvo incidentes de exposición, que invalidan esa interpretación y deben revisarse.

Antes de una evaluación final se debe registrar universo punto-en-el-tiempo, periodo,
potencia/tamaño de muestra justificado, hipótesis primaria, márgenes de costes/latencia,
regla para resultados no definidos y criterios de aceptación estadística. No se inventa
un umbral mensual de ganancias. Datos válidos importados son EXPLORATORY; ninguna ruta
eleva automáticamente a OUT_OF_SAMPLE_EVALUATED ni habilita dinero real.
