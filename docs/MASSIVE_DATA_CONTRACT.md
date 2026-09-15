# Massive histórico — contrato y validación AAPL

## Resultado externo, 2026-09-15

**MASSIVE_HISTORICAL_RVOL_VERIFIED**. Captura real por HTTP, no por MCP ni mock.
Primero falló la red restringida con CONNECTIVITY_FAILED, sin respuesta HTTP.
El mismo comando con permiso de red obtuvo un HTTP 200, sin reintentos ni páginas
adicionales. El intento fallido queda preservado; no se reclasifica como fallo de
autenticación ni falta de suscripción.

| Campo | Evidencia observada |
|---|---|
| provider / símbolo | massive / AAPL, common_stock USD XNAS; sin ID de bróker inventado |
| endpoint | `GET https://api.massive.com/v2/aggs/ticker/AAPL/range/1/minute/1786714200000/1789415940000` |
| parámetros | `adjusted=true&sort=asc&limit=50000` |
| plan/access observed | Plan desconocido; HISTORICAL_AGGREGATES_HTTP_200 |
| timeframe / availability_class | 1m / HISTORICAL_DOWNLOAD |
| ventana | 2026-08-14 13:30 UTC a 2026-09-14 19:59 UTC, límite de inicio de última barra inclusivo |
| sesiones | 20 previas completas + objetivo 2026-09-14; 21 solicitadas, 21 válidas |
| barras | 17.588 raw; 8.190 regulares; 9.398 excluidas por horario regular |
| calidad regular | PASS; cero huecos, duplicados, precios no positivos, OHLC inválido, volúmenes negativos/cero, errores de zona o desorden |
| coverage | 100_percent_market, basado en contrato documental del endpoint histórico consolidado |
| ORH / ORL | 334.83 / 331.72 |
| V5 objetivo | 1834725.760868 |
| media V5 de las 20 previas | 1690527.49202725 |
| RVOL | 1.085297795818647139199521439 |
| comparación motor | MATCH, igualdad Decimal exacta para las cinco métricas |
| decisión operativa del motor | OBSERVED_AVAILABILITY_REQUIRED; cero candidatos y señales |

Sesiones exactas: agosto 14, 17–21, 24–28, 31; septiembre 1–4, 8–11 y 14.
Labor Day (07/09) se excluye. Todas tienen 390 minutos. Esta ventana no observa
una transición DST ni cierre temprano; ambos se prueban con datos fabricados y
el calendario fijado, sin atribuir esa evidencia a la captura real.

Raw inmutable: `data/raw/massive/20260915T122702-6a68f76c/`.
Informe: `runtime/massive-audits/20260915T122702-6a68f76c/result.json`.
Primer fallo: `runtime/massive-audits/20260915T122542-86ddc8a1/result.json`.
Manifiesto público mínimo: [massive-historical-manifest.json](massive-historical-manifest.json).
No se versionan raw, CSV, credenciales, identificadores de petición ni estado local.

## Contrato documental del volumen

Documentación oficial consultada el 15/09/2026:

