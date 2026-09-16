# A2 — validación de datos Massive, 2026-09-15

## Evidencia real

AAPL reutiliza la captura HTTP previa inmutable. SPY y QQQ se descargaron con
el cliente Massive real: dos GET, HTTP 200 el 15/09 a las 14:15:49 y 14:16:04 UTC.
El primer intento restringido falló por CONNECTIVITY_FAILED y se preserva en
`runtime/a2-massive/attempt-1.json`. El segundo está en `attempt-2.json` en esa carpeta.
No se sustituyeron datos ni se cambiaron credenciales o configuración global.

Objetivo 14/09/2026; ventana 14/08/2026 13:30 UTC–14/09/2026 19:59 UTC
(inicio de última barra inclusivo). Cada símbolo tiene 21 sesiones completas,
8.190 barras regulares: 20 sesiones inmediatamente anteriores más objetivo.
Raw AAPL/SPY/QQQ: 17.588 / 17.601 / 18.545 barras respectivamente; fuera de
horario se excluyen, sin rellenar huecos. Los tres conjuntos de timestamps coinciden.
Parámetros: minuto, adjusted=true, sort=asc, limit=50000. Calendario y versión
de dependencias fijados por uv.lock, sesiones America/New_York, timestamps UTC.

| Criterio | Resultado |
|---|---|
| Objetivo + 20 sesiones previas por instrumento | PASS |
| Capturas Massive reales | PASS |
| ORH/ORL 5 minutos AAPL | PASS: 334.83 / 331.72 |
| RVOL con 20 aperturas anteriores | PASS: 1.085297795818647139199521439 |
| SPY y QQQ completos y alineados | PASS |
| VWAP con campos Massive | PASS: 333.8021631970573334714429697 |
| Evidencia reproducible | PASS |

Apertura: 09:30–09:34 NY (13:30–13:34 UTC); quinta barra termina 09:35.
RVOL vigente = suma de esos cinco volúmenes / media de las veinte sumas anteriores.
Numerador 1834725.760868; denominador 1690527.49202725. ORH/ORL/volúmenes/RVOL
coinciden exactamente entre Fraction raw y Decimal del motor.

VWAP vigente = sum(HLC3 * volumen) / sum(volumen), reiniciado en sesión regular,
390 barras objetivo. Usa h/l/c/v, campos del [contrato oficial Massive](https://massive.com/docs/rest/stocks/aggregates/custom-bars).
Es una aproximación por barras, no el VWAP exacto de trades ni el campo opcional vw.
Referencia por reordenación algebraica: 333.8021631970573334714429698;
diferencia Decimal 1e-25, tolerancia absoluta 1e-20.

RS vigente desde apertura hasta cierre de quinta barra: acción/benchmark por
precios alineados, sin gap nocturno. AAPL−SPY = -0.0056583396564916453438395162;
AAPL−QQQ = -0.0060946866862482405341895887 (fracciones, no porcentajes).
RS y VWAP son funciones de investigación inactivas. **No hay regla de régimen
especificada ni implementada en ORB_RVOL_v0.1**: se registra NOT_APPLICABLE,
sin inventar una fórmula ni afirmar validación de un filtro inexistente.

AAPL cumple el universo histórico: cierre previo 332.23 USD y liquidez media
9944172811.663554861085 USD, calculada como media de sum(close_minuto*volume).
RVOL inferior al umbral 2 no invalida su cálculo; no demuestra selección o señal.
SPY/QQQ son ETF de referencia, excluidos del universo de acciones operables.

## Reproducción offline

```powershell
.\scripts\uv.ps1 run --frozen python scripts/validate_massive_a2.py --target 2026-09-14 --aapl data/raw/massive/20260915T122702-6a68f76c --spy data/raw/massive/a2-SPY-7a9414b5bd91 --qqq data/raw/massive/a2-QQQ-b98a06944fb9 --output runtime/a2-massive/reproduction.json
```

La salida debe ser nueva. El comando no necesita credenciales ni red, verifica hashes,
identidades, calidad, 21 sesiones y cálculos. `offline-final.json` registra la
reproducción ejecutada. [Manifiesto portable](massive-a2-manifest.json) conserva
resultados, rutas relativas y hashes; el informe completo incluye calidad por sesión.
Los archivos raw privados no se versionan: otra máquina necesita las capturas
autorizadas para reproducir sus mismos hashes. Nunca falsificar NETWORK_HTTP.

Para descargar exclusivamente benchmarks ausentes se omiten sus rutas y se añade
`--capture-missing`; requiere MASSIVE_API_KEY heredada por el proceso. Una ruta
explícita inválida falla y nunca dispara una descarga sustitutiva. Errores y
criterios FAIL persisten; código de salida 2. La allowlist es AAPL/SPY/QQQ,
solo GET histórico api.massive.com, sin rutas arbitrarias ni cuentas.

## Límites y pruebas

HISTORICAL_DOWNLOAD permanece: no acredita disponibilidad observada en tiempo real,
señales causales, universo punto-en-el-tiempo, elegibilidad de bróker ni rentabilidad.
El gate OBSERVED_AVAILABILITY_REQUIRED sigue intacto. Sin cambios de Strategy 1,
riesgo, ejecución, eToro, lock, A3, tuning o backtesting de rendimiento.
No se ejecuta scripts/verify.py porque incluye CLI backtest y demo-offline con
simulación de órdenes, excluidas por este alcance; se ejecutan sus checks estáticos
y la suite de regresión automatizada separadamente. Resultados exactos en VERIFICATION.
