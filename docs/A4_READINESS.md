# A4 — replay real reproducible, 2026-09-15

## Resultado actual: A4 DONE, reproducción y verificación PASS

El responsable aprobó explícitamente `replay_as_of_v1`: visibilidad lógica
separada de procedencia. Esta autorización sustituye el bloqueo documental
histórico conservado al final. Contrato e implementación: [REPLAY_AS_OF_V1](REPLAY_AS_OF_V1.md).

Dos ejecuciones consecutivas de Strategy_1 / ORB_RVOL_v1.0 sobre las tres
capturas Massive aprobadas A2 produjeron exactamente las mismas operaciones,
decisiones, equity, métricas y bootstrap. Comparación funcional **PASS**.
Los checks de entrega se registran en [VERIFICATION](VERIFICATION.md).
Suite completa: 658 passed, siete warnings, cero fallos/skips; ocho checks de
entrega PASS. Cobertura 90.641410%, módulos críticos sin reducción.

Resultado: una sesión evaluada, AAPL evaluable, cero operaciones porque
`RVOL_BELOW_THRESHOLD` (RVOL A2 1.085297795818647139199521439 frente al mínimo
congelado 2). SPY/QQQ se excluyen del universo operable y permanecen referencias.
No hay rechazo OBSERVED_AVAILABILITY_REQUIRED en estos runs. Cero costes y
retorno neto 0; Sharpe, win rate y esperanza permanecen null según métricas existentes.
No se modifica la estrategia para obtener señales. Los tests de determinismo
con trades no vacíos son una comprobación de software separada y fabricada.

## Identidad ejecutada

| Campo | Valor |
|---|---|
| Commit base | ed456c32355bea05b5c6e04bc4b889ce8bce8ef3 |
| SHA-256 del árbol efectivo | 5b9fefc95ee1b319425f3172ef7be5418365ce2c734d416e968f092051d25db6 |
| Strategy 1 | ORB_RVOL_v1.0; configs/strategy-1-v1.yaml; strategy_hash e751eb0db5be3f07950d5da5ccda0def4aeee6c03b0da83912ac38ed6beed7cb |
| Snapshot A3 SHA-256 | 3268550aa4e110c29673003262787172f9c6ddaf52bea5af96670372d32579e0 |
| Dataset | docs/massive-a2-manifest.json; AAPL/SPY/QQQ; SHA-256 7605880936ef74ff27ded089af134b6a3538b3d051300ff861a091e5d2da0805 |
| Ventana | 2026-08-14 a 2026-09-14; 20 warmups + objetivo 14/09; 8.190 barras por símbolo |
| Procedencia / disponibilidad | historical_download / replay_as_of_v1, 24.570 cierres efectivos documentados |
| Zona | UTC para eventos/disponibilidad; America/New_York para sesiones |
| Motor | minute-next-open-v1; capital 10000, latency_ms 250, spread_bps 2, slippage_bps 1, seed 42, bootstrap_samples 200, block_sessions 2 |
| Entorno | Python 3.12.12, uv.lock congelado; Decimal local prec=28, ROUND_HALF_EVEN |
| run_id funcional | 1d21808255a75077d902, igual en ambas invocaciones |

Los manifests contienen configuración completa strategy/risk/costs, parámetros
del motor, hashes por archivo fuente y por captura/página. HEAD solo no identifica
el árbol con cambios A2/A3/A4 sin commit. Se comprobó identidad de código antes
y después de cada run, y hashes raw/A3 nuevamente antes de persistir.

## Comandos exactos ejecutados

```powershell
.\scripts\uv.ps1 run --frozen python scripts/run_a4.py run --output runtime/a4-replay/run-1
.\scripts\uv.ps1 run --frozen python scripts/run_a4.py run --output runtime/a4-replay/run-2
.\scripts\uv.ps1 run --frozen python scripts/run_a4.py compare runtime/a4-replay/run-1/1d21808255a75077d902.json runtime/a4-replay/run-2/1d21808255a75077d902.json --output runtime/a4-replay/comparison.json
```