- [Custom Bars](https://massive.com/docs/rest/stocks/aggregates/custom-bars):
  `t` es inicio del intervalo en milisegundos Unix; `o/h/l/c` son precios y `v`
  el volumen negociado del intervalo. Los agregados usan trades elegibles; puede
  faltar una barra cuando no los hay. `next_url` es opcional y dirige a otra
  página. `limit=50000` limita agregados base, no garantiza completitud por sí solo.
- [Trade Eligibility](https://massive.com/blog/understanding-trade-eligibility):
  Massive aplica las reglas de actualización consolidadas CTA/UTP. El volumen
  suma tamaños de trades elegibles para volumen; OHLC aplica elegibilidad por
  campo. No significa número de operaciones, ticks, cotizaciones ni todos los
  eventos publicados. Una condición que excluye actualizar volumen excluye ese
  aporte; una exclusión de precios no implica excluir volumen. El ejemplo oficial
  Average Price Trade (CTA B / UTP W) actualiza volumen, pero no OHLC. Las condiciones
  múltiples se evalúan según las reglas del campo y las notas de las matrices.
  No reconstruimos trades desde minutos ni afirmamos auditar sus condiciones
  individualmente; `n` y `vw` se conservan raw y no reemplazan `v`.
- [Stocks](https://massive.com/stocks): documenta cobertura de todo el mercado
  estadounidense, planes individuales basados en SIP y SIP completo al final del
  día también en Business. Por eso el cliente restringe la captura a fechas NY
  anteriores a hoy. La cobertura de este endpoint EOD queda documentada sin
  inferir nombre de plan desde HTTP 200. No se usa FMV intradía ni feeds parciales.
  `100_percent_market` describe alcance de mercados; no elimina las exclusiones
  por condiciones ni acredita reconciliación independiente contra cada trade.
- [Volumen fraccionario](https://massive.com/knowledge-base/article/why-does-volume-return-as-a-decimal-value-from-the-aggregates-endpoint):
  `adjusted=true` ajusta OHLCV por splits y puede producir volumen fraccionario.
  El proveedor conserva decimales, sin redondearlos a acciones enteras ni ajustar
  otra vez. Esta captura devuelve fracciones; no demuestra por sí sola qué evento
  corporativo produjo cada fracción. No es volumen monetario ni ajuste por dividendos.

La versión local `massive-consolidated-eligible-split-v1` enlaza estas fuentes.
Si su evidencia falta o no coincide, el lector conserva `volume_kind=unknown`,
coverage=null y la auditoría no puede dar el hito verificado.

## Integración y reproducción

`data/massive_http.py` adquiere; `data/massive.py::MassiveHistoricalProvider.load()`
lee offline y devuelve el DataBundle del MarketDataProvider existente;
`data/massive_audit.py` valida y compara. Son independientes de Alpaca y eToro.
No hay SDK nuevo ni cambios de Python, lock, estrategia, DataConfig o configuración
operativa. CSV/manifiesto son compatibles con el importador existente.

```powershell
.\scripts\uv.ps1 run --frozen python scripts/audit_massive_history.py --capture --target 2026-09-14
.\scripts\uv.ps1 run --frozen python scripts/audit_massive_history.py --input data/raw/massive/20260915T122702-6a68f76c
```

Sin `--target`, elige la última sesión de fecha NY anterior a hoy. Un objetivo
de hoy/futuro se rechaza antes de red, incluso después de su cierre. Una descarga
EOD que aún no esté disponible debe fallar por acceso/completitud; no se inventa
un tiempo de publicación. En modo offline el objetivo proviene de la captura.
Cada ejecución crea carpetas nuevas; no sobrescribe raw ni informes anteriores.

`MASSIVE_API_KEY` se lee exclusivamente del entorno del proceso y se envía en
Authorization Bearer, según el [Quickstart oficial](https://massive.com/docs/rest/quickstart).
No se carga `.env`, no se busca en perfiles, no se reutilizan claves Alpaca/eToro.
El repr de credenciales oculta valores. Respuestas de error no se guardan; un
cuerpo exitoso que refleje la clave también se rechaza antes de persistirlo.
TLS obligatorio, proxy del proceso y CA local `certs/epm-root.cer` o
`REQUESTS_CA_BUNDLE`; sin desactivar certificados ni cambiar opciones globales.

Solo GET, host api.massive.com, AAPL y range/1/minute. No hay rutas de cuenta,
órdenes, WebSocket ni URL arbitraria. Las páginas pueden avanzar el inicio dentro
de la ventana pero no cambiar el final, símbolo, host, granularidad, sort o ajuste.
Cursores opacos solo se siguen tras validar URL/query; redirecciones se rechazan.
Cadena, terminación y checksums se verifican otra vez al cargar offline.

Pausa local de 13s entre peticiones para respetar 5/min; no es latencia de datos.
429 admite hasta tres intentos cuando Retry-After/Reset define espera <=60s.
Espera desconocida, inválida o mayor bloquea con MASSIVE_RATE_LIMITED. No se reduce
una espera larga para reintentar antes. Quota restante cero también bloquea/espera
antes de la siguiente página. 401/403 no se reintentan; 403 no prueba qué plan falta.

## Calidad, aritmética y disponibilidad

Se comprueba presencia de t/o/h/l/c/v, milisegundos enteros alineados al minuto,
valores Decimal finitos, precios positivos, OHLC coherente y volumen no negativo.
El orden se valida antes de cualquier clasificación de horario. Duplicados,
incluidos idénticos, bloquean calidad: se representa una fila en el CSV pero no
se da por válida la captura. Huecos y cero volumen bloquean; no se rellenan.
Errores que interrumpen el parser dejan conteos desconocidos, nunca falsos ceros.

Calendario XNYS de exchange-calendars fijado por uv.lock; zona America/New_York.
Se exigen todos los minutos de las 21 sesiones, apertura 09:30 y ventana
09:30..09:34. Cierre temprano usa su cierre real (210 minutos en la prueba de
28/11/2025). Se prueban DST marzo/noviembre y festivos. Los huecos no se atribuyen
a halts sin evidencia independiente. Cierres extraordinarios futuros requieren
revisar el calendario; no se inventa una sesión.

La referencia independiente lee directamente t/h/l/v raw usando Fraction:
V5 de cada sesión = suma de sus cinco primeros minutos; media = suma de veinte
V5 anteriores /20; RVOL = V5 objetivo/media; ORH/ORL = máximo high/mínimo low
de la apertura objetivo. La ruta del motor usa Bar/Decimal y su función existente
`ORBStrategy.opening_metrics`. Se exige igualdad exacta de las cinco métricas;
una diferencia de 1e-13 ya bloquea en la regresión.

received_at y available_at son la recepción real de cada página, nunca el tiempo
de mercado más una demora supuesta. availability_class=HISTORICAL_DOWNLOAD,
availability_kind=historical_download y latency=null. `final=true` solo identifica
un intervalo cerrado en la instantánea; pueden existir correcciones posteriores.
El ensayo con datos posteriores a 09:34 alterados conserva el cálculo inicial.
No se etiqueta la descarga como observed ni se modifica el gate del motor.

## Estados públicos y límites

| Estado | Condición |
|---|---|
| MASSIVE_AUTHENTICATION_FAILED | Clave ausente/inválida, HTTP 401/403 o denegación de auth en payload; reason distingue el caso |
| MASSIVE_RATE_LIMITED | Cuota agotada o espera pendiente/inválida; fallo bloqueante |
| MASSIVE_DATA_INCOMPLETE | Transporte, almacenamiento, esquema, calendario, calidad, cadena de páginas o comparación fallidos; reason conserva el motivo |
| MASSIVE_VOLUME_SEMANTICS_UNVERIFIED | Aritmética/calidad completas pero evidencia semántica no acreditada |
| MASSIVE_HISTORICAL_RVOL_VERIFIED | Captura NETWORK_HTTP, 21 sesiones válidas, semántica acreditada, igualdad exacta y gate operativo preservado |

Mocks permanecen CONTRACT_TEST y no reciben el hito externo; el test de la rama
de éxito manipula metadata solo dentro de un directorio de pruebas fabricadas.
Una declaración local no es certificación criptográfica de acceso: la evidencia
externa real de esta fase es la ejecución HTTP registrada y su raw inmutable.

eToro DEMO_READ_VERIFIED se conserva como hito histórico. Alpaca sigue implementado
y bloqueado externamente según su evidencia previa; eToro Market Data sigue
insuficiente para RVOL. No se habilitan órdenes, Demo Write ni shadow.
Este resultado acredita aritmética histórica para AAPL, no señales causales,
rentabilidad, universo punto-en-el-tiempo, disponibilidad realtime o ejecución.
Pruebas, gates, cobertura y commits: [VERIFICATION](VERIFICATION.md).
