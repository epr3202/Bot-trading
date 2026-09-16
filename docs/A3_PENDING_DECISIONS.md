# A3 — propuestas de decisión pendientes

## Resolución aprobada — 2026-09-15

B1–B4 **RESUELTOS por decisión explícita del responsable**, incorporada en
ORB_RVOL_v1.0. B1: RS simultánea frente a SPY y QQQ desde apertura regular hasta
la candidata ORB, comparación estricta, margen cero; faltantes/empates no pasan.
B2: régimen desactivado. B3: confirmación VWAP desactivada.
B4: common_stock elegible, ETF no operables y SPY/QQQ reference-only.
No se requiere otra aprobación de estas decisiones. Especificación final:
[STRATEGY_1_A3_AUDIT](STRATEGY_1_A3_AUDIT.md).

## Historial de propuestas no adoptadas como conjunto

Estado de todas: **PROPOSED / NOT_APPROVED / NOT_IMPLEMENTED**.
Responsable: titular de la hipótesis (usuario). A3 BLOCKED; A4 pendiente.
Se usan B1–B4, los IDs ya existentes en la auditoría; no se abre otra convención.
[Evidencia y referencias históricas](STRATEGY_1_A3_AUDIT.md).
Ninguna opción se seleccionó por rendimiento ni introduce umbrales numéricos nuevos.

## B1 — fuerza relativa SPY/QQQ

**Problema:** definir si condiciona entradas y con qué benchmark/tiempo/umbral.
**Evidencia:** bootstrap H0:225 define diferencia de retornos desde apertura;
FUT-001 deja hipótesis/ventana pendientes. Helper recibe cuatro precios, flags false.
**Insuficiencia:** ni fórmula aislada ni ejemplo A2 deciden benchmark, operador,
threshold, timeframe, instante, lookback o comportamiento si faltan barras.

| Opción | Significado y efecto | Arquitectura / complejidad | Información necesaria |
|---|---|---|---|
| B1-A | Conservar RS desactivada en versión inicial; las entradas no dependen de SPY/QQQ | Sin cambio del motor; baja, congelación explícita | Aprobar exclusión del filtro para esta versión |
| B1-B | Nueva versión con un benchmark fijo elegido previamente | Reutiliza helper; añade configuración y sincronización; media | Elegir SPY o QQQ; timeframe, inicio/fin, umbral/comparador, momento y faltantes |
| B1-C | Nueva versión con elección por instrumento o evaluación conjunta de ambos | Mapeo auditable y/o combinación; media-alta | Regla de elección o AND/OR, todos los campos de B1-B y política de autorreferencia |

**Decisión requerida:** ¿Se aprueba B1-A o se solicita B1-B/B1-C con una especificación
completa de sus campos pendientes? Elegir B/C por sí solo no autoriza inventar esos campos.

## B2 — régimen de mercado

**Problema:** definir qué condiciones de mercado habilitan o bloquean entradas.
**Evidencia:** bootstrap H0:227 exige causalidad, FUT-002 difiere la especificación,
regime_enabled es Literal[False]; no se recuperó un indicador o umbral histórico.
**Insuficiencia:** causalidad es una restricción temporal, no una regla bullish/bearish/neutral.

| Opción | Significado y efecto | Arquitectura / complejidad | Información necesaria |
|---|---|---|---|
| B2-A | Sin filtro de régimen en la versión inicial | Sin cambio; baja | Aprobar su exclusión |
| B2-B | Nueva versión con régimen fijado usando datos anteriores a apertura | Indicador y snapshot por sesión; media | Instrumento, indicadores, timeframe/lookback, umbrales/clases, disponibilidad y tratamiento de faltantes |
| B2-C | Nueva versión con régimen reevaluado intradía | Sincronización de eventos y estado causal; alta | Campos de B2-B más frecuencia, vigencia y si bloquea entradas o afecta posiciones existentes |

