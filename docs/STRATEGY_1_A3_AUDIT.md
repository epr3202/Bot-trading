# A3 — especificación congelada de Strategy 1 v1

## Versión final aprobada — 2026-09-15

**A3 DONE — Strategy_1 / ORB_RVOL_v1.0**. Las decisiones explícitas del responsable en esta
iteración sustituyen los bloqueos B1–B4. El historial inferior se conserva como
antecedente, no como estado vigente. Verificación final en [VERIFICATION](VERIFICATION.md).

| Decisión | Estado E1 aprobado | Regla v1 |
|---|---|---|
| B1 / A3-RS | RESUELTO | RS activa, SPY y QQQ obligatorios; comparación estricta contra ambos, margen 0 |
| B2 / A3-REGIME | RESUELTO | Régimen desactivado; no rechaza por régimen general |
| B3 / A3-VWAP | RESUELTO | Confirmación VWAP desactivada; helper HLC3 conservado |
| B4 / A3-UNIVERSE | RESUELTO | Solo acciones comunes elegibles; ETF excluidos, SPY/QQQ reference-only |

### Identidad, configuración y carga

Implementación: `src/intraday_etoro_lab/strategies/orb.py::ORBStrategy` con
`StrategyConfig.version="ORB_RVOL_v1.0"`. Configuración canónica:
`configs/strategy-1-v1.yaml`, cargada mediante `config.load_config()` existente.
`ORB_RVOL_v0.1`, `ORB_BASE_v0.1` y `configs/offline.yaml` siguen disponibles;
v0.1 continúa rechazando activación RS. No hay registry o sistema paralelo.

El YAML v1 explicita todos los campos strategy/risk/costs. StrategyConfig rechaza
alterar parámetros v1 y ORBStrategy revalida incluso objetos copiados sin validación.
AppConfig impide modificar riesgo/costes bajo v1. `strategy_hash` identifica solo
strategy/risk/costs, independiente de datos, runtime y parámetros de replay A4.
Los costes auditados son supuestos locales conservados, no tarifas externas verificadas.
El snapshot contiene configuración efectiva, hash y SHA-256 de fuentes del contrato;
su bloque historical_audit preserva la evidencia anterior sin reinterpretarla.

```powershell
.\scripts\uv.ps1 run --frozen python scripts/inspect_strategy_v1.py
```

El comando solo carga/verifica configuración y fuentes; no descarga datos, emite
señales, consulta cuentas o ejecuta replay. Cualquier hash divergente devuelve FAIL.
La regeneración del snapshot requiere revisar/versionar el cambio; no debe utilizarse
para aprobar cambios silenciosos de v1 durante A4.

### RS causal y tratamiento de la primera candidata

Para cada instrumento, retorno = close de la candidata / open de 09:30 NY −1.
La función existente de diferencias de retornos se reutiliza; LONG exige diferencia
estrictamente positiva respecto a SPY **y** QQQ. No hay margen, ranking RS, suavizado
o sustitución por otro benchmark. El denominador es la apertura regular exacta de
esa sesión, nunca premarket, cierre previo o primera barra disponible arbitraria.

Se mantiene selección ORB a apertura+5m+2s. La primera barra final posterior al
rango con close>ORH y disponible antes de apertura+60m es la candidata original.
RS se evalúa en candidate.available_at, sin esperar a que llegue un benchmark.
Se requieren apertura y barra de SPY/QQQ con event_time exactamente igual al evento
correspondiente, final=true, revision=0, identidad ETF/USD inequívoca y misma fuente,
volumen positivo, received_at/available_at <= candidate.available_at.
El identificador del instrumento de cada barra debe coincidir con el del bundle.

Un minuto anterior es stale para esta comparación; uno posterior no es sustituto.
Las barras de revisión posterior no reemplazan la primera final conocida. Los
timestamps/intervalos/OHLC válidos siguen sujetos al modelo Bar e importador existentes.
Empates, faltantes, identidades ambiguas o recepción tardía producen rechazo explícito
RS_*; no se imputa ni se evalúa con un único benchmark. Si la primera candidata
no pasa RS se termina la evaluación de ese símbolo/sesión, conservando la semántica
de la primera candidata y evitando reintentos con barras posteriores.