Los tres comandos devolvieron exit 0. Para repetir se requieren directorios y
archivo de comparación nuevos; no sobrescribir los existentes.

## Artefactos y comparación

- `runtime/a4-replay/run-1/1d21808255a75077d902.json`:
  SHA-256 536d74807e97ffc0bc35dd3afcc9d00af3f200d072ecade1c012c0d863436ed8.
- `runtime/a4-replay/run-2/1d21808255a75077d902.json`:
  SHA-256 35aaa621a5672a02407c74b64d163544bc46ec27cb738a2baf74c169b6203569.
- Cada directorio incluye availability.jsonl, experiments.jsonl y HTML del
  escritor existente. Availability tiene SHA-256 idéntico
  475d6ad94d3684f1163b96b0eabc76c5f1c30e8dd0eac110a159ce83c0b14839.
- `runtime/a4-replay/comparison.json`: funcional/trades en orden/summary **true**.
  Huella funcional común:
  03e898ccdb57c6b863656bece41ddaec4b30cdbe682abea593f4f37defef85be.
- Solo se excluyen run_metadata.execution.started_at y finished_at.
  El resto del resultado completo debe coincidir, incluido run_id y metadatos
  de identidad. Los JSON completos difieren por las horas informativas.

No se editaron código/configuración/dataset entre ambas ejecuciones. Raw y
artefactos locales siguen ignorados por Git; otra máquina necesita las capturas
autorizadas con esos mismos hashes. No se realizaron descargas nuevas, cuentas,
órdenes externas, tuning, commits o publicación.

## Archivos de implementación y decisiones

- `backtesting/replay.py`: registros originales y vistas observed por reloj;
  prioridad de disponibilidad, lotes atómicos, selección y terminales inmutables.
- `backtesting/engine.py`: boundary opcional, identidad temporal, run_metadata;
  closes/stops no procesados antes de disponibilidad ni después del cierre de
  la sesión evaluada. La ruta sin boundary mantiene su contrato previo.
- `backtesting/a4.py`, `scripts/run_a4.py`: validación pin A2/A3, agregación de
  capturas, manifiesto extendido y persistencia/comparación sin fallback.
- `tests/test_replay_as_of.py`: contratos temporales y persistencia; pruebas
  fabricadas explícitamente separadas del resultado real.
- Documentación: REPLAY_AS_OF_V1, A4_READINESS, ARCHITECTURE, BACKTEST_PROTOCOL,
  system_context, changelog, decisions, pending_tasks, VERIFICATION y continuidad
  STATUS/HANDOFF/TASKS. Snapshots/YAML/fuentes congeladas A3 intactos.

La disponibilidad al cierre es un modelo autorizado, no la publicación real
observada en vivo. Se conserva la limitación de instantánea histórica ajustada y
posibles correcciones, sin afirmar ausencia de revisiones del proveedor. Esto
valida infraestructura y reproducibilidad; no demuestra rentabilidad o aptitud Demo.

# Antecedente — inspección BLOCKED anterior a la autorización temporal

## Resultado

No se implementó ni se declara aprobado el backtest A4. La inspección identifica
una incompatibilidad estructural entre el dataset aprobado A2 y el contrato
congelado A3. Se aplica la instrucción de detener la expansión, documentar el
bloqueo y proponer el cambio mínimo sin implementarlo fuera de A4.

A2 sigue CLOSED para validación de datos y A3 sigue DONE para su hipótesis
congelada. Estos cierres no demuestran compatibilidad para replay histórico.

## Identidades verificadas

- Base Git: `ed456c32355bea05b5c6e04bc4b889ce8bce8ef3`. El árbol contiene
  modificaciones A2/A3 previas sin commit; ese commit solo no identifica el código.