**Decisión requerida:** ¿Se aprueba B2-A o se especifica B2-B/B2-C íntegramente antes
de implementarlo? No se propone una media móvil, ventana o umbral sin evidencia.

## B3 — confirmación VWAP

**Problema:** decidir si el cálculo VWAP participa en la entrada y cómo.
**Evidencia:** helper HLC3, volumen verificado positivo y sesión única; bootstrap
H0:229 separa entrada/salida/retroceso; FUT-002 mantiene especificación pendiente.
**Insuficiencia:** el helper no define `close > VWAP`, cruce, distancia, pendiente
ni evaluación. Rechazar volumen inválido no define una política para minutos ausentes.

| Opción | Significado y efecto | Arquitectura / complejidad | Información necesaria |
|---|---|---|---|
| B3-A | Sin confirmación VWAP en versión inicial | Sin cambio; baja | Aprobar su exclusión |
| B3-B | Nueva versión con comparación puntual contra VWAP en el evento de entrada | Reutiliza helper con acumulación causal; media | Sesión, precio de comparación, operador, inclusión de barra actual, instante y gaps/faltantes |
| B3-C | Nueva variante con cruce o condición temporal VWAP | Añade estado de eventos; alta | Campos B3-B, definición exacta del cruce/condición, vigencia, rearme y relación con unicidad ORB |

**Decisión requerida:** ¿Se aprueba B3-A o se aporta la condición exacta B3-B/B3-C?
No se presupone ningún operador. La variante de retroceso no se mezcla implícitamente
con la ruptura directa. Ausencia de datos no se rellena silenciosamente.

## B4 — universo y papel de SPY/QQQ

**Problema:** resolver solicitud acciones+ETF frente a exclusión inicial explícita.
**Evidencia:** bootstrap H0:169 excluye ETF y asigna SPY/QQQ solo a investigación;
tipos internos y catálogo histórico permiten representarlos; tres capas bloquean
su entrada. A2 valida datos de benchmarks, no compatibilidad de trading.
**Insuficiencia:** soporte del tipo no equivale a autorización de universo ni a
elegibilidad de producto eToro. No se encontró decisión posterior de habilitación.

| Opción | Significado y efecto | Arquitectura / complejidad | Información necesaria |
|---|---|---|---|
| B4-A | Mantener common_stock USD XNYS/XNAS y SPY/QQQ solo referencias | Sin cambios; baja | Aprobar universo inicial sin ETF |
| B4-B | Nueva versión con acciones+ETF autorizados, excluyendo SPY/QQQ operables | Ajustes universo/riesgo/adaptador y metadata; media-alta | Subtipos/exclusiones, mercados, identidad, elegibilidad, pasos/costes, política de ranking/liquidez y conservación de límites |
| B4-C | Nueva versión con acciones+ETF y SPY/QQQ también operables | Lo anterior más política benchmark/autorreferencia; alta | Campos B4-B y benchmark de cada ETF, interacción con cupos y ausencia de auto-comparación implícita |

**Decisión requerida:** ¿Se conserva B4-A o se especifica la ampliación B4-B/B4-C,
incluyendo explícitamente el rol de SPY/QQQ? La palabra «inicialmente» del bootstrap
no autoriza por sí misma una fecha o condición de ampliación.

## Condición de aprobación y siguiente paso

Una decisión debe registrar ID/opción, valores y reglas completos cuando corresponda,
responsable y fecha. Con A en los cuatro puntos se podría preparar una congelación
explícita de v0.1 conservando esas exclusiones; esto aún no está aprobado.
Con filtros activos o ETF se requiere una nueva versión y pruebas de causalidad,
universo y riesgo, sin usar resultados A4 para diseñarla. Toda modificación sigue
sujeta a los límites virtuales y guardas existentes; no habilita sesiones externas.

**A4 consume Strategy 1 congelada; A4 no modifica Strategy 1 para mejorar resultados.**