La estrategia sigue siendo exclusivamente LONG. La regla short conceptual aprobada
sería superar a ambos a la baja, pero no existe flujo short operativo y no se implementa.

### Datos de referencia y universo

ORBStrategy recibe un DataBundle con acciones y benchmarks. El loader existente
provider=import ya admite CSV/Parquet multiinstrumento con `asset_class=etf` para
SPY/QQQ, manifiesto y hashes; el test de integración verifica esa ruta sin adaptadores
nuevos. Se conservan las capturas Massive A2 y su validación; no se descargan otra vez.
Cada captura Massive actual es un instrumento independiente: seleccionarla por sí
sola no agrega benchmarks ni habilita RS. No se crea una conexión ficticia.

El YAML congelado usa fixtures como contexto offline seguro; ese fixture existente
no contiene SPY/QQQ y por tanto bloquea las entradas RS. Para otro dataset se cambia
solo data mediante el loader existente, conservando exactamente strategy/risk/costs
y strategy_hash. La congelación de la hipótesis no constituye una ejecución A4.
Los datos Massive A2 mantienen HISTORICAL_DOWNLOAD: el gate
OBSERVED_AVAILABILITY_REQUIRED permanece y no se backdatean recepciones.

SPY/QQQ nunca integran evaluable_symbols, ranking, selección ni señales. Por ello no
alcanzan sizing, reservas, posiciones o cupos de Strategy 1. Incluso si un loader
los etiquetara incorrectamente como common_stock, el veto por símbolo permanece.
ETF genéricos tampoco son candidatos. Es una decisión explícita del universo, no
una limitación de capacidad del sistema para representar ETF.

### Parámetros y reglas preservadas

ORB 5m; RVOL V5/media de 20 V5 anteriores, mínimo 2; ventana 60m; selección top-10
por RVOL/liquidez/símbolo; apertura alcista, stop ORL, TTL 10s y salida cierre−5m.
Universo USD XNYS/XNAS; cierre previo >10 y liquidez media >50 millones.
Capital virtual 10.000; riesgo/trade 0,10%; diario 0,50%; 2 posiciones/intenciones;
exposición bruta 100% e individual 60%. Sizing, costes, controles de cotización,
reservas y ejecución no se modifican. El inventario anterior detalla sus fórmulas.

**A4 debe ejecutar Strategy 1 v1 exactamente como queda congelada al cerrar A3.**
Cambiar ORB/RVOL/RS/benchmarks/régimen/VWAP/universo/filtros/entradas/salidas/riesgo
o sizing requiere una nueva versión y decisión/experimento explícitos.

## Antecedente preservado — auditoría bloqueada previa

Estado: **A3 BLOCKED**. No hay configuración final congelada para A4.
Base Git: `ed456c32355bea05b5c6e04bc4b889ce8bce8ef3`.
El árbol de partida contiene los cambios A2 sin commit; no se atribuyen a ese hash.

## Continuación: investigación histórica B1–B4, 2026-09-15

Se conserva la auditoría anterior. **A3 sigue BLOCKED**: se recuperó evidencia E1
de exclusiones iniciales, pero ninguna especificación completa del alcance ampliado.
Las propuestas para revisión humana están en [A3_PENDING_DECISIONS](A3_PENDING_DECISIONS.md).
No se adoptó ninguna opción ni se modificaron reglas/configuración/tests.

### Cobertura de búsqueda y reproducción

Se inspeccionaron las 15 revisiones alcanzables por `git log --all` y los árboles
de cada una, incluyendo main, feat/phase3-readonly-evidence, recovery/phase2-reviewed
y origin/main local. No se hizo fetch, checkout, reset o rebase; la conclusión se
limita al historial disponible, no a commits remotos desconocidos o inaccesibles.
Se revisaron los diffs completos de estrategia, helpers, riesgo, YAML, bootstrap,
especificación y registro de experimentos, incluidas líneas eliminadas.

Comandos Git de solo lectura empleados:

```powershell
git log --all --format="%H %s"
git log --all -G 'SPY|QQQ|VWAP|regime|ETF|relative.strength' --name-only -- src configs docs BOOTSTRAP_SPEC.md
git log --all -S SPY --format="%H %s" --name-only
git log --all -p -- src/intraday_etoro_lab/strategies/orb.py
git blame -L 165,170 -- BOOTSTRAP_SPEC.md
git blame -L 221,231 -- BOOTSTRAP_SPEC.md
git show 6af05f1b16b8e3488a5cd959dc0e7f889b258fd6:configs/offline.yaml
```