- Strategy_1 / `ORB_RVOL_v1.0`, configuración `configs/strategy-1-v1.yaml`.
  Snapshot `docs/strategy-1-a3-audit.json`: configuración efectiva, fuentes SHA-256
  y strategy_hash `e751eb0db5be3f07950d5da5ccda0def4aeee6c03b0da83912ac38ed6beed7cb`.
  Se verificaron igualdad efectiva y todos los hashes de fuentes del snapshot.
- Dataset: `docs/massive-a2-manifest.json`, AAPL con SPY/QQQ de referencia;
  objetivo 2026-09-14, veinte sesiones previas desde 2026-08-14.
  Cada captura local coincide con el SHA-256 aprobado de capture.json y de cada
  página raw; el lector devuelve 8.190 barras regulares por símbolo,
  `NETWORK_HTTP`, `synthetic=false`, `availability_kind=historical_download`.
- Evidencia local: `runtime/a4-readiness/evidence.json`. Incluye huella SHA-256
  de src/configs/pyproject/lock/versión Python, hashes A2/A3, configuración efectiva,
  parámetros del backtest no ejecutados, Python y contexto Decimal.

Esta comprobación verifica integridad local respecto de A2; no realiza una nueva
verificación externa ni convierte provenance local en firma del proveedor.

## Bloqueo exacto

1. `data/massive.py::MassiveHistoricalProvider` conserva la recepción HTTP real
   como received_at y available_at, y el manifiesto como historical_download.
   Las capturas llegaron el 15 de septiembre, después de la sesión objetivo del 14.
2. `strategies/orb.py::ORBStrategy.process_session` rechaza cualquier instrumento
   real cuya disponibilidad no sea observed con `OBSERVED_AVAILABILITY_REQUIRED`,
   antes de calcular universo, warmup, ORB, RVOL o RS.
3. El diagnóstico cargó cada una de las tres capturas aprobadas por separado y
   llamó a Strategy 1 congelada: los tres resultados contienen ese rechazo y
   ninguna señal. Son comprobaciones del bloqueo por captura; no constituyen un
   backtest multiinstrumento ni una comparación de dos runs A4.
4. `backtesting/engine.py::run_backtest` utiliza esa misma estrategia y clasifica
   los datos no observed como `RESEARCH_BLOCKED_DATA`. Un reporte sin operaciones
   por este rechazo no sería un backtest válido según BACKTEST_PROTOCOL.
5. Cambiar solo la etiqueta no basta: las barras seguirían llegando después del
   cutoff y no satisfarían warmup/apertura/RS causales. Retrofechar esas recepciones
   falsificaría la evidencia y alteraría el contrato congelado.

No se modifican la estrategia, parámetros, snapshots, raw, proveedores, motor,
riesgo, eToro ni guardas. No se usa fixtures como evidencia A4.

## Inventario del motor y persistencia existente

| Archivo | Función relevante |
|---|---|
| `backtesting/engine.py` | BacktestConfig, BacktestResult, run_backtest; mismo ORBStrategy/RiskEngine; fill al open estrictamente posterior |
| `backtesting/metrics.py` | portfolio_metrics y bootstrap por sesiones con random.Random(seed) |
| `backtesting/experiments.py` | append_experiment: registro JSONL append-only con identidad y métricas; controlled_comparison queda fuera de A4 |
| `service.py` | load_bundle: selección explícita de proveedor; save_report: resultado completo JSON/HTML con control de colisiones; _run_research enlaza los componentes |
| `data/providers.py` | DataBundle: instrumentos, barras, manifiesto, sesiones evaluadas |
| `data/massive.py` | Un DataBundle por captura/instrumento; lector offline con hashes, sin fallback |
| `tests/test_backtest_replay.py` | Determinismo, next-open, costes, TTL, métricas; datos sintéticos únicamente para regresión |
| `tests/test_strategy_v1.py`, `tests/test_strategy_a3_audit.py` | Identidad y reglas congeladas A3 |
| `tests/test_massive_a2.py` | Contrato y auditoría A2; no prueba una adquisición nueva |

