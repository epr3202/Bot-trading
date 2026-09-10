# ORB_RVOL_v0.1

Implementación: `strategies/orb.py`, modelo StrategyConfig usado por YAML validado.
Hipótesis no validada, exclusivamente larga. Fuerza relativa, régimen y VWAP son false
literales en v0.1: no basta un flag para activar otra estrategia.

## Universo y cálculo

Acciones comunes USD en XNYS/XNAS; ETF, ADR y SPY/QQQ excluidos. La elegibilidad real
de instrumento/producto eToro se vuelve a verificar en riesgo/preflight. Cada sesión
exige las 20 sesiones bursátiles inmediatamente anteriores completas y disponibles.
Este criterio es deliberadamente más conservador que saltar huecos hasta reunir veinte
días antiguos. Cierre previo >10 USD; promedio de `sum(cierre_minuto*volumen_minuto)`
de cada sesión >50.000.000 USD. Es una aproximación con cierres de minuto, no turnover
exacto de trades ni cierre diario multiplicado por volumen diario.

Rango [apertura, apertura+5m): ORH=max(high), ORL=min(low), ORO=primera open,
ORC=quinta close. Numerador: suma de cinco volúmenes de hoy; denominador: promedio de
las mismas cinco velas de las 20 sesiones previas, sin hoy ni volumen final del día.
Denominador <=0, ventana inválida o volumen no comprobado produce exclusión explícita.

Se congela a apertura+5m+2s (espera configurable 0–10s). Faltantes/tardíos se excluyen;
el reporte conserva evaluable_symbols y motivos. Se escogen hasta diez RVOL>=2, orden
descendente RVOL, después liquidez previa y símbolo. No se vuelve a ordenar ese día.
Revisiones posteriores se conservan como calidad, no cambian señales antiguas.

Ejemplo fixture primer día: cada apertura histórica suma 12.500 acciones sintéticas.
SIMA suma 37.500, RVOL=3; SIMB 25.000, RVOL=2; SIMC 12.500, RVOL=1 y se excluye.
SIMA: ORO=100, ORC=100,50, ORH=100,70, ORL=99,80. La barra 09:35–09:36 cierra
100,90; solo se conoce a 09:36:00,200 NY, nunca a las 09:35.

## Intención y salida

ORC debe superar ORO. La primera vela completa posterior al rango que cierra
estrictamente sobre ORH crea una única signal_id estable por versión/sesión/símbolo.
La recepción y envío deben ocurrir antes de apertura+60m; el rango inicial no puede
confirmarse a sí mismo. Señales simultáneas siguen el ranking congelado. Rechazo,
cancelación o stop no autoriza otra intención. Persistencia asegura esta regla también
después de reiniciar; Strategy devuelve la misma identidad para el mismo día.

Caducidad de señal: 10s desde available_at. En replay se envía al sumar latencia; la
orden ya aceptada puede esperar el siguiente open sin extender la vida de la señal.
Antes de la escritura conectada se necesita cotización fresca real y evaluación de
riesgo. El proxy de último cierre usado en backtest no certifica esas condiciones.

Stop inicial ORL. Sin objetivo fijo, trailing, promedio a la baja ni salida VWAP.
Salida programada cinco minutos antes del cierre de calendario, también en jornadas
reducidas. Ausencia de barra/cotización no demuestra ejecución: queda incidencia de
exposición pendiente. El stop puede saltar; un precio garantizado no se modela.

## Comparaciones predefinidas

ORB_BASE_v0.1 usa el mismo universo/riesgo, sin filtro RVOL, y ranking de liquidez.
No se ocultan diferencias: al existir límite de diez, el ranking distinto también
forma parte de esta comparación. `features.py` calcula RS simple desde apertura
(r_acción-r_referencia, sin gap nocturno) y VWAP HLC3 por volumen con reinicio de sesión.
Son funciones de investigación, no filtros activos. Beta, régimen, entrada en retroceso
y reglas VWAP requieren una especificación/versionado independiente y test temporal.
