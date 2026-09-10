# Política de riesgo

Fuente ejecutable: `risk/engine.py`, `RiskConfig`, `CostConfig`, `RiskEngine.assess`.
El ejemplo asigna 10.000 USD virtuales, riesgo por operación ≤0,10%, pérdida diaria
≤0,50%, dos posiciones/intenciones, exposición bruta ≤100%, concentración ≤60%.
Los máximos de riesgo están acotados por validación; capital, precios y costes usan
Decimal finito. No hay apalancamiento ni cortos.

El motor busca mediante bisección el mayor múltiplo del paso admisible cuyo riesgo
`unidades*(ask-stop)+costes(unidades,ask)` y desembolso caben en todos los límites.
Costes incluyen fijos por lado, mínimo, por unidad, tasa sobre nominal, deslizamiento
y término cuadrático no negativo. No se redondea hacia arriba para alcanzar mínimos.
El spread está en bid/ask y no vuelve a cobrarse como comisión. Ejemplo: 10 USD de
riesgo, entrada 100, stop 99 y coste total 0,03 por unidad permiten 9,708 unidades con
paso 0,001; 9,709 excedería 10 USD. Los valores de costes YAML son supuestos sintéticos.

El presupuesto efectivo es el menor entre asignación, capital de referencia y equity;
se descuentan efectivo, reservas pendientes, riesgo abierto y pérdidas de sesión.
UNKNOWN conserva reservas y cupo. El ejecutor serializa evaluación y persistencia
bajo bloqueo de proceso. No se toma automáticamente el saldo Demo como presupuesto.

Controles previos: recepción/caducidad ≤10s, cotización ≤3s, reloj coherente, horario,
spread ≤0,3%, desviación señal/precio ≤0,5%, divergencia entre fuentes ≤0,5%, producto
acción común USD, elegibilidad y stop nativo comprobados. Los defaults de reglas de
instrumento pertenecen exclusivamente al simulador; Demo necesita evidencia externa.

Después de un fill se revisan protección y riesgo: incidente pausa entradas, cancela
pendientes propios y solicita salida propia. No amplía stops. Pausar entradas conserva
reconciliación y salida; cerrar no pasa filtros RVOL. PnL persistente separa comisiones,
realizado y valoración de posiciones del bot. No hay depósitos ni flujos externos.
El motor no garantiza pérdida máxima frente a gaps, ausencia de mercado o fallos.

Limitación de integración: la sesión Demo automática sigue bloqueada; falta una fuente
OHLCV compatible y reconciliación completa de cierres v1. No usar los defaults sintéticos
para aprobar instrumentos, costes ni protección reales de la cuenta virtual.