BacktestResult ya contiene trades ordenados, decisions, signals, equity,
rejections, incidents, metrics y bootstrap. Los trades son diccionarios con
signal_id, symbol, session, submitted_at, entry_at, exit_at, units, precios de
entrada/salida/stop, exit_reason, net_pnl, planned_risk, r_multiple, costes,
fees, spread_slippage y turnover. No hace falta inventar un modelo alternativo.

## Inspección de determinismo y propuesta A4 diferida

El run_id actual deriva de datos/configuración/calendario/commit; la configuración
se serializa con claves ordenadas. La estrategia ordena instrumentos y ranking;
el motor ordena eventos por tiempo, prioridad, ranking y símbolo. Duplicados de
primeras barras dependen del orden de llegada: la ruta A4 deberá conservar el orden
canónico y rechazar duplicados/ambigüedades mediante las validaciones existentes.
No hay concurrencia ni reloj de pared en la generación de operaciones observada.
Bootstrap usa generador local con semilla fija. Decimal y métricas float requieren
registrar entorno y dependencias; no se afirma igualdad entre plataformas distintas.

Tras resolver el contrato temporal, el cambio mínimo A4 sería agregar las tres
capturas verificadas a un DataBundle sin alterar sus campos, extender mínimamente
BacktestResult/save_report para configuración efectiva, identidades A2/A3 y huella
del código, y persistir cada ejecución en un directorio nuevo. Reutilizar JSON/JSONL;
no crear otro registro de runs. Añadir pruebas de identidad, rechazos de fuente,
persistencia y comparación exacta de trades (incluido orden), metrics y bootstrap.

La fecha/hora de ejecución y el identificador de invocación serían metadata
informativa excluida de la comparación; timestamps de señales, envíos, entradas
y salidas nunca se excluyen. Hoy no hay tal comparación implementada ni aprobada.
La identidad del código debe incluir el árbol real, no solo HEAD del árbol sucio.

## Cambio mínimo necesario fuera del alcance actual

Responsable: propietario del contrato de investigación A2/A3. Primero decidir
explícitamente si se permite replay con disponibilidad **modelada**, diferenciada
de recepción observada. Si se decide permitirlo, especificar/versionar ese contrato
y sus pruebas causales en una tarea separada; preservar raw/recepciones originales
y prohibir que habilite shadow o Demo. La versión congelada actual no ofrece ese
contrato y A4 no lo introduce mediante un bypass o una copia alterada del bundle.

La alternativa para conservar el contrato observed es aprobar un dataset con
evidencia contemporánea compatible; sería una nueva referencia aprobada, no los
mismos históricos A2. Descargar nuevamente las barras no recupera su disponibilidad
histórica. Ninguna de estas alternativas se implementó ni se aprobó aquí.

## Comandos y evidencia

```powershell
.\scripts\uv.ps1 run --frozen python runtime/a4-readiness/check_readiness.py
.\scripts\uv.ps1 run --frozen pytest -q tests/test_backtest_replay.py tests/test_strategy_v1.py tests/test_strategy_a3_audit.py tests/test_massive_a2.py --junitxml=runtime/a4-readiness/tests.xml
```

El diagnóstico escribe evidence.json con creación exclusiva; para repetirlo debe
usarse una ubicación de salida nueva. Script y evidencia permanecen locales bajo
runtime ignorado. Su primer intento como inspect.py falló antes de cargar datos
por colisión con el módulo estándar inspect; se renombró check_readiness.py y
la ejecución corregida pasó. No hubo cambios de dependencias ni código productivo.

Resultados exactos de pruebas y preservación: `docs/VERIFICATION.md`.
No hay primer/segundo artefacto de backtest A4; comparación funcional
`NOT_DEMONSTRATED`. A4 permanece **BLOCKED**, con fases 2–5 y aceptación pendientes.