`-S` se repitió para QQQ, VWAP, regime, ETF, relative strength, relative_strength
y HLC3. Además `git grep -n -I -i -E` sobre cada commit buscó esos términos,
benchmark, bullish/bearish, asset_type/security_type y equivalentes; se inspeccionaron
65 pares únicos archivo/texto. Lectura directa del bootstrap incluyó régimen causal
en español. Se contrastó con `rg` sobre código, tests, fixtures, JSON, YAML, TOML,
README, ADR y documentos actuales, incluidos los archivos A2/A3 aún sin commit.
Los falsos positivos (NetworkSpy, formatter, tarifas y fuerza de tests) no son reglas.
Logs de consultas y diffs: runtime/a3-history; `before.json` conserva hashes previos.

### Evidencia histórica concreta

H0 = `6af05f1b16b8e3488a5cd959dc0e7f889b258fd6` (bootstrap inicial).
Las líneas siguientes pertenecen a archivos que no cambiaron desde H0, salvo donde
se indica otro commit o working tree.

| Hallazgo | Fuente / commit / líneas | Clase y significado |
|---|---|---|
| Extensiones desactivadas inicialmente | H0, BOOTSTRAP_SPEC.md:33 y 221–231; docs/adr/003-strategy-v01.md:5 | E1: decisión inicial; no define filtros activos |
| RS simple desde apertura sin gap | H0, BOOTSTRAP_SPEC.md:225 | E1 parcial: r_acción−r_referencia; no elección SPY/QQQ, umbral ni instante de entrada |
| RS ejecutable aislada | H0, strategies/features.py:8–13 | E2 para entrada: recibe cuatro precios; no política de selección ni evaluación |
| Régimen solo causal | H0, BOOTSTRAP_SPEC.md:227 | E1 parcial: prohíbe información futura; no define indicadores/clases/umbrales |
| VWAP por sesión y variantes separadas | H0, BOOTSTRAP_SPEC.md:229; features.py:16–34 | E1 para intención de extensión; E2 para confirmación: helper HLC3 sin regla de entrada |
| Pendientes expresos FUT-001/FUT-002 | H0, docs/EXPERIMENT_REGISTRY.md:12–13 | E1: hipótesis/ventana RS y especificaciones régimen/VWAP pendientes; no activar en v0.1 |
| Exclusión ETF y rol SPY/QQQ | H0, BOOTSTRAP_SPEC.md:169; docs/STRATEGY_SPEC.md:9 | E1: exclusión inicial explícita; SPY/QQQ solo referencias |
| Flags false en única configuración histórica | H0, configs/offline.yaml:19–21; orb.py:26–28 | E1 consistente con ADR; no existe otra revisión de ese YAML |
| Guard histórico añadido | `ef8bf5564f6e15bd04ae084c18cd63dd27ba380b`, orb.py diff | E1 de seguridad: OBSERVED_AVAILABILITY_REQUIRED; ninguna activación de filtros |
| Extracción ORB/RVOL sin nueva fórmula | `880993a7536e41cf989932cc1f6faecc70d7d63f`, orb.py diff | E2 respecto a B1–B4: aritmética existente, sin política nueva |
| QQQ excluido en muestra externa | `d063f8273fd5e6186ef2731685aea0a7d61f3658`, docs/DATA_PROVIDER_AUDIT.md:68–69 | E1 corroborativa de exclusión; no justifica habilitar ETF |
| vw opcional Alpaca | `c1c5a114f2e6bc3a56a14e1770fbec4c29089a16`, data/alpaca.py:162–165 y 284 | E2: valida/cuenta campo, no confirmación VWAP |
| Semántica de volumen Alpaca | `43c9cc5b7d6366ee72d38dd17542ec7341e4e7e1`, docs/ALPACA_DATA_CONTRACT.md | E2 para filtros: contrato de datos, no regla de entrada |
| ETF representable en tipos | H0, domain/models.py:13–18; docs/etoro_spec_snapshot.json:3791,3986 | E2: capacidad de representación/catálogo, no decisión de operar ETF |
| SPY/QQQ históricos A2 | Working tree, data/massive.py:69–76 y tests/test_massive_a2.py:23–39 | E2 para trading: ETF de referencia, no congelación ni elegibilidad eToro |

