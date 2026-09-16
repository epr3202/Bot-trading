# A7: auditoria de cotizacion y costes — PARTIAL/BLOCKED

Validacion final de esta auditoria: 861 tests PASS, 7 warnings; 16/16 gates PASS.
142 focales A7/A6 PASS; secret scan 187 archivos / 0 hallazgos; diff check 0.
Strategy 1/riesgo/runner A6/config/lock preservados por hashes. Evidencia exacta
en runtime/a7-quote-audit/verification.json y acceptance.json.

2026-09-16. El artefacto anterior contiene `age_seconds: 81.588043`, no
81588 segundos. La coma decimal en la respuesta al usuario fue ambigua.
El calculo anterior usaba `transport.now() - quote.event_time` despues del
parseo; no guardaba la recepcion HTTP exacta. No se puede reconstruir esa
recepcion retrospectivamente. La prueba equivalente usa 14:39:21.398043Z
menos 14:37:59.810Z y verifica exactamente 81.588043 segundos.

## Lecturas externas nuevas

Origen fijo: https://public-api.etoro.com, GET `/api/v2/market-data/rates`,
query documentada `instrumentIds=1001`. HTTP 200, AAPL, `realtime`.

| Evidencia local | Fecha cruda del proveedor (UTC contractual) | Recepcion UTC inmediata | Edad s | Bid / ask |
|---|---|---|---|---|
| runtime/a7-quote-audit/readiness-20260916T151135.json | 2026-09-16T15:10:59.623 | 2026-09-16T15:11:35.483831+00:00 | 35.860831 | 333.64 / 333.68 |
| runtime/a7-quote-audit/readiness-20260916T151414.json | 2026-09-16T15:12:59.687 | 2026-09-16T15:14:14.794782+00:00 | 75.107782 | 333.50 / 333.53 |

Ambas son nuevas peticiones HTTP. El cliente httpx no incorpora cache local.
Cabeceras publicas observadas: `Cache-Control: public, max-age=1, s-maxage=1`,
`CF-Cache-Status: DYNAMIC`, Date coherente con recepcion. No prueban la causa
interna del retraso ni ausencia absoluta de caches upstream; esta queda UNKNOWN.
No se agregan parametros ficticios, rutas alternativas ni retries de trading.

`utc_now()` usa datetime.now(UTC). El smoke no inyecta reloj, transporte mock
ni datos A6. `Z` y offsets se normalizan a UTC; la fecha sin sufijo sigue
el contrato UTC getRates. No usa timezone local, archivos, candles, Massive,
eligibility ni metadata para la frescura. El pre-send consulta rates de nuevo.

## Cambio acotado

- transport.py: guarda recepcion inmediatamente despues de obtener el cuerpo
  HTTP y antes de parsear JSON. No modifica despacho de mutaciones.
- market_data.py: usa esa recepcion aware UTC y normaliza event_time UTC.
  Reloj ausente/naive bloquea. La comprobacion adicional del adaptador contra
  su reloj actual conserva la edad durante procesamiento; limite 3 s intacto.
- etoro_demo.py: normaliza `value` observado y `amount` documentado a Decimal
  dentro del adaptador. Ausentes, no numericos, no finitos o campos duales
  contradictorios bloquean. No calcula ni inventa importes o costes de cierre.
- tests/fixtures/etoro_a7_costs_observed.json: costes publicos sanitizados de
  la lectura real 15:11:35; no cuenta, tokens ni claves.
- tests/test_demo_quote_cost_audit.py: regresion UTC, fecha con/sin sufijo,
  recepcion anterior al decode, HTTP nuevo, limites frescos/stale, costes.

## Gate y limite de esta entrega

DEMO_VERIFIED, scope write observado, AAPL/1001 y allowOpenPosition=true.
Consulta de costes para 1 unidad, leverage 1, subyacente long; parser PASS.
`settlementType=real` designa el subyacente, nunca una cuenta REAL.
Frescura FAIL: 75.107782 > 3 s. La elegibilidad observada permite leverage 1,
pero no se afirma validacion final de riesgo, sizing ni stop de una intencion:
no se creo ninguna. Gate agregado BLOCKED antes de habilitar trading.

Comando desde raiz, usando las credenciales existentes (ambas PRESENT):

```powershell
.\scripts\uv.ps1 run --frozen --env-file .env python runtime/a7-quote-audit/probe.py
```

Script diagnostico exit 2 (BLOCKED); el launcher PowerShell reporta exit 1.
GET y POST de consulta eligibility/costs; cero POST de orden, cero mutaciones,
cero ordenes. Sin provider orderId/positionId/closeOrderId; no hay posicion
del smoke que cerrar. REAL_CAPABILITY=NONE. Las etapas 7–11 quedan pendientes
por la condicion explicita del usuario: no continuar con quote retrasada.
No A8, no cambios Strategy 1, .env, riesgo, runner A6 ni autorizacion.