### Matriz de resolución

Confianza alta significa certeza sobre la evidencia localizada y sus límites;
no certeza sobre una regla de trading ausente.

| Bloqueo | Estado | Evidencia | Fuente | Regla recuperada | Confianza |
|---|---|---|---|---|---|
| B1 RS | PENDIENTE | E1 parcial + E2; E3 para filtro completo | H0 bootstrap:225, FUT-001, features.py | Diferencia de retornos desde apertura; flag false; faltan benchmark/evaluación/umbral | Alta |
| B2 Régimen | PENDIENTE | E1 causalidad/desactivación; E3 para filtro completo | H0 bootstrap:227, FUT-002 | Solo datos disponibles al decidir; sin definición bullish/bearish/neutral | Alta |
| B3 VWAP | PENDIENTE | E1 extensión separada + E2; E3 para confirmación | H0 bootstrap:229, FUT-002, features.py | HLC3 de sesión; sin comparador/momento/faltantes para entrada | Alta |
| B4 ETF | PENDIENTE | E1 exclusión inicial; E2 soporte; E3 ampliación | H0 bootstrap:169, tipos y gates actuales | ETF excluidos; SPY/QQQ solo benchmarks; inclusión no decidida | Alta |

Los cuatro casos tienen confianza **alta** en esta clasificación. B4 sí resuelve
el motivo histórico: fue una decisión explícita de alcance inicial, no una
incapacidad de representar ETF. «Inicialmente» no fija fecha ni condición automática
de habilitación. El conflicto con la solicitud ampliada sigue requiriendo decisión.

### ETF: capacidad técnica y cambio mínimo pendiente

1. Massive documenta metadata `type` en Ticker Overview y un catálogo de códigos
   `code`/`description` en Ticker Types. Una integración general debe resolver ese
   código contra el catálogo, conservar fecha, mercado e identificadores y mapearlo
   al tipo interno; OHLCV por sí solo no demuestra que un instrumento sea ETF.
   Fuentes oficiales consultadas 15/09/2026: [Overview](https://massive.com/docs/rest/stocks/tickers/ticker-overview),
   [Types](https://massive.com/docs/rest/stocks/tickers/ticker-types).
   No se consultó la API autenticada de metadata ni se acredita ese mapeo como implementado.
2. El proyecto usa `Instrument(symbol, exchange, currency, asset_class, stable_id,
   broker_id)`, distinguiendo common_stock/etf/adr/other. Importador exige asset_class.
   Massive actual asigna AAPL=common_stock, SPY/QQQ=etf por su allowlist; no obtiene
   esa clasificación de un endpoint de metadata. El test A2 prueba ese mapeo local.
3. Existe filtro eToro: EtoroDemoBroker.submit exige common_stock, stable_id/broker_id,
   y _check_eligibility valida producto, compra long sin apalancamiento, permisos,
   unidades, nominal y stop. RiskEngine exige effective_product=common_stock.
   El snapshot histórico enumera ETF en catálogo, pero no prueba elegibilidad de
   un ETF en una cuenta. No hubo lecturas de cuenta o cambios de transporte.
4. Tests actuales: A2 comprueba tipo ETF y datos de benchmarks; test_risk_engine
   rechaza CFD/divisa/eligibilidad no comprobada; test_etoro_adapter cubre
   incompatibilidades de elegibilidad. No se encontró un caso positivo de operar
   ETF ni una especificación documentada que lo autorice.
5. Incluir ETF requeriría al menos modificar las políticas de universo en orb.py,
   producto en risk/engine.py e identidad en brokers/etoro_demo.py; definir mercados
   admitidos (SPY se representa ARCX, hoy excluido por XNYS/XNAS), metadata, mapping
   de símbolos/IDs y tests de elegibilidad. No basta modificar asset_class o el YAML.
   La fórmula ORB/RVOL y la bisección de sizing podrían reutilizarse, pero conservar
   filtros de liquidez, costes y pasos requiere decisión explícita, no extrapolación.
6. Aumentar el universo cambia competidores del top-10, cupo y asignación de riesgo
   incluso sin alterar fórmulas. Operar SPY/QQQ además de usarlos como benchmark
   obliga a definir autorreferencia: RS contra el mismo símbolo sería cero.
   Roles viables son solo benchmark o benchmark+operable, pendientes de aprobación.

## Fuentes e inventario

Se revisaron AGENTS, STATUS, HANDOFF, TASKS, los seis documentos de continuidad,
BOOTSTRAP_SPEC.md, STRATEGY_SPEC.md, RISK_POLICY.md, ORDER_LIFECYCLE.md y ADR 003.
Código: strategies/orb.py y features.py, risk/engine.py, config.py,
data/calendar.py, service.py; lectura del consumidor backtesting/engine.py,
experiments.py y de tests de estrategia/configuración/riesgo. Se localizaron YAML,
TOML y config.schema.json; la única configuración YAML versionada es offline.yaml.

Referencias abreviadas de la tabla (relativas a la raíz):

- S: `src/intraday_etoro_lab/strategies/orb.py`, StrategyConfig y ORBStrategy.
- F: `src/intraday_etoro_lab/strategies/features.py`.
- R: `src/intraday_etoro_lab/risk/engine.py`, RiskConfig/CostConfig/RiskEngine.
- C: `src/intraday_etoro_lab/data/calendar.py`.
- Y: `configs/offline.yaml`; todos los campos strategy/risk/costs están explícitos.
- DS/DR: `docs/STRATEGY_SPEC.md` / `docs/RISK_POLICY.md`.

Los valores siguientes son **efectivos actuales**, no una aprobación de congelación
del alcance ampliado solicitado. El [snapshot JSON](strategy-1-a3-audit.json)
incluye todos los campos, fuentes SHA-256, versión y commit base.

| Regla / parámetro | Valor o condición efectiva; default | Fuente / respaldo |
|---|---|---|
| Versión | ORB_RVOL_v0.1; mismo default | S, Y, DS, ADR 003 |
| Alternativa distinta | ORB_BASE_v0.1 omite filtro RVOL y ordena por liquidez | S, DS; no seleccionada en Y |
| Universo | Solo common_stock USD XNYS/XNAS; ETF/ADR/SPY/QQQ excluidos; literal sin campo YAML | S, DS; R exige producto common_stock |
| Sesión / zona | Regular XNYS, America/New_York; timestamps UTC; DST/festivos/cierres tempranos por calendario fijado | C, DATA_CONTRACTS |
| Premarket | No participa en OR ni warmup/liquidez regular | S, C, DS |
| OR | 5 minutos, literal/default 5; [09:30,09:35) NY | S, Y, DS |
| ORH / ORL / ORO / ORC | max(high), min(low), primer open, quinto close | S.opening_metrics/process_session, DS |
| Warmup | 20 sesiones inmediatamente anteriores completas; búsqueda 60 días calendario, sin saltar sesiones faltantes | S, Y (20), DS |
| Cierre previo | Estrictamente >10 USD; default 10 | S, Y, DS |
| Liquidez | Media de 20 sum(close_minuto*volume_minuto), estrictamente >50.000.000 USD; default 50000000 | S, Y, DS |
| RVOL | V5 actual / media de 20 V5 anteriores, sin volumen posterior ni sesión actual en denominador | S, DS |
| Umbral RVOL | >=2; default 2, ajustable en el modelo existente | S, Y, DS |
| Volumen | consolidated_shares; synthetic_shares solo tests; ajustes no unknown; V5 >0 | S, DATA_CONTRACTS |
| Disponibilidad | Real exige observed; barras final y revision=0, primera llegada; recepción hasta cutoff | S, DS; Massive histórico A2 no pasa este gate |
| Selección | Apertura+5m+2s; espera default 2, rango 0–10s | S, Y, DS |
| Ranking | RVOL descendente, liquidez descendente, símbolo ascendente; máximo 10; sin reselección intradía | S, Y, DS |
| Apertura alcista | ORC > ORO; rango no alcista impide señal, pero ocupa su lugar ya seleccionado | S, DS |
| Breakout | Primera barra final posterior al rango cuyo close > ORH | S, DS |
| Entrada | available_at >=cutoff y <apertura+60m; default 60, rango 6–60 | S, Y, DS |
| Caducidad | available_at+10s; now>=expires_at rechaza; default 10 en estrategia y riesgo | S, R, Y, DS/DR |
| Unicidad | SHA-256(version|fecha|símbolo)[:24]; una señal; persistencia bloquea segunda intención tras rechazo/cancelación/stop | S, ORDER_LIFECYCLE |
| Stop | ORL inicial, entrada estrictamente superior; no ampliación, trailing, take-profit fijo ni salida VWAP | S, R, DS/DR |
| Salida horaria | Cierre de calendario menos 5m, también cierre temprano; ejecución requiere mercado disponible | C.flatten_at, DS, consumidor replay existente |
| Fuerza relativa | Flag Literal[False]; función stock_now/stock_open − benchmark_now/benchmark_open, sin gap nocturno | S, F, Y, DS |
| Política SPY/QQQ | Ninguna selección/uso de benchmark para entradas; A2 evaluó ambos solo como evidencia de datos | F, MASSIVE_A2; **pendiente** |
| Régimen | Flag Literal[False]; no función, indicadores, timeframe, lookback ni umbrales | S, Y, DS; **pendiente** |
| VWAP | Flag Literal[False]; sum(((h+l+c)/3)*v)/sum(v), sesión única, barras final y volumen comprobado positivo | F, Y, DS |
| Confirmación VWAP | No existe comparador, momento de evaluación ni regla de entrada | F, DS; **pendiente** |
| Capital asignado | 10.000 USD virtuales; default 10000 | R, Y, DR |
| Riesgo por trade | <=0,001 del capital efectivo = min(asignado, referencia, equity); default/máximo 0,001 | R, Y, DR |
| Pérdida diaria | Rechazo si realizado+no realizado <=−0,005*capital_referencia; default/máximo 0,005 | R, Y, DR |
| Presupuesto de riesgo | min(capital_efectivo*0,001, referencia*0,005+min(0,PnL)-riesgo_reservado) | R.assess, DR |
| Cupo | Máximo 2 posiciones/intenciones potenciales; UNKNOWN conserva reservas | R, Y, DR, ORDER_LIFECYCLE |
| Exposición | Bruta <=100%; por posición <=60%; efectivo/reservas incluidos | R, Y, DR |
| Sizing | Bisección del mayor múltiplo de unit_step admisible: q*(entrada−stop)+costes<=riesgo, q*entrada+costes<=efectivo; respeta mínimos/máximos | R.assess, DR |
| Spread | (ask−bid)/ask <=0,003; default 0,003 | R, Y, DR |
| Desviación | abs(entrada−referencia)/referencia <=0,005 si referencia presente | R, Y, DR |
| Divergencia fuente | abs(entrada−fuente)/fuente <=0,005 si fuente presente | R, Y, DR |
| Quote | Edad <=3s; no futuro; bid>0, ask>=bid, entrada>=ask | R, Y, DR |
| Instrumento | USD/common_stock, elegibilidad y stop nativo verificados; pasos/límites externos son inputs | R.InstrumentRules, DR |
| Supuestos locales de instrumento | Paso/mínimo 0,001; máximo 1.000.000 unidades; nominal 1–1.000.000 USD; defaults solo simulador | R.InstrumentRules, DR; no evidencia eToro |
| Costes | known=true; fixed/minimum/notional_rate por lado=0; per_unit por lado=0,005; slippage/unidad=0,02; quadratic=0 | R.CostConfig, Y, DR; supuestos sintéticos, no tarifas verificadas |
| Coste total | 2*(fixed+max(minimum,q*per_unit+q*entrada*rate))+q*slippage+quadratic*q² | R.estimate, DR |
| Otras invalidaciones | Datos/Decimal/identidad/reglas inválidos, pausa, reconciliación pendiente, costes desconocidos, cupo/presupuesto agotado, mínimos incompatibles | R._reject_reason/assess |
| Post-fill | Protección ausente o riesgo efectivo >planeado produce incidente; pausar/cancelar/salir propios | R.post_fill_risk, DR, execution/engine.py |

La pérdida máxima es un presupuesto, no una garantía contra gaps o fallos.
La función RS acepta precios elegidos por el llamador: no impone timeframe, lookback,
umbral o criterio de entrada. La función VWAP solo impone sesión única, no selecciona
por sí misma horario regular: A2 le pasó barras regulares. No extrapolar el ejemplo
A2 (primera ventana de cinco minutos) como regla nueva de trading.

## Discrepancias y decisiones necesarias

| ID | Evidencia actual | Información necesaria para cerrar A3 |
|---|---|---|
| B1 RS | Desactivada por bootstrap y ADR; solo función aritmética | Confirmar exclusión de v0.1 o definir SPY/QQQ/ambos, selección, intervalo, lookback, umbral, comparador, evaluación y comportamiento si faltan datos |
| B2 Régimen | Desactivado; no regla ejecutable | Confirmar exclusión o especificar instrumento, indicadores, timeframe, lookbacks, umbrales y régimen válido/no válido |
| B3 VWAP | HLC3 existe; no confirmación de entrada | Confirmar exclusión o definir sesión, precio/barra comparados, operador y momento, reglas de faltantes |
| B4 Universo | Código y riesgo excluyen ETF; solicitud contempla acciones/ETF | Confirmar universo common_stock actual o definir ampliación y reglas de elegibilidad, con implementación/versionado separado |

Autoridad para describir lo vigente: código + YAML + DS/DR + ADR 003 coinciden.
La solicitud nueva gobierna el objetivo A3; la decisión antigua de mantener filtros
inactivos no basta para declarar completa esa solicitud. No se resuelve silenciosamente
tratando requisitos faltantes como NOT_APPLICABLE. Responsable de decisión: usuario.

También se identificó una limitación de congelación: `version` no inmoviliza todos
los valores. StrategyConfig permite otros min_rvol, ventanas, liquidez y esperas
con el mismo identificador. `frozen=True` impide asignaciones sobre un objeto,
no vincula el nombre de versión a un conjunto canónico. A3 necesitará un snapshot
aprobado y prueba de identidad tras resolver B1–B4.

## Carga y reproducción de la auditoría actual

`load_config("configs/offline.yaml")` valida AppConfig; sus objetos strategy/risk/costs
se pasan a ORBStrategy/RiskEngine. No hay factory/registry independiente.
La configuración existente también contiene parámetros de replay; no se copian
a una supuesta versión congelada. Su config_hash identifica AppConfig completo,
incluido runtime/backtest, y no equivale a un hash exclusivo de estrategia.
BOT_MODE y ORDER_SUBMISSION_ENABLED pueden variar el contexto; no cambian strategy/risk.

```powershell
.\scripts\uv.ps1 run --frozen python -c "import json; from intraday_etoro_lab.config import load_config; c=load_config('configs/offline.yaml'); print(json.dumps({k:getattr(c,k).model_dump(mode='json') for k in ('strategy','risk','costs')},indent=2))"
.\scripts\uv.ps1 run --frozen pytest tests/test_strategy_a3_audit.py tests/test_strategy_orb.py tests/test_config_api.py tests/test_risk_engine.py -q
```

Los tests verifican inventario explícito sin defaults ocultos en esas tres secciones,
igualdad contra snapshot, carga determinista, identidad ORB_RVOL y rechazo de activar
extensiones. **No son pruebas de una Strategy 1 congelada aún inexistente.**
No se ejecutan descargas, cuentas, órdenes ni backtest A4.

## Protección A4 y trazabilidad

**A4 consume Strategy 1 congelada; A4 no modifica Strategy 1 para mejorar resultados.**
Cualquier cambio de filtros, umbrales, universo, ORB/RVOL, ventana, RS/régimen/VWAP,
riesgo o entradas/salidas requiere nueva versión y reabrir A3 o tarea equivalente.
A4 permanece pendiente y bloqueada hasta una congelación aprobada y verificada.
No se implementó una arquitectura nueva ni una configuración final provisional.

El commit base no representa el árbol A2 sin commit. Se preservó el diff previo
en runtime/a3-audit/pre-a3.patch y su estado en pre-a3-status.txt. No se crea commit
de congelación mientras A3 siga bloqueado. Los cambios quedan preparados para revisión,
sin staging o publicación y sin mezclar A2 en un commit atribuido exclusivamente a A3.
