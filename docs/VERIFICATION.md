## A7 WebSocket: verificacion final del spike (2026-09-16)

23 tests del spike PASS; 165 focales WebSocket/A6/A7 PASS (5 warnings).
Suite completa: 905 passed, 7 warnings, cero fallos/errors/skips; 16/16 gates
PASS con scripts/verify.py y codigo inmutable durante checks. Secret scan:
193 archivos, 0 hallazgos; git diff --check exit 0; inspector Strategy 1 PASS.
52 archivos src/configs/lock/snapshot/pyproject preservados contra baseline.
El primer gate detecto dos fallos del aislamiento monkeypatch del test nuevo;
se corrigieron y se repitieron focales y todos los gates. Evidencia inicial
se conserva, evidencia final: runtime/a7-websocket/verification.json.
No demuestra viabilidad WebSocket: handshake HTTP 403 del proxy EPM, cero
eventos y cero mutaciones; A7 PARTIAL/BLOCKED. Detalle: A7_WEBSOCKET.md.

# Evidencia de verificación local

Validacion final de esta auditoria: 861 tests PASS, 7 warnings; 16/16 gates PASS.
142 focales A7/A6 PASS; secret scan 187 archivos / 0 hallazgos; diff check 0.
Strategy 1/riesgo/runner A6/config/lock preservados por hashes. Evidencia exacta
en runtime/a7-quote-audit/verification.json y acceptance.json.

## A7 — auditoria UTC/costes, PARTIAL/BLOCKED (2026-09-16)

La evidencia anterior era 81.588043 s, no 81588 s; ambiguedad de coma decimal.
Dos GET rates nuevos confirmaron retrasos de 35.860831 y 75.107782 s.
Recepcion HTTP registrada antes del parseo, UTC aware; limite 3 s intacto.
Costes value/amount normalizados dentro del adapter; fixture real sanitizado.
142 pruebas focales A7/A6 PASS. Gate externo QUOTE_STALE_OR_DELAYED;
cero ordenes/mutaciones; identidad DEMO y parser de costes PASS.
No se habilita el vertical de trading mientras falle frescura. No A8.
Detalle, cambios, comandos y evidencia: [auditoria A7](A7_QUOTE_COST_AUDIT.md).


## A7 — continuación verificada, 2026-09-16T14:45:18.340310+00:00

Estado A7 PARTIAL/BLOCKED; cero mutaciones. Lecturas externas sí observadas:
Demo/scopes/elegibilidad/what-if; quote obsoleta 81.588043s >3s impidió el envío.
No confundir diagnóstico con aceptación open/reconcile/close/reconcile.

- Baseline: `.\scripts\uv.ps1 run --frozen pytest tests/test_demo_only_identity.py tests/test_demo_session.py tests/test_etoro_adapter.py tests/test_etoro_transport.py tests/test_execution_engine.py tests/test_persistence_recovery.py -q`:
  exit 0, 383 passed, 5 warnings, 27.64s. Repetición tras preparación: 383 passed,
  5 warnings, 25.32s; cero fallos/skips en ambas.
- `.\scripts\uv.ps1 run --frozen pytest tests/test_demo_pre_send.py -q`:
  exit 0, 20 passed, 3.15s. Rechazos y reservas, errores ambiguos/no retry,
  crash/restart/correlación, quote UTC y previews confinados.
- `.\scripts\uv.ps1 run --frozen python scripts/verify.py`: exit 0,
  **16/16 PASS**, 842 passed, 7 warnings in 158.10s (0:02:38). Cero errores/fallos/skips; 39 A6 y 84 A7 PASS.
  Ruff check/format, mypy 47 fuentes, build, cobertura, secretos y recorridos
  offline PASS. Las CLI conectadas conservan rechazo esperado exit 2.
- Código estable durante los gates: true; SHA-256 `ca0a4fa44392bda3fcfb565895cceac804038273015c51afaae1b2a0a7c29b31`.
- Cobertura total 91.520566%; transporte 98.879552%, autorización 99.206349%,
  ejecución 94.767442%, modelos 100%; todos los módulos críticos >=90.
- `.\scripts\uv.ps1 run --frozen python scripts/inspect_strategy_v1.py`: PASS,
  source_hashes_match=true; Strategy 1 conserva
  `e751eb0db5be3f07950d5da5ccda0def4aeee6c03b0da83912ac38ed6beed7cb`.
- Secret scan: 184 candidatos, cero hallazgos. git diff --check exit 0.

Evidencia cruda de gates: runtime/a7-completion/verification.json. Evidencia
combinada actualizada: runtime/a7/verification.json, con A7_acceptance=BLOCKED
y provider IDs null. Versión anterior preservada en prior-verification.json.
Detalles de estados, red, contratos y límites: [continuación](A7_COMPLETION_ATTEMPT.md).
Sin cambios .env, Strategy 1, riesgo, A6, schema SQLite, configuración o lock;
sin commits/publicación. La preparación del ejecutor sí cambió, explícitamente.

## A7 — validación final parcial, 2026-09-16T14:11:45.950641+00:00

Estado funcional: PARTIAL / ejecución externa BLOCKED. No DEMO_WRITE_VERIFIED.

- Baseline antes de editar: `.\scripts\uv.ps1 run --frozen pytest tests/test_demo_session.py tests/test_etoro_adapter.py tests/test_etoro_transport.py tests/test_execution_engine.py tests/test_persistence_recovery.py tests/test_risk_engine.py -q`:
  exit 0, 364 passed, 5 warnings, 29.95s, cero fallos.
- Incremento bróker/preflight: `.\scripts\uv.ps1 run --frozen pytest tests/test_etoro_adapter.py tests/test_etoro_transport.py tests/test_demo_preflight.py tests/test_phase2_broker.py -q`:
  exit 0, 235 passed, 1 warning, 4.83s. Cinco fallos introducidos por adelantar
  lecturas a validaciones locales se corrigieron en código; no se relajaron asserts.
- Nuevas pruebas aisladas antes de los tres últimos casos de IDs ambiguos:
  `.\scripts\uv.ps1 run --frozen pytest tests/test_demo_only_identity.py -q`:
  exit 0, 61 passed, 1 warning, 4.42s. Total final A7 en suite completa: 64 PASS.
- Gate final `.\scripts\uv.ps1 run --frozen python scripts/verify.py`: exit 0,
  **16/16 PASS**; 822 passed, 7 warnings in 158.17s (0:02:38). Cero errores/fallos/skips. A6: 39 PASS.
  Incluye contratos unitarios, integración local SQLite/Executor/RiskEngine/adapter,
  regresiones, Ruff check/format, mypy 47 fuentes, cobertura, secretos, build,
  recorridos offline y CLI conectada bloqueada con sus exits esperados.
- Primera ejecución del colector: 15/16, fallo de formato por finales de línea
  mixtos; árbol editado durante esa ronda. NO se usa como evidencia final.
  Se conserva en runtime/a7/verification-first-pass.json; formato corregido y
  colector completo repetido sobre código estable.
- Código final sin cambios durante checks: true; SHA-256 `9ebb719c4cd3e3406105007fce35a0fc8f6df976513de78bc3b93f0d2fb558d7`.
- Cobertura total 91.493740%; identity.py 99%, transport.py 98.837209%,
  session.py 95.180723%. Gate crítico >=90 PASS; transporte antes A6 99.34%,
  se informa la variación, no se afirma ausencia de descenso de cobertura.
- `.\scripts\uv.ps1 run --frozen python scripts/inspect_strategy_v1.py`:
  PASS, source_hashes_match=true, hash de estrategia
  `e751eb0db5be3f07950d5da5ccda0def4aeee6c03b0da83912ac38ed6beed7cb`.
- Escaneo final: 182 candidatos, cero secretos; git diff --check exit 0.
  Comparación inicial/final de 19 archivos core/config/lock: todos idénticos.

Evidencia: runtime/a7/verification.json, baseline-tests.json, preserved-core.json
y final-review.json. Sin consultas de cuenta, mutaciones externas, credenciales
nuevas, cambios .env, commits ni publicación. Contratos oficiales consultados
solo como documentación; [alcance/DoD/bloqueos](A7_DEMO_ONLY.md).

## A6 — gates, recorridos locales y revisión, 2026-09-16

**PASS / SIMULATED_ONLY**. Python 3.12.12 y lock preservados. Verificación completa
terminada a 2026-09-16T13:23:34.554154+00:00; código estable durante checks.
SHA-256 efectivo `1821516c468340c9cade64b2fd96b5e6c61fb97e640715955354a300db667e3c`.
Evidencia exacta conservada en runtime/a6/verification.json, runtime/test-results.xml
(y cobertura en runtime/coverage.json). No commit/publicación.

| Comando/check | Resultado exacto |
|---|---|
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_demo_session.py` | Primera fase: 28 passed, 5 warnings, 16.65s; exit 0 |
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_demo_session.py tests/test_execution_engine.py tests/test_persistence_recovery.py tests/test_risk_engine.py tests/test_strategy_v1.py --junitxml=runtime/a6/focal.xml` | Focal/regresión: 276 passed, 5 warnings, 30.50s; exit 0. Después se añadió el caso de presupuesto virtual insuficiente, incluido en la suite completa |
| `.\scripts\uv.ps1 run --frozen python scripts/verify.py` | Exit 0, 16/16 gates PASS; credenciales retiradas de hijos |
| pytest dentro de verify.py, cobertura y JUnit | 758 passed, 7 warnings, 192.75s; cero errores/fallos/skips; 39 casos A6 incluidos |
| Ruff check / format --check / mypy src | Exit 0 / 0 / 0, 46 módulos fuente |
| Cobertura total líneas+ramas | 91.411683%; session.py 95.18%, session_inputs.py y session_fixture.py 100% |
| Cobertura crítica | riesgo 100%, transporte 99.34%, autorización 99.20%, ejecución 95.31%, modelos 100%, persistencia 95.27% |
| scan_secrets.py | Exit 0, cero hallazgos |
| doctor / data validate / demo-offline / backtest | Exit 0; offline |
| preflight sin claves / run etoro_demo / run live | Exit 2 esperado; bloqueos conservados |
| uv sync --frozen --offline / build --offline / sintaxis JS | Exit 0 |
| `.\scripts\uv.ps1 run --frozen python scripts/inspect_strategy_v1.py` | Exit 0, PASS, source_hashes_match=true |

Recorridos de CLI A6 ejecutados, todos exit 0:

```powershell
.\scripts\uv.ps1 run --frozen python scripts/run_a6.py --database runtime/a6/accepted-1.sqlite --report runtime/a6/accepted-1.json
.\scripts\uv.ps1 run --frozen python scripts/run_a6.py --database runtime/a6/accepted-2.sqlite --report runtime/a6/accepted-2.json
.\scripts\uv.ps1 run --frozen python scripts/run_a6.py --scenario no-signal --database runtime/a6/no-signal.sqlite --report runtime/a6/no-signal.json
.\scripts\uv.ps1 run --frozen python scripts/run_a6.py --database runtime/a6/accepted-1.sqlite --report runtime/a6/accepted-1-retry.json
```

Aceptados: 1 señal, 2 intenciones (entrada+cierre), flat=true, reconciled=true,
entries_armed=false. Sin señal: 0 señales/0 intenciones, flat/reconciled=true.
Comparación funcional, órdenes y todas las tablas durables salvo audit coinciden
entre bases independientes; el retry conserva resultado y órdenes. Audit mantiene
sus timestamps operativos: no son datos financieros ni tiempos de señales.
Seis comprobaciones PASS en runtime/a6/comparison.json. Cero IO externo; todos los
resultados etiquetados SIMULATED, A7 NOT_IMPLEMENTED. No beneficios reales atribuidos.

Revisión de cambios: cinco nuevos archivos código/tests; huella de todos los archivos
previos exactamente igual a la de A5. Evidencia runtime/a6/prior-work-review.json.
Escaneo final tras documentación: 179 candidatos, cero hallazgos; git diff --check
exit 0. Revisión propia de fronteras, UNKNOWN/reservas, orden durable y causalidad.
Sin cambios a Strategy 1, riesgo, ejecutor, store, eToro, datos A2–A4, configs o lock.
El diff global conserva trabajo previo sin commit; no se atribuye todo a A6.
Diseño, siete casos y riesgos externos pendientes en [A6_SESSION](A6_SESSION.md).

## A5 continuación — carga .env y PASS externo, 2026-09-16

Corrección exclusivamente operacional/documental: uv --env-file .env antes del
proceso Python. Ambas claves PRESENT; .env preservado, sin código/dependencias
nuevos. CLI real no instrumentada a las 12:55:35.171934Z: exit 0, overall PASS,
identidad Demo, 16 scopes, credit virtual y AAPL/1001. Tres GET, HTTP 200/200/200,
ninguna mutación. Evidence: runtime/a5-preflight/demo-read-verified.json.
Comando exacto:

```powershell
.\scripts\uv.ps1 run --frozen --env-file .env bot etoro preflight --read-only --config configs/strategy-1-v1.yaml --evidence runtime/a5-preflight/demo-read-verified.json
```

Antes, el comando pedido con UV_ENV_FILE=.env en el lanzador produjo
ETORO_READ_UNAVAILABLE, exit Python 2 (wrapper 1), tres intentos GET y ningún HTTP.
La instrumentación diagnóstica posterior conservó solo clases/códigos de error:
ConnectError/ConnectionRefusedError, WinError 10061. Con ejecución externa
autorizada, el mismo servicio pasó; después se confirmó con CLI sin instrumentación.
TLS y CA local conservados. Sin cambios de proxy, ajustes globales ni .env.

| Check de esta continuación | Resultado |
|---|---|
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_demo_preflight.py tests/test_etoro_adapter.py tests/test_etoro_transport.py tests/test_corporate_network.py tests/test_e2e_http.py --junitxml=runtime/a5-preflight/env-followup-tests.xml` | 202 passed, 7 warnings, 8.35s; exit 0; cero fallos/errores/skips |
| Ruff check . / Ruff format --check . | Exit 0 / 0 |
| mypy src | Exit 0 |
| scripts/inspect_strategy_v1.py | Exit 0; PASS y source_hashes_match=true |

Resultados exactos en runtime/a5-preflight/env-followup-checks.json y JUnit.
No se repitió la suite completa porque no cambió código; se conserva evidencia
anterior de 719 passed y 16/16 gates. No se presenta un mock como conexión real.
Escaneo final: 173 candidatos Git, cero hallazgos; comparación exacta contra ambas
claves también cero, tanto en candidatos como en el reporte final. Diff revisado y
git diff --check exit 0. Huella de código/configuración/tests/scripts idéntica a la
suite completa anterior (code_unchanged_since_full_gates=true). Revisión local:
runtime/a5-preflight/final-followup-review.json. Sin staging, commit o publicación.
Detalle de nueve comprobaciones de carga y criterios: [A5](A5_PREFLIGHT.md).
Las notas A5 pendiente inferiores son antecedentes superados por este PASS.

## A5 — preflight Demo read-only, 2026-09-16

Estado: software local verificado; A5 pendiente de PASS externo con claves propias.
Python 3.12.12, uv.lock conservado. Código estable durante todos los checks.
SHA-256 efectivo: `e28c776d913edb6db91a04b70a2045c63de99bf18e14fd19510fb5bc13f938ec`.
Evidencia exacta local: runtime/a5-preflight/verification-20260916.json,
runtime/test-results.xml y runtime/coverage.json. Sin commit nuevo.

| Comando | Resultado exacto |
|---|---|
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_demo_preflight.py tests/test_etoro_adapter.py tests/test_etoro_transport.py tests/test_e2e_http.py` | Primer pase: 193 passed, 7 warnings, 18.01s; exit 0. Después se añadió el caso JSON duplicado, incluido en la suite completa |
| `.\scripts\uv.ps1 run --frozen python scripts/verify.py` | Exit 0; 16/16 PASS; credenciales retiradas de procesos hijos |
| pytest con cobertura y JUnit, dentro de verify.py | 719 passed, 7 warnings, 127.99s; 0 fallos/errores/skips; incluye 61 casos A5 nuevos |
| Ruff check / format --check / mypy src | Todos exit 0; mypy 43 archivos |
| Cobertura de líneas y ramas | Total 91.131387%; crítica: riesgo 100%, transporte 99.34%, autorización 99.20%, ejecución 95.31%, modelos 100%, persistencia 95.27% |
| scan_secrets.py | Exit 0, ningún hallazgo |
| doctor / data validate / demo-offline / backtest | Exit 0, recorridos offline |
| preflight sin claves / run etoro_demo / run live | Exit 2 esperado, bloqueos preservados |
| uv sync --frozen --offline / build --offline / sintaxis JS | Exit 0 |
| `.\scripts\uv.ps1 run --frozen python scripts/inspect_strategy_v1.py` | Exit 0, PASS; source_hashes_match=true, Strategy 1 congelada preservada |
| Escaneo final tras documentación / `git diff --check` | Exit 0; 173 archivos candidatos, cero secretos; diff sin errores de whitespace |

Preflight con entorno real: ambas variables ETORO_API_KEY/ETORO_USER_KEY ausentes.
2026-09-16T12:38:58.942252+00:00, exit Python 2,
CREDENTIALS_MISSING_OR_INVALID, cero solicitudes y cero mutaciones. Resultado en
runtime/a5-preflight/process-evidence-20260916.json; comando y exit capturados en
process-result-20260916.json. El wrapper PowerShell del primer intento reportó 1;
se registró por separado el exit real del proceso Python, 2. Ningún PASS externo.

Comando para completar la validación, con ambas claves Demo Read en el entorno y
un archivo de evidencia nuevo:

```powershell
.\scripts\uv.ps1 run --frozen bot etoro preflight --read-only --config configs/strategy-1-v1.yaml --evidence runtime/a5-preflight/demo-read.json
```

Revisión propia: allowlist de tres GET antes del transporte, REAL/UNKNOWN fallan,
redirecciones/JSON ambiguo rechazados; sin rutas reales, órdenes ni A6. No hubo
staging, commit o publicación. El diff global contiene cambios anteriores A2–A4;
la entrega A5 añade únicamente servicio/preflight, transporte, CLI, tests y docs.
Diseño, contrato y limitaciones: [A5_PREFLIGHT](A5_PREFLIGHT.md).

## A4 — replay_as_of_v1 y reproducción real, 2026-09-15

Autorización temporal explícita del responsable aplicada en el boundary, sin
modificar Strategy 1. Base HEAD ed456c32355bea05b5c6e04bc4b889ce8bce8ef3;
SHA-256 de código/configuración/tests/scripts/lock efectivo:
5b9fefc95ee1b319425f3172ef7be5418365ce2c734d416e968f092051d25db6.
Python 3.12.12. No se creó commit ni se atribuye el árbol actual solo a HEAD.

### Checks por fases anteriores a ejecutar A4 real

| Comando | Resultado |
|---|---|
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_replay_as_of.py tests/test_backtest_replay.py tests/test_strategy_a3_audit.py` | Exit 0; primer boundary 20 passed, 5 warnings, 53.10s; log temporal-tests.log |
| Mismo comando con `--junitxml=runtime/a4-readiness/phase2-tests.xml` | Exit 0; persistencia/comparación 24 passed, 5 warnings, 66.02s; phase2-tests.log |
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_replay_as_of.py --junitxml=runtime/a4-readiness/boundary-final.xml` | Exit 0; 13 passed, 5 warnings, 64.24s; boundary-final.log |
| `.\scripts\uv.ps1 run --frozen ruff check .` | Exit 0, PASS |
| `.\scripts\uv.ps1 run --frozen ruff format --check .` | Exit 0, 146 archivos formateados |
| `.\scripts\uv.ps1 run --frozen mypy src` | Exit 0, 42 archivos fuente |

Los logs focales están en runtime/a4-readiness. Las 13 pruebas nuevas cubren
visibilidad inclusiva, ausencia de leakage lógico, fuentes preservadas,
publicación explícita prioritaria, contrato ausente, orden, rechazo terminal RS,
futuras publicaciones fuera de sesión, trades no vacíos y persistencia/igualdad.
Inputs fabricados únicamente para contratos; las capturas A2 no se copian a fixtures.
Durante desarrollo Ruff detectó tres líneas largas y luego una firma larga/orden
de imports en el test; corregidos antes de la batería final y los runs reales.

### Dos ejecuciones reales consecutivas

```powershell
.\scripts\uv.ps1 run --frozen python scripts/run_a4.py run --output runtime/a4-replay/run-1
.\scripts\uv.ps1 run --frozen python scripts/run_a4.py run --output runtime/a4-replay/run-2
.\scripts\uv.ps1 run --frozen python scripts/run_a4.py compare runtime/a4-replay/run-1/1d21808255a75077d902.json runtime/a4-replay/run-2/1d21808255a75077d902.json --output runtime/a4-replay/comparison.json
.\scripts\uv.ps1 run --frozen python runtime/a4-replay/check_preservation.py
```

Todos exit 0. Comparación PASS: trades ordenados, summary y resultado funcional
completo iguales. Solo se excluyen started_at/finished_at de metadata de ejecución.
La configuración/código/dataset no cambió entre runs; la preservación final confirma
que el código entregado coincide con ambos manifests. A2/A3/raw y fuentes congeladas
intactos. Entre fuentes existentes solo cambia backtesting/engine.py; se añaden
backtesting/replay.py y a4.py. Transporte, bróker, reservas, propiedad, recuperación,
riesgo y modelos no se modifican. Revisión propia; no se delegó.

Una sesión AAPL evaluable, cero operaciones por RVOL_BELOW_THRESHOLD. SPY/QQQ
reference-only; ningún OBSERVED_AVAILABILITY_REQUIRED. Artefactos/hashes y límites
en [A4_READINESS](A4_READINESS.md), contrato en [REPLAY_AS_OF_V1](REPLAY_AS_OF_V1.md).
No hay nueva adquisición externa o mutación de cuentas; provenance sigue histórico.

### Verificación global de entrega

**PASS: 8/8 checks**, código sin cambios durante la batería. Suite completa:
**658 passed**, siete warnings de deprecación, cero errores/fallos/skips,
391.89s. Ruff check/format, mypy (42 fuentes), inspector A3, secret scan
(170 candidatos, cero hallazgos), demo-offline y backtest legacy: exit 0.
Cobertura total líneas+ramas 90.64141035258815%; los seis módulos críticos
conservan exactamente su cobertura A3: riesgo 100%, transporte 99.267399%,
autorización 98.4%, ejecución 95.3125%, modelos 100%, persistencia 95.270270%.

Salida estructurada: runtime/a4-replay/validation/verification.json, checks.json,
coverage.json, tests.xml y logs individuales. No se atribuye la batería de ocho
checks a los dieciséis del script global histórico; se ejecutaron los checks
pertinentes y las rutas offline en estado nuevo, sin preflights de cuentas o build.

Comando: `.\scripts\uv.ps1 run --frozen python runtime/a4-replay/validate_delivery.py`.
El script registra comandos exactos, salidas, tiempos, cobertura y huella en
runtime/a4-replay/validation. Retira credenciales de todos los procesos hijos.
Usa estado/reportes nuevos para demo-offline y backtest de regresión v0.1;
esa simulación fabricada está separada de los dos runs A4 reales.

Equivalentes reproducibles con el lanzador local; el colector usó el intérprete
3.12.12 del entorno frozen y registra sus comandos literales en checks.json:

```powershell
.\scripts\uv.ps1 run --frozen pytest -q --cov=intraday_etoro_lab --cov-branch --cov-report=json:runtime/a4-replay/validation/coverage.json --junitxml=runtime/a4-replay/validation/tests.xml
.\scripts\uv.ps1 run --frozen bot demo-offline --config runtime/a4-replay/validation/offline.yaml
.\scripts\uv.ps1 run --frozen bot backtest --config runtime/a4-replay/validation/offline.yaml
```

El colector ejecutó los módulos equivalentes con sys.executable, retirando las
credenciales y registrando la ruta absoluta/argumentos exactos en checks.json.
La configuración local de regresión cambia solo rutas de estado/reportes v0.1;
no es la configuración de los runs A4 ni altera el YAML congelado.

## A4 — diagnóstico BLOCKED, 2026-09-15

Base HEAD ed456c32355bea05b5c6e04bc4b889ce8bce8ef3; cambios previos A2/A3
preservados. No hay implementación productiva A4 ni dos runs de backtest.
Python 3.12.12, uv local, lock congelado. Informe: [A4_READINESS](A4_READINESS.md).

| Comando exacto | Resultado |
|---|---|
| `.\scripts\uv.ps1 run --frozen python runtime/a4-readiness/check_readiness.py` | Exit 0; hashes A2 y congelación A3 PASS; A4_BLOCKED_AVAILABILITY_CONTRACT |
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_backtest_replay.py tests/test_strategy_v1.py tests/test_strategy_a3_audit.py tests/test_massive_a2.py --junitxml=runtime/a4-readiness/tests.xml` | Exit 0; 63 passed, 5 warnings, 24.06s; cero fallos/errores/skips |
| `.\scripts\uv.ps1 run --frozen python runtime/a4-readiness/check_preservation.py` | Exit 0; 45 archivos fuente/config/dependencias, snapshots A2/A3 y raw sin cambios |
| `.\scripts\uv.ps1 run --frozen python scripts/scan_secrets.py` | Exit 0; 165 candidatos, cero hallazgos |
| `git diff --check` | Exit 0; avisos CRLF/LF existentes, sin errores de whitespace |

Evidencia local ignorada: runtime/a4-readiness/evidence.json, preservation.json,
tests.log y tests.xml. El log de pytest se guardó redirigiendo stdout/stderr.
Huella del código/configuración/dependencias verificados:
`bbc6b300f0952b942953dc09b4865c8b393a4ff18027d75619f2f90026ecf904`.
No es un commit ni una certificación de reproducibilidad de operaciones.

Los tests del motor usan fixtures como regresión, nunca como evidencia del mercado
A4. El diagnóstico usa exclusivamente las capturas reales A2 en lectura offline;
verifica por separado el rechazo de AAPL/SPY/QQQ en Strategy 1 congelada.
No se ejecutan brokers, red, capturas nuevas, tuning o comparación de variantes.
No se atribuyen checks globales Ruff/mypy/verify de fases anteriores a esta entrega
documental. No se añaden tests de funciones A4 que no se implementaron.

Incidencias de herramientas: primer diagnóstico llamado inspect.py falló por
colisión de nombre con stdlib antes de cargar datos; renombrado y corregido.
Un intento de preservación por stdin a uv.ps1 no ejecutó el código (no generó
artefacto); se sustituyó por check_preservation.py y se verificó su salida PASS.
No se ocultan esos intentos ni se contabilizan como comprobaciones aprobadas.

## A3 definitivo — ORB_RVOL_v1.0, 2026-09-15

Base y HEAD: `ed456c32355bea05b5c6e04bc4b889ce8bce8ef3`, working tree A2/A3
conservado; sin commit nuevo. Python 3.12.12, uv local y lock congelado.
Config: configs/strategy-1-v1.yaml; hash exclusivo strategy/risk/costs:
`e751eb0db5be3f07950d5da5ccda0def4aeee6c03b0da83912ac38ed6beed7cb`.

Todos los comandos Python siguientes usan `.\scripts\uv.ps1 run --frozen`.

| Comando | Resultado |
|---|---|
| `pytest -q --cov=intraday_etoro_lab --cov-branch --cov-report=json:runtime/a3-freeze/coverage.json --junitxml=runtime/a3-freeze/tests.xml` | exit 0; 645 passed, 0 fallos/errores/skips, 7 warnings; 151.03s |
| `pytest tests/test_strategy_v1.py tests/test_strategy_a3_audit.py tests/test_strategy_orb.py tests/test_config_api.py tests/test_risk_engine.py -q --junitxml=runtime/a3-freeze/focal-final.xml` | exit 0; 116 passed, 0 fallos/errores/skips, 7 warnings; 25.80s |
| `ruff check .` | exit 0, PASS |
| `ruff format --check .` | exit 0, 140 archivos, PASS |
| `mypy src` | exit 0, 40 archivos, PASS |
| `python scripts/inspect_strategy_v1.py` | exit 0, configuración efectiva/hash/fuentes PASS; inspection.json |
| `python scripts/scan_secrets.py` | exit 0, 164 candidatos, cero hallazgos |
| `git diff --check` (sin prefijo uv) | exit 0, PASS |

Cobertura total **91.30871136089924%**; los seis módulos críticos mantienen
exactamente su cobertura previa y superan 90%. Comparación en checks.json.
Huella de código/configs/scripts/tests de esta batería:
`1d4dfc4cd5bdee48db566bfd52a2f08d85a78d5647871e28542e3a0fc518daad`.
42 casos nuevos v1 más los cinco A3 previos conservados. Suite completa también
incluye regresión A1/A2; no equivale a una ejecución del alcance A4.

La batería focal inicial detectó un hash anterior a una corrección de tipos; se
regeneró el snapshot tras revisar esa corrección y la batería final pasó completa.
No se relajó el test ni la comparación de hashes. Regeneración de documentación
mediante scripts/document_config.py: exit 0, dos warnings Pydantic de defaults Path
no serializables; los defaults de estrategia/riesgo/costes están explícitos en YAML.

Se preservaron byte a byte 35 rutas protegidas de datos/riesgo/ejecución/bróker/
backtesting/persistencia, uv.lock y YAML offline anterior respecto a before.json.
Los únicos cambios nuevos de producción están en config.py y strategies/orb.py.
Evidencia local: runtime/a3-freeze (before.json, prior-audit.*, preservation.json,
focal-final.log/xml e inspection.json). Las pruebas son unitarias/contrato con datos
sintéticos; no representan una ejecución de A4 ni acceso de trading.
El gate histórico observed sigue probado y no se ejecutó scripts/verify.py ni CLI
backtest/demo-offline. No se añaden permisos ni rutas de cuenta.

## A3 — investigación histórica B1–B4, 2026-09-15

Base sin cambio: `ed456c32355bea05b5c6e04bc4b889ce8bce8ef3`.
Incremento exclusivamente documental/snapshot; producción, configuración y tests
son idénticos byte a byte a la partida de esta iteración. No se repiten Ruff/mypy
ni suite global: no hay cambios ejecutables. Resultados previos se conservan abajo.

| Comprobación | Resultado |
|---|---|
| `.\scripts\uv.ps1 run --frozen pytest tests/test_strategy_a3_audit.py -q --junitxml=runtime/a3-history/tests.xml` | exit 0; 5 passed, 0 fallos/errores/skips, 1 warning; 12.37s |
| `.\scripts\uv.ps1 run --frozen python scripts/scan_secrets.py` | exit 0; 161 candidatos, cero hallazgos |
| `git diff --check` | exit 0, PASS |
| SHA-256 de todas las fuentes del snapshot | PASS; valores y hashes previos intactos |
| Comparación contra runtime/a3-history/before.json | PASS; solo ocho documentos/snapshot previos y un documento nuevo dentro del alcance |
| `git rev-parse HEAD` y `git status --short` | Base intacta; A2/A3 previos preservados, sin commit/staging |

Evidencia: runtime/a3-history/tests.log, tests.xml, before.json, preservation.json;
commits.txt, consultas *-pickaxe.txt, historiales *-history.patch y
all-history-matches.json. Revisados 15 commits alcanzables y 65 pares únicos
archivo/texto de búsqueda multitémino; consultas y hallazgos explicados en
[auditoría](STRATEGY_1_A3_AUDIT.md). No hubo fetch o modificaciones de ramas.

Resultado: A3 BLOCKED, B1–B4 PENDIENTE; E1 de políticas iniciales, E2 de soporte
técnico, E3 de reglas completas solicitadas. [Propuestas](A3_PENDING_DECISIONS.md)
sin aprobación ni implementación. A4, backtest, optimización y consultas de cuenta
no ejecutados. Solo documentación pública Massive para el análisis de metadata ETF.

## A3 — auditoría bloqueada, 2026-09-15

Base Git `ed456c32355bea05b5c6e04bc4b889ce8bce8ef3`, con cambios A2 sin commit.
Sin cambios de producción/configuración en A3. Se añadieron cinco casos de prueba
que verifican la configuración existente; no acreditan una congelación final.

Prefijo de comandos: `.\scripts\uv.ps1 run --frozen` (Python 3.12.12 y lock existente).

| Comando | Resultado |
|---|---|
| `pytest tests/test_strategy_a3_audit.py tests/test_strategy_orb.py tests/test_config_api.py tests/test_risk_engine.py -q --junitxml=runtime/a3-audit/tests.xml` | exit 0; 74 passed, 0 fallos/errores/skips, 7 warnings; 24.53s |
| `ruff check .` | exit 0, PASS |
| `ruff format --check .` | exit 0, PASS |
| `mypy src` | exit 0, 40 archivos, PASS |
| `python scripts/scan_secrets.py` | exit 0, 160 candidatos, cero hallazgos |
| `git diff --check` (sin prefijo uv) | exit 0, PASS |

Log/JUnit: runtime/a3-audit/tests.log y tests.xml. Snapshot efectivo y hashes:
[strategy-1-a3-audit.json](strategy-1-a3-audit.json); inventario y reproducción:
[STRATEGY_1_A3_AUDIT](STRATEGY_1_A3_AUDIT.md). Sin suite global repetida porque
el incremento solo añade auditoría/documentación/tests; no se atribuye a A3 una
nueva medición de cobertura. No se ejecutó verify.py, replay, optimización ni A4.

## A2 — datos Massive reales, 2026-09-15

Python 3.12.12; uv local, --frozen; lock intacto. Huella del código probado:
`d36e98d5b142fd94b2c8276b8f1433197e2f0397ced0b1b153b0b50fab8a18bd`.

| Comando (prefijo `.\scripts\uv.ps1 run --frozen`) | Resultado |
|---|---|
| `pytest -q --cov=intraday_etoro_lab --cov-branch --cov-report=json:runtime/a2-massive/coverage.json --junitxml=runtime/a2-massive/tests.xml` | exit 0; 598 passed, 0 fallos/errores/skips, 7 warnings; 170.07s |
| `ruff check .` | exit 0, PASS |
| `ruff format --check .` | exit 0, 134 archivos, PASS |
| `mypy src` | exit 0, 40 archivos, PASS |
| `python scripts/scan_secrets.py` | exit 0, cero hallazgos |
| `python scripts/validate_massive_a2.py` con rutas de MASSIVE_A2.md | exit 0, siete criterios PASS, offline-final.json |

Suite previa focal: 82 passed, 5 warnings, exit 0 (antes de añadir el último test
de aritmética/alineación del manifiesto; la suite final incluye los nueve nuevos).
Los fixtures de pruebas no son evidencia de acceso real.
Logs: runtime/a2-massive/pytest.log, tests.xml y coverage.json.
Cobertura total 91.14285714285714%; seis módulos críticos sin reducción y >=90%,
comparación exacta contra prior-coverage.json en checks.json. `git diff --check` PASS.

Capturas nuevas reales: SPY/QQQ, dos GET HTTP 200; AAPL reutilizada sin alteración.
Primer intento restringido CONNECTIVITY_FAILED registrado, segundo PASS.
Manifiesto portable: [massive-a2-manifest.json](massive-a2-manifest.json).
Reproducción, fórmulas, evidencia y límites: [MASSIVE_A2](MASSIVE_A2.md).

No se ejecutó el colector completo scripts/verify.py: incluye backtest, demo-offline
y comandos eToro que están fuera del alcance A2 solicitado. No se afirma 16/16
gates en esta fase. Se ejecutó la suite automatizada con su frontera offline y
credenciales retiradas por conftest. Ningún backtest de rendimiento o simulación
de órdenes fue lanzado como recorrido operativo; tests de regresión sí conservados.
Sin cambios de estrategia, riesgo, ejecución, lock, rutas de cuenta o autorización.

## A1 — selección Massive y batería focal final, 2026-09-15

Partida limpia `adb2e101af7dac7cad134a2114738eb59abfe07c`.
Cambio de producción limitado a DataConfig y load_bundle: proveedor massive,
path de captura offline existente, dispatch explícito y errores propagados.
No se modifica el lector/auditor/cliente Massive ni el manifiesto real anterior.
Las pruebas nuevas son de configuración e integración con capturas fabricadas.
No hubo captura externa, consultas eToro, shadow, órdenes ni Demo Write.

### Comandos finales focales ejecutados

| Comando exacto | Exit | Passed | Failures | Errors | Skips | Warnings |
|---|---:|---:|---:|---:|---:|---:|
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_massive_history.py` | 0 | **69** | 0 | 0 | 0 | 5 |
| `.\scripts\uv.ps1 run --frozen pytest -q tests/test_config_api.py tests/test_import_phase2.py tests/test_e2e_http.py` | 0 | **36** | 0 | 0 | 0 | 7 |

El archivo Massive completo pasó sobre el código final: 62 casos anteriores y
siete adicionales; también se ejercita el gate observed existente a través de
load_bundle con configuración Massive. Duración pytest 26,25s, comando iniciado
13:04:50.830530 UTC y finalizado 13:05:25.080630 UTC. La regresión adicional pasó
en 27,86s. Esta es la evidencia focal vigente; los 52 casos de la sección
histórica siguiente no son el criterio de cierre A1.

Los cinco warnings Massive son de deprecación NumPy/exchange-calendars. La
regresión adicional incluye además avisos Starlette/httpx y AnyIO. No se
silenciaron warnings, redujeron gates ni cambiaron dependencias o exclusiones.

Ambos comandos ejecutados por PowerShell mediante el lanzador local, sin alterar
sus argumentos, con las claves eToro/Alpaca/Massive retiradas. Salida completa,
exit code, tiempos y huella antes/después en
`runtime/a1-massive-config-20260915/{massive,related}.json`.
Huella común estable: `b2c1ae5541d6f3f751ade6f579ed808a1be1c72e63eaa9160a3279ea3888ac80`.
Python 3.12.12; lock SHA-256 intacto:
`d4d45c705053eb37a857e7ef737cbf206b3fe92f04605151fdc0a86159956e9f`.

### Gate oficial completo

`.\scripts\uv.ps1 run --frozen python scripts/verify.py`: **exit 0, 16/16 gates
PASS**, código estable y misma huella que ambas ejecuciones focales. Pytest global:
**589 passed, 0 failures, 0 errors, 0 skips, 7 warnings**; 114,727s en JUnit.
Ambos criterios pendientes de **A1 quedan CLOSED**. A2 no se inicia ni se completa.

Gates: sync frozen offline, Ruff check/format, mypy, pytest, cobertura crítica,
scanner, doctor, data validate, demo-offline, backtest, preflight sin claves
(2 esperado), rechazos etoro_demo/live (2 esperado cada uno), build offline y
sintaxis JS. Los recorridos offline son sintéticos; el preflight es negativo
sin claves. Ningún resultado se atribuye a una conexión eToro/Massive nueva.

Cobertura total líneas/ramas **90,70593149540518%**, frente a 90,52521008403362%
de partida. Cobertura crítica idéntica: riesgo 100%, autorización 98,4%,
transporte 99,26739926739927%, ejecución 95,3125%, modelos de ejecución 100%,
persistencia 95,27027027027027%. No se redujeron gates, umbrales ni exclusiones.

Evidencia completa: `runtime/a1-massive-config-20260915/gates.json` y
`final-{verification.json,coverage.json,test-results.xml}`. La batería anterior
se preserva en `prior-*`. Se compararon las huellas de focales, gate global y
código final: coinciden. El cierre se versiona tras revisar rutas explícitas,
comparar blobs staged y escanear secretos; el commit final se identifica en
el historial Git, sin introducir un hash autorreferente en este documento.

### Alcance de la revisión

Configuración exige path/directorio y rechaza manifest externo para Massive;
el lector existente valida esquema/checksums. Tests prueban directorio vacío,
JSON inválido, fuente incorrecta, checksum distinto y propagación del mismo
MassiveDataError. Fixtures, importador y HTTP fallan deliberadamente si son
invocados durante la carga Massive probada. La captura fabricada permanece
inmutable. Fixtures e import mantienen sus regresiones; provider desconocido
se rechaza incluso al eludir la validación de Pydantic.

Diff vacío respecto de la partida en ORBStrategy, riesgo, ejecución, bróker,
Alpaca, persistencia, subsistema Massive, scripts de captura/gates, configs,
uv.lock y docs/massive-historical-manifest.json. No se altera
OBSERVED_AVAILABILITY_REQUIRED ni order_submission_enabled. A2 queda fuera
de alcance. Esquema JSON/referencia de configuración regenerados con
`.\scripts\uv.ps1 run --frozen python scripts/document_config.py` (exit 0);
único cambio generado: incluir massive en el enum/lista de proveedores.

## Antecedente — Massive histórico, 2026-09-15

Resultado externo: **MASSIVE_HISTORICAL_RVOL_VERIFIED**, AAPL/1m,
20 previas + objetivo 14/09/2026, 21/21 sesiones válidas, 8.190 barras regulares.
GET histórico real, un HTTP 200; plan no observado. Cinco métricas coinciden
exactamente con el motor. Contrato, fuentes y métricas completas:
[MASSIVE_DATA_CONTRACT](MASSIVE_DATA_CONTRACT.md).

Partida limpia `262944f`. Commit de código local **`8ed65eb`** en
feat/phase3-readonly-evidence: ocho rutas explícitas, tres módulos Massive,
CLI de auditoría, pruebas y aislamiento/escaneo de la nueva credencial.
El commit documental siguiente registra resultados sin cambiar el código probado;
su identificador se obtiene del historial Git. Identidad efectiva author/committer
comprobada, sin inventarla ni cambiar configuración. No hubo push/publicación.

Se verificó diff vacío contra la partida para Alpaca (tres módulos y CLI),
eToro/brokers, estrategia, riesgo, ejecución, persistencia, configs, Python y lock.
No se consultaron cuentas. Demo Read previo conservado; órdenes externas
deshabilitadas, Demo Write NOT_TESTED, shadow NOT_STARTED.

### Comprobaciones exactas

Todos los comandos `run --frozen` usan `.\scripts\uv.ps1` en Windows.
Python 3.12.12. `scripts/verify.py` retira las claves eToro, Alpaca y Massive de
los procesos hijos; la suite también las retira y bloquea sockets externos.

| Comando / recorrido | Resultado |
|---|---|
| `run --frozen pytest -q tests/test_massive_history.py`, primera batería | 52 passed; contrato fabricado, antes de ampliar pruebas |
| `run --frozen pytest -q tests/test_strategy_orb.py tests/test_data_contracts.py` | 15 passed |
| Ampliación Massive a 62 casos | Detectó fixture Decimal no serializable en prueba de bucle; se corrigió la serialización del mock |
| `run --frozen pytest -q tests/test_massive_history.py::test_incomplete_pagination_reader_and_loop` | 1 passed tras corregir el fixture |
| `run --frozen python scripts/verify.py`, preliminar | 15/16; fallo del fixture anterior y huella no estable al corregirlo durante ese pase; no es evidencia final |
| `run --frozen python scripts/verify.py`, final | **16/16 PASS**, salida 0, código estable |
| pytest dentro del gate final | **574 pruebas, 0 errores/fallos/skips**, 7 warnings; incluye 62 Massive; 164,734s en JUnit |
| `run --frozen ruff check .`, `ruff format --check .`, `mypy src` | 0 cada uno; 39 archivos fuente para mypy |
| `run --frozen python scripts/audit_massive_history.py --capture --target 2026-09-14`, restringido | CONNECTIVITY_FAILED, sin HTTP/barras; lanzador devolvió 1 |
| Mismo comando con permiso de red | Salida 0; NETWORK_HTTP, HTTP 200, 17.588 barras raw, 8.190 regulares; hito histórico verificado |
| `run --frozen python scripts/audit_massive_history.py --input data/raw/massive/20260915T122702-6a68f76c` | Salida 0; mismas métricas y checksums, sin red |
| Importador existente sobre CSV/manifiesto reales | 8.190 barras, historical_download, cero candidatos/señales; OBSERVED_AVAILABILITY_REQUIRED |
| `git diff --check`, `git diff --cached --check`, scanner de candidatos y blobs staged | 0; ningún secreto; blobs staged iguales a archivos revisados; identidad configurada |

Los 16 gates: sync frozen offline, Ruff check, Ruff format, mypy, pytest,
cobertura crítica, scanner, doctor, data validate, demo-offline, backtest,
preflight sin credenciales (2 esperado), bloqueos etoro_demo/live (2 cada uno),
build offline y sintaxis JS. Replay/demo-offline usan fixtures sintéticos: no
son órdenes externas ni prueban rentabilidad. Preflight es negativo sin claves;
no repite la lectura de cuenta eToro. Avisos de deprecación NumPy/calendario
se conservan; ningún fallo de calidad/acceso se rebajó a warning.

### Cobertura, huellas y revisión

Cobertura combinada líneas/ramas **90,52521008403362%** (partida 90,488615%).
Massive: lector 92,715232%, auditoría 92,523364%, HTTP 89,160839%.
Módulos críticos sin reducción: riesgo 100%, autorización 98,4%, transporte
99,267399%, ejecución 95,3125%, modelos de ejecución 100%, persistencia 95,270270%.
No se cambiaron umbrales ni se añadieron exclusiones para aprobar.

Verificación final: **2026-09-15T12:37:38.294018Z**, huella estable:
`18d6323a0a99498d0c53ec4deaf9d2851d45645f363b4964aa89325768607e27`.
Lock intacto: `d4d45c705053eb37a857e7ef737cbf206b3fe92f04605151fdc0a86159956e9f`.
Evidencia exacta con stdout/stderr, salidas esperadas y comandos en
`runtime/massive-phase-20260915T071442/final-verification.json`;
JUnit/coverage final junto a ese archivo. Baseline y pase fallido preservados
como prior-* y preliminary-*, sin sobrescribirlos.

Captura externa recibida **2026-09-15T12:27:06.148056Z**. Sus intervalos se
marcan final como instantánea histórica, no como versiones originales observadas.
SHA-256 raw: `143f529d60baeb21a9361d1a6eb77652939bcb94b1095135c0903e66dce221a2`.
SHA-256 capture: `43f556d7a6a7ff24ec1a50580f40c438a3e42c1b8d640b90a2490a84fa9310f2`.
SHA-256 CSV: `819eeb47413f0eedba17fdc453f5ff597e9723e4f3d7175a7e75eb94a29e27be`.
La captura ocurrió con fuentes Massive aún sin commit; esas mismas fuentes
están en `8ed65eb`. La corrección posterior afectó solo al fixture de test.

Revisión de seguridad/datos: host/método/ruta fijos, paginación sin desvío de
credenciales, redirecciones bloqueadas, reintentos acotados, raws inmutables,
calendario NY y recibos sin backdating. Duplicados y huecos bloquean, no se
rellenan. Pruebas verifican perturbación del futuro, rechazo del motor por
disponibilidad y ausencia de mutaciones. Reservas, propiedad, recuperación y
transporte eToro no cambian; sus regresiones están incluidas en la batería.

Límites: plan comercial desconocido; cobertura sustentada por contrato EOD
consolidado, sin reconciliación trade a trade. Snapshot susceptible de revisiones;
no validación de disponibilidad realtime, causalidad operativa, universo histórico
ni rentabilidad. Este hito no autoriza shadow ni Demo Write.

## Preparación para fase shadow — 2026-09-14

Decisión: **BLOCKED_BY_EXTERNAL_CONFIGURATION**, motivo observado
**ALPACA_CREDENTIALS_UNAVAILABLE**; **SHADOW_NOT_READY**.
Partida `43c9cc5b7d6366ee72d38dd17542ec7341e4e7e1`, rama
feat/phase3-readonly-evidence, árbol e índice limpios comprobados.
El registro anterior leído tenía 16/16 gates y código estable; se preservó junto
con coverage/JUnit/package en runtime/shadow-readiness-20260914/prior-*.
No se confunde esa evidencia heredada con las ejecuciones nuevas siguientes.

Código final: commit local `b7a17b7d17e3c7da3f1fa03c4bc5cbcffda16918`.
Seis rutas explícitas: tres módulos Alpaca, CLI de auditoría y dos archivos de
tests. Sin cambios en estrategia, riesgo, ejecución, bróker, persistencia,
configs/offline.yaml, Python o uv.lock. El commit documental siguiente conserva
esta evidencia y la decisión; su identificador se obtiene del historial local.
Identidad efectiva author/committer comprobada, sin modificar configuración.

### Comprobaciones ejecutadas

Todos los comandos uv usan `.\scripts\uv.ps1` y `--frozen` en Windows.
La suite estándar retira claves eToro/Alpaca y mantiene modo offline/envío false.

| Comando / recorrido | Resultado observado |
|---|---|
| `run --frozen pytest -q tests/test_alpaca_history.py tests/test_strategy_orb.py tests/test_data_contracts.py tests/test_backtest_replay.py` | 75 passed, 5 warnings, 43,77s antes de añadir los tres casos de costes |
| `run --frozen ruff check .` | 0 |
| `run --frozen mypy src` | 0 tras corregir anotación de coverage; 36 fuentes |
| `run --frozen python scripts/verify.py`, primer pase | 0; 512 pruebas, 16/16 gates, cobertura 90,470532%; código estable |
| `run --frozen python scripts/verify.py`, final | 0; **512 pruebas, 0 errores/fallos/skips, 16/16 gates**; 119,534s de pytest |
| `run --frozen python scripts/audit_alpaca_history.py --capture --feed sip --target 2026-09-11` | Lanzador exit 1; status/reason ALPACA_CREDENTIALS_UNAVAILABLE antes de red; main exit 2 comprobado por test |
| Auditoría histórica/calidad con capturas fabricadas, importación y comparación independiente | Ejecutadas por pytest; incluyen determinismo, hashes, apertura faltante, calendario y futuro perturbado; no evidencia real |
| `bot data validate`, `demo-offline`, `backtest` dentro de verify.py | 0 cada uno; fixtures sintéticos, nunca baseline real |
| Histórico/calidad ampliada/backtest reales | BLOCKED/NOT_RUN por gate externo; no comando con dataset inexistente ni sustitución por fixture |
| `run --frozen python scripts/scan_secrets.py` adicional antes de commit | 0; 145 candidatos, cero hallazgos |
| Escaneo de seis blobs staged + igualdad con archivos revisados | 0; cero hallazgos; keyword audit ETORO_, ALPACA_, APCA_, api-key, secret, private, user-key sin valores impresos |
| `git diff --check`, `git diff --cached --check` | 0 |
| `run --frozen python scripts/verify_package.py` con claves retiradas | 0; instalación nueva offline de 52 paquetes con Python 3.12.12; demo sintética de 4 órdenes y 0 posiciones |

Los 16 gates finales incluyen sync frozen offline, Ruff check/format, mypy,
pytest, cobertura crítica, scanner, doctor, data validate, demo-offline, backtest,
preflight sin claves (2 esperado), bloqueos etoro_demo/live (2 esperado), build
offline y sintaxis JS. No se rebajaron gates ni umbrales. El preflight de la suite
es un test negativo sin claves, no una repetición de la cuenta Demo del usuario.

Primer pase completo preservado en runtime/shadow-readiness-20260914/first-*.
La revisión posterior encontró que el manifiesto aún infería volumen consolidado
con feed no confirmado; se cambió a unknown/unverified con calidad BLOCKED y se
repitieron los gates. Finalizado **2026-09-14T20:07:48.868538Z**; evidencia final
en runtime/shadow-readiness-20260914/final-{verification.json,coverage.json,test-results.xml}.
El código no cambió durante cada batería.

Cobertura final combinada: **90,488615%**. Crítica idéntica a la partida:
riesgo 100%, autorización 98,4%, transporte 99,267399%, ejecución 95,3125%,
modelos de ejecución 100%, persistencia 95,270270%.
Huella de código: `b03aee3f85785abc9f96b167bc62bf9aa848d53d1bc0cabfb604f170f29c331e`.
Lock: `d4d45c705053eb37a857e7ef737cbf206b3fe92f04605151fdc0a86159956e9f`.

Fallos intermedios visibles: cuatro diagnósticos mypy por inferencia de tipos del
reporte se corrigieron con una anotación explícita. Los tres nuevos tests de costes
fallaron inicialmente al consultar un atributo inexistente de SessionDecision;
se corrigió la comprobación a Signal.strategy_version. La suite final los incluye
aprobados sin modificar estrategia ni costes. Un helper PowerShell no pudo leer
coverage.json con ConvertFrom-Json; se leyó con Python, sin alterar el reporte.
Advertencias de dependencias permanecen visibles, sin skips para ocultarlas.

### Evidencia externa y límites

Ambas variables Alpaca ausentes por comprobación de presencia. Intento oficial
en runtime/alpaca-audits/20260914T195435-d5744088/result.json, SHA-256
`87727b03931ce1ea8e7890248ee8336400df8d6a341e13bb40e05862f846fd94`.
Ese hash pertenece al resultado bloqueado, no a datos de mercado. No se creó su
directorio raw. El comando se ejecutó sobre cambios locales con HEAD de partida,
antes del ajuste final de etiquetas de manifiesto; su ruta negativa no cambió.
El artefacto anterior v1 se preserva sin reescribir su clasificación histórica.

Alpaca/AAPL/1Min, SIP solicitado, observado null, 0 barras/sesiones. ORH/ORL/RVOL,
V5 y paridad reales null; ampliación, baseline, costes reales y OOS NOT_RUN.
Tolerancia numérica local 1e-12 absoluta/0 relativa, sin cambios.
Costes 1x/2x/3x se prueban solo con fixtures; ninguna rentabilidad inferida.

Documentación pública [Alpaca FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)
reconsultada: petición por feed y agregación por condiciones son semántica
documentada, no observación de esta cuenta. Feed sin eco conserva FEED_UNVERIFIED
y volumen unknown. El gate OBSERVED_AVAILABILITY_REQUIRED permanece: la descarga
histórica no prueba disponibilidad causal ni autoriza señales/realtime/shadow.

Sin lecturas de cuenta nuevas, Demo Write, WebSocket, shadow, compras, remoto,
push o publicación. La revisión de riesgo/seguridad es propia, sin delegación ni
afirmación de auditoría externa. [Decisión y dependencias](SHADOW_READINESS.md).

La anotación documental de resultados se cerró después del build de los gates;
ese paquete contiene el código final, pero no esta anotación posterior.
Paquete instalado bajo runtime/package-checks/6b811c4a495a433e8cfabd99c1790b5c;
registro y hashes en runtime/shadow-readiness-20260914/final-package-evidence.json.
Comparación byte a byte: 79 archivos de src/scripts/tests/configs/Python/lock
coinciden con el árbol revisado. Sdist SHA-256
`e859142ed5968fcd1ac857112d57fd6376856dc5bdd5859e5ad29b3b2bf283c5`;
wheel `bdd1607ae3083251bc54a1e615abb80eef86b0025251b9731878b00e70ec2874`.

## Alpaca histórico — 2026-09-14

Base limpia 134844b; baseline/gates preservados en
runtime/alpaca-phase-20260914T184730. Nuevo proveedor REST histórico, lector offline
MarketDataProvider, auditoría Fraction/Decimal y CLI de captura explícita. Se
mantuvieron Python 3.12.12, uv.lock, eToro Demo y todos los bloqueos de mutación.

Intento externo autorizado:
`.\scripts\uv.ps1 run --frozen python scripts/audit_alpaca_history.py --capture --feed sip --target 2026-09-11`.
El lanzador PowerShell reportó exit 1; el resultado estructurado es
ALPACA_DATA_INSUFFICIENT_FOR_RVOL / ALPACA_CREDENTIALS_UNAVAILABLE antes de red.
No respuesta HTTP, feed efectivo null, 0 sesiones, métricas reales null, entitlement
no comprobado. No se repitió diagnóstico eToro ni se solicitaron secretos.
Evidencia exacta en runtime/alpaca-audits/20260914T185623-4eab7c52/result.json;
SHA-256 `5948385984087470bc2f04ea2bf1dfb268149f89e83052e2d43eb8e3a883a91c`.
Ese hash es de un resultado bloqueado, no de barras inexistentes.

Pruebas focalizadas: 38 passed con `uv run --frozen pytest -q tests/test_alpaca_history.py`;
15 passed con `uv run --frozen pytest -q tests/test_strategy_orb.py tests/test_data_contracts.py`.
Todos los comandos usan scripts/uv.ps1 en Windows. Un primer comando apuntó a un
nombre de test inexistente y no ejecutó pruebas; se corrigió la ruta. Mypy y Ruff
aprobados. Las pruebas de CLI confirman código de salida 2 para bloqueo semántico;
no lo confunden con la salida 1 del lanzador observado.

Batería final `scripts/uv.ps1 run --frozen python scripts/verify.py`: salida 0,
**491 pruebas sin errores/fallos/skips y 16/16 gates**, 118,875s de tests.
Terminó 2026-09-14T19:11:20.283614Z. Cobertura total **90,070065%**; cobertura crítica
exactamente igual a la base: riesgo 100%, autorización 98,4%, transporte 99,267399%,
ejecución 95,3125%, modelos de ejecución 100%, persistencia 95,270270%.
Ruff check/format, mypy, scan, recorridos offline, bloqueos negativos, build y
sintaxis JS aprobados. Credenciales Alpaca/eToro retiradas de los checks.
Huella de código estable: `eb3e1377cc82f022b520a14d88e08fbc32fa46184417c50a3a83d6d1db54b268`.
Lock intacto: `d4d45c705053eb37a857e7ef737cbf206b3fe92f04605151fdc0a86159956e9f`.
Evidencia exacta preservada en runtime/alpaca-phase-20260914T184730/final-gates.
La documentación se terminó después del build; no se atribuye a ese paquete la
instantánea documental posterior. Las pruebas no certifican conexión externa Alpaca.

Commits locales separados: `880993a` extrae el cálculo sin cambiar reglas;
`c1c5a11` incorpora proveedor, adquisición, auditoría y pruebas; el documental registra el
resultado C observado. Antes de cada commit: rutas explícitas, comparación de blobs
staged con archivos revisados y escaneo de secretos sin hallazgos. Sin remoto/push.

Las barras fabricadas en tests se marcan CONTRACT_TEST y no pueden obtener
ALPACA_SIP_HISTORICAL_VERIFIED. Se prueba RVOL esperado 3 con veinte aperturas de
5.000 y apertura objetivo 15.000, calculado fuera del motor; también se fuerza una
discrepancia del motor y se exige MISMATCH. Esto prueba software, no feed externo.
El motor operativo sigue rechazando histórico real con OBSERVED_AVAILABILITY_REQUIRED.
No hubo shadow, datos realtime, órdenes externas, compras o publicación.

## Market Data — 2026-09-14

Hito externo previo aceptado desde la salida comunicada por el usuario:
DEMO_READ_VERIFIED, connectivity/authentication/demo_identity VERIFIED, writes=0,
external_mutations=DISABLED. No se repitió preflight externo ni lectura de cuenta.
Baseline saneado, HEAD e índice/diff previos preservados en
`runtime/market-audit-20260914T164913/`; gates previos en su carpeta prior-gates.

Evidencia externa nueva: siete GET Market Data mediante MCP, HTTP 200 sin truncar:
instrumentos AAPL, rates, exchanges, candles asc/desc 1Min/1000, OneDay/30 y
OneMinute/10. Fuente de adquisición distinta del proceso HTTP de Bot 3, registrada
explícitamente. Informe completo en [ETORO_MARKET_DATA_VALIDATION](ETORO_MARKET_DATA_VALIDATION.md).

Comprobación real sin red adicional:
`.\scripts\uv.ps1 run --frozen python scripts/audit_etoro_market_data.py --input data/raw/etoro-market-20260914T164913 --output runtime/market-audit-20260914T164913/final-analysis`
salió 0. Este exit acredita el análisis, cuyo resultado de aptitud es BLOCKED,
no calidad suficiente. ORH=334,54; ORL=331,72; volume apertura=1.181.044; RVOL null.
Importación real de 209 minutos aprobada; motor rechaza
OBSERVED_AVAILABILITY_REQUIRED. Parser de quote rechaza timestamp sin offset.
No se afirma paridad numérica, rentabilidad, señal válida ni shadow.

Diez pruebas de auditoría aprobadas con
`.\scripts\uv.ps1 run --frozen pytest -q tests/test_market_audit.py`;
son regresiones sintéticas separadas de los datos externos. Se corrigió un problema
de importación del script en el arnés antes de aprobarlas. Batería final:
`.\scripts\uv.ps1 run --frozen python scripts/verify.py`, salida 0 a
2026-09-14T17:02:56.797513Z. **16/16 gates; 453 pruebas, cero errores/fallos/skips,
82,574s; cobertura total 90,686683% y módulos críticos por encima del 90%.**
Ruff check/format, mypy, scan de secretos, recorridos offline, bloqueos negativos,
build offline y sintaxis JS aprobados. Huella de código estable durante checks:
`4160c8a854c93b76ae078e6d50bb8abb7a6bedda8a4828e6808468cd81e33343`.
Python 3.12.12 y lock SHA `d4d45c705053eb37a857e7ef737cbf206b3fe92f04605151fdc0a86159956e9f`
conservados. Evidencia exacta copiada a `runtime/market-audit-20260914T164913/final-gates/`.
La documentación se terminó después de los checks; la huella corresponde al código,
no se atribuye al build una instantánea documental posterior.
La suite estándar verifica además casos negativos con claves retiradas: no son
reintentos de credenciales ni consultas de conectividad de la cuenta del usuario.

Manifest local: `runtime/market-audit-20260914T164913/final-analysis/manifest.json`.
SHA raw principal: `0e453e072905390e7132e34e8614e61c99cff92b9a6dac7e51d33c2e05221290`.
SHA CSV: `2a869259e2d47376ef466ff5828985b430091e6e5e14396f981d33607fbcae2f`.
Datos raw y derivados permanecen fuera de Git. Sin nueva conexión a otro proveedor,
sin compras, publicación ni mutaciones externas. Los estados de las fases siguientes
son históricos; NOT_CONFIGURED no sustituye el hito actual.

Versionado local: `2d6eec3` conserva soporte de proxy/CA y ocho regresiones de la
fase previa; el commit de esta auditoría añade el analizador, diez regresiones y
documentación de evidencia. Solo rutas explícitas revisadas; blobs staged
comparados con el worktree y escaneados para secretos antes de cada commit.
Sin cambios de identidad Git, remoto ni publicación.

## Fase 3 — versiones realmente comprobadas

Verificaciones ejecutadas en Windows con Python 3.12.12 y uv 0.12.12, lock congelado
sin cambios. Las suites retiran credenciales, bloquean sockets externos en tests y
mantienen ORDER_SUBMISSION_ENABLED=false. Un resultado mock no acredita conexión.

| Capa | Commit / árbol | Verificación observada | Evidencia local preservada |
|---|---|---|---|
| A: índice original, 123 archivos | 6af05f1b16b8e3488a5cd959dc0e7f889b258fd6 / 457998f3c919c0ff03d1c3bf1afcd1930e6bcf02 | 2026-09-10T19:25:47.993500Z; 358 passed, 0 failed/skipped, 82,875 s; 16/16 gates; 90,432663% | runtime/phase3/baseline-A/runtime/verification.json, coverage.json, test-results.xml, import-binding.json |
| B: recuperación íntegra de Fase 2 | ef8bf5564f6e15bd04ae084c18cd63dd27ba380b / f8e132b821babcd96d42d9128978e6cb75450a51 | 2026-09-10T19:29:24.460889Z; 420 passed, 0 failed/skipped, 62,155 s; 16/16 gates; 90,610987% | runtime/phase3/B-verification.json, B-coverage.json, B-test-results.xml |
| C: correcciones contractuales de Fase 3 | b51506a97771d04a5edfb45d46e8fac4c31f307f / 2cd8ee28a1b196d75518fec08536bb30cc7a752f | 2026-09-10T19:35:03.850966Z; 435 passed, 0 failed/skipped, 68,335 s; 16/16 gates; 90,650293% | runtime/phase3/C-verification.json, C-coverage.json, C-test-results.xml |

Cada suite se ejecutó antes del commit indicado sobre esos archivos de código.
Se conservaron las siete advertencias de dependencias, sin ocultarlas con skips.
La huella de código B coincide con la comprobada al final de Fase 2:
`75c12a9e7e320fff518d04dd10f26ad7c00557781d8ae0090ac6bbaf1a7d7e47`.
Huella C: `adab286382ca6fdb8ef98491a6ae65a0b7e69fdc209a5eb712a07176e550b373`.
Lock SHA-256: `d4d45c705053eb37a857e7ef737cbf206b3fe92f04605151fdc0a86159956e9f`.
Código estable durante las baterías B/C. El commit documental posterior comparte
todo el código de C: sus 435 pruebas son evidencia heredada de C, no una nueva suite.
La documentación auditada estaba en edición durante la batería C y no forma parte
de su huella de código; no se atribuye el contenido documental de aquel build al
árbol completo de C. El paquete final debe identificarse por su propio SHA.

### Aislación de A y preservación

Antes de git add: coincidencia de los 123 blobs con index_sha256 del manifiesto
original, SHA del ZIP original confirmado, scanner sin secretos. Los 129 archivos
de B se copiaron y hashearon por separado. Se revisaron también los blobs staged
de B y se confirmó igualdad con los archivos revisados tras CRLF→LF de Git.
Los hashes de bytes originales se conservan sin normalizar en
runtime/phase3/layers-before-commits.json y phase2-B-reviewed.zip.

A se exportó desde el índice a runtime/phase3/baseline-A; uv sync --project sobre
esa carpeta, --frozen --offline, creó su propia .venv (52 paquetes, exit 0).
El módulo cargado fue exactamente
`runtime/phase3/baseline-A/src/intraday_etoro_lab/__init__.py`, con el Python de
`runtime/phase3/baseline-A/.venv/Scripts/python.exe`. Se ejecutó el verify.py de A
sin editarlo mediante runtime/phase3/run_baseline.py. El arnés únicamente fija
ubicación de uv/caché/Python; no cambia gates, pruebas ni expectativas. Git se leyó
con GIT_WORK_TREE=A y una copia del índice original; scanner: 123 candidatos reales,
cero hallazgos. No repositorio anidado ni importación editable del código B.
Se verificó que los bytes exportados A y los archivos de trabajo B siguieran intactos.

### Comandos y códigos de salida

| Comando / comprobación | A | B | C |
|---|---|---|---|
| scripts/verify.py (A a través del arnés aislado) | 0 | 0 | 0 |
| uv sync --frozen --offline | 0 | 0 | 0 |
| python -m ruff check . / format --check . | 0 / 0 | 0 / 0 | 0 / 0 |
| python -m mypy src | 0 | 0 | 0 |
| python -m pytest -q --cov=intraday_etoro_lab --cov-branch --cov-report=json:runtime/coverage.json --junitxml=runtime/test-results.xml | 0 | 0 | 0 |
| scripts/check_coverage.py / scripts/scan_secrets.py | 0 / 0 | 0 / 0 | 0 / 0 |
| bot doctor / data validate / demo-offline / backtest | 0 cada uno | 0 cada uno | 0 cada uno |
| bot etoro preflight --read-only (caso negativo con claves retiradas) | 2 esperado | 2 esperado | 2 esperado |
| bot run --mode etoro_demo / --mode live | 2 / 2 esperados | 2 / 2 esperados | 2 / 2 esperados |
| uv build --offline / node --check src/intraday_etoro_lab/ui/app.js | 0 / 0 | 0 / 0 | 0 / 0 |

Cada registro verification.json contiene los comandos reales, stdout/stderr y exit.
En B/C también inicio/fin UTC y huella por check. La batería focalizada previa de
170 tests del bróker salió 0 antes de añadir los cuatro casos finales de ejecución
sin fills; no se confunde ese paso intermedio con las 435 pruebas del código final.

Adicionales de B ejecutados desde .venv/Scripts/python.exe:

- scripts/verify_import.py: exit 0; 8.190 barras sintéticas, 21 sesiones, cálculo
  CSV independiente ORH=100,70, ORL=99,80, RVOL=3 y perturbación futura PASS. Raw sin
  cambios. Configuración runtime/import-checks/b4621007b7ed44a6805295fc2c7e72c8/replay.yaml;
  registro runtime/phase3/B-import-evidence.json. No se añadió generador en Fase 3.
- scripts/verify_package.py: exit 0; instalación nueva offline de 52 paquetes y
  demo de cuatro órdenes/cero posiciones. Extraído en
  runtime/package-checks/4488758252694cba8e1869e1898c1645/intraday_etoro_lab-0.1.0;
  registro runtime/phase3/B-package-evidence.json. Esta comprobación pertenece a B.

### Evidencia externa y panel, separada

| Recorrido | Versión y comando | Resultado |
|---|---|---|
| Configuración Demo real del proceso | B preservada; .\\scripts\\uv.ps1 run bot etoro preflight --read-only; 2026-09-10T19:24:54Z | Exit 2, NOT_CONFIGURED, CREDENTIALS_MISSING_OR_INVALID. Ambas claves ausentes; sin petición de cuenta. runtime/phase3/preflight.json |
| Catálogo/OpenAPI | API v1.375.0 / catálogo 1.19.1; tags → rutas Demo → cuatro specs | DOCUMENTED; no prueba cuenta local ni usa execute-read/write del conector. Matriz y preguntas no enviadas en ETORO_API_AUDIT |
| Muestra pública | urllib con timeout, sin claves; NVDA XNAS.ITCH de Databento y metadatos | URLError; diagnóstico WinError 10061. Cero bytes de mercado, sin muestra/importación real. Fuente candidata limit=4 insuficiente. Registros data-access.json y data-transport-diagnostic.json en runtime/phase3 |
| HTTP | Suites A/B/C, tests/test_e2e_http.py y test_config_api.py | VERIFIED: autenticación, comandos locales, informe, recuperación y bloqueo Demo |
| Visual | C, UI idéntica a B; python scripts/verify_ui.py con Chrome instalado | Exit 1, 2026-09-10T19:33:13Z, Local browser debugging did not start. NOT_REPRODUCED. runtime/phase3/browser-evidence.json; token retirado, servidor finalizado |
| Mutaciones externas | C, transport spy con permisos previos; guardas preservadas | DISABLED / NOT_TESTED externamente. Ningún envío, cancelación, cierre o modificación de stops de cuenta |

No se deshabilitó seguridad ni se cerraron sesiones personales para probar Chrome.
La única excepción revisada al permiso de escritura del entorno fue para los
metadatos Git autorizados; no cambió permisos del sistema. No hubo rechazo de
revisión automática, publicación, compras, acceso real ni revisión independiente.

Las secciones siguientes son evidencia histórica de sus fases, no el estado actual.

## Fase 2 — evidencia actual

Base reproducida antes del producto: **2026-09-10T16:35:45.658225+00:00**, 358 pruebas,
16/16 gates, 90,432663% de cobertura. Sin discrepancia en esos resultados ni en cuatro
órdenes/cero posiciones. Nombre/correo Git siguen ausentes. Referencia de 123 archivos:
docs/phase2-baseline.json, payload SHA-256
`96ac15232483b818eb9b4b88dac33d244f4ff1978d7453d311aa83194a0fe077`.
ZIP revisado y evidencia original/reproducida en runtime/phase2-baseline; ninguna
credencial, token, DB, log privado ni dataset externo en la copia de código.

Regresión final: **2026-09-10T17:08:10.046894+00:00**; `uv run python scripts/verify.py`:
**420 passed, 0 failed, 0 skipped, 7 warnings, 35,78s; 16/16 gates**. No se cambiaron
umbrales de cobertura, riesgo ni estrategia. Cada check incluye comando, stdout/stderr,
exit_code, resultado esperado, inicio/fin UTC y huella. Código estable durante batería.

Huella SHA-256 de código/pruebas/scripts/configuración comprobados:
`75c12a9e7e320fff518d04dd10f26ad7c00557781d8ae0090ac6bbaf1a7d7e47`.
Lockfile sin cambios: `d4d45c705053eb37a857e7ef737cbf206b3fe92f04605151fdc0a86159956e9f`.
Cobertura combinada **90,610987%**; riesgo 100%, transporte 99,20%, autorización 98,40%,
ejecutor 95,31%, estados 100%, persistencia 95,27%. Ruff, formato, mypy (33 fuentes),
scanner, sync frozen offline, build offline y sintaxis JS aprobados.

| Dimensión de comprobación | Resultado observado |
|---|---|
| Unitarias/integración local | 420 pruebas totales incluyendo contratos mock, HTTP, recuperación, datos y replay |
| Contratos con transporte simulado | Cierres ACK/UNKNOWN/parcial/fill, duplicados, reinicios, timeout, 404/401/403/429/500, propiedad, snapshots atrasados, contabilidad pendiente, cuota compartida y bloqueo de red |
| Lectura externa | NO realizada; preflight con configuración local real devuelve exit 2, NOT_CONFIGURED, CREDENTIALS_MISSING_OR_INVALID |
| Escritura externa | NO ejecutada, NOT_TESTED; transporte y panel DISABLED |
| Datos | Fixture original 26.910 barras; copia CSV de 8.190 barras/21 sesiones validada y reproducida; identidad/SHA/raw preservados |
| Investigación | Solo replay sintético; ORH 100,70 / ORL 99,80 / RVOL 3 calculados desde CSV independientemente; futuro alterado no cambia decisión |
| Panel | Tests HTTP y node --check aprobados; verificación visual Chrome FALLÓ al iniciar depuración local, sin elevar permisos |

`demo-offline` conserva cuatro órdenes, cero posiciones y PnL del simulador sin
duplicar. Nuevo run por cambio de fuente/configuración de manifiesto y código:
`08d4d7a5962b5470f99f`. El histórico run `42ff34b0e40a7f44e861` se conserva; no se
sobrescribió ni se cambió el fixture para mejorar resultados.

Fallos intermedios de fase visibles: formato del nuevo helper de preservación hizo
fallar dos gates del primer intento (runtime/phase2-baseline/attempt1-verification.json);
repetición corregida 16/16. Una prueba anterior esperaba consultar un cierre sin
propietario: ahora exige bloqueo antes de la lectura; se añadió matriz de cierre
trazable/enum desconocido, sin omitir pruebas. Import no-eco de comandos auxiliares
requirió ruta absoluta de uv en Windows. Un import de prueba fuera de cabecera produjo
E402 y se corrigió. Primera regresión de incremento: 416 pruebas/16 gates, conservada
en runtime/phase2-first-regression.json; cuatro casos adicionales dieron las 420 actuales.

Fallo vigente adicional: `python scripts/verify_ui.py RUTA_CHROME` salió 1 con
`Local browser debugging did not start`. No hubo rechazo de revisión automática:
no se solicitó elevación. La captura y browser-evidence del bootstrap son históricos,
no evidencia visual de fase 2. Servidor/token de la comprobación se retiraron al terminar.
No se ocultó el fallo ni se afirmó auditoría independiente: esta revisión es del agente.

Registros actuales: runtime/verification.json, coverage.json, test-results.xml,
phase2-preflight.json, import-evidence.json; docs/phase2-baseline.json y auditorías
oficiales. Comandos adicionales y paquete final se detallan a continuación.

Adicionales ejecutados: `.\scripts\uv.ps1 run --offline bot doctor` y build offline
salieron 0; `python scripts/verify_package.py` instaló 52 paquetes en otra .venv desde
el sdist, íntegramente offline, y reprodujo cuatro órdenes/cero posiciones. Comprobó
exclusión de runtime/secretos y presencia de assets; runtime/package-evidence.json.
`python scripts/verify_import.py` repitió importación/validación/replay, exit 0, con
configuración única registrada en runtime/import-evidence.json. Nunca se etiqueta real.
Revisión final Git: 123 entradas originales intactas, 33 archivos modificados y 6
nuevos sin staging, 0 commits/0 remotos; runtime/phase2-git-evidence.json. Scanner:
129 candidatos, cero hallazgos. Git diff --check y diff --cached --check aprobados.

La revisión final de textos detectó sustitución de acentos por el pipe ASCII de
PowerShell en STATUS/HANDOFF/TASKS y una etiqueta HTML. Se corrigieron escribiendo
UTF-8 directamente y se repitió la batería para dejar huella del contenido final.

## Antecedente: bootstrap

Batería del bootstrap: **2026-09-10T15:50:42.989442+00:00**, Windows, Python 3.12.12.
Ejecutor `scripts/verify.py` con CI=true, BOT_MODE=offline, escrituras false y claves
de cuenta retiradas de procesos hijos. Registro detallado con stdout/stderr, comando,
exit_code y resultado esperado: runtime/verification.json (ignorado, sin secretos).

| Gate ejecutado | Resultado |
|---|---|
| uv sync --frozen --offline | 0; 52 paquetes instalados/verificados |
| Ruff check / format --check | 0 / 0 |
| mypy src | 0; 33 archivos fuente |
| pytest + coverage de ramas + JUnit | 0; **358 passed**, 0 failed, 0 skipped, 7 warnings; 38,46s en batería final |
| check_coverage.py | 0; todos los módulos críticos ≥90% |
| scan_secrets.py | 0; cero hallazgos en archivos candidatos versionables |
| bot doctor | 0; cuenta NOT_CONFIGURED, cero llamadas de red |
| bot data validate | 0; 26.910 barras sintéticas |
| bot demo-offline | 0; 4 órdenes, 0 posiciones, run 42ff34b0e40a7f44e861 |
| bot backtest | 0; mismo run determinista y registro append-only |
| bot etoro preflight --read-only sin claves | 2 esperado; CREDENTIALS_MISSING_OR_INVALID, sin llamada de cuenta |
| bot run --mode etoro_demo | 2 esperado; DEMO_SESSION_RUNNER_NOT_VALIDATED |
| bot run --mode live | 2 esperado; argumento rechazado |
| uv build --offline | 0; wheel y sdist |
| node --check ui/app.js | 0 |

Cobertura (líneas y ramas combinadas): total **90,43%**; risk/engine **100%**,
brokers/transport **99,12%**, brokers/authorization **98,40%**, execution/engine **94,52%**,
execution/models **100%**, persistence/store **96,34%**. No se excluyeron ramas críticas
ni se disminuyó el umbral. Ramas POSIX no ejecutadas en Windows figuran como no cubiertas.

Adicionales: scripts/verify_package.py instaló el sdist en una carpeta nueva y otro
.venv usando solo caché, con exit 0 y el mismo recorrido. Se inspeccionaron sdist/wheel:
sin runtime/.env/credenciales/entornos/cachés y con los tres assets del panel.
Chrome instalado se ejecutó sin ventana y con resolución externa bloqueada; el panel
autenticó, mostró OFFLINE y cuatro órdenes. runtime/dashboard.png y browser-evidence.json
documentan la prueba. scripts/verify_ui.py apagó navegador/servidor y retiró tokens.

Fallos intermedios solucionados: pip sin acceso inicial (exit 1), permisos de directorios
temporales pytest (exit 1, sin pruebas omitidas), una expectativa de código de error
de ID de bróker que debía ser BROKER_ID_CHANGED (exit 1), lint/formato iniciales (exit 1),
scanner que interpretaba la siguiente clave vacía como valor (exit 1), arranque Chrome
bajo restricción (exit 1; prueba posterior con permiso del entorno pasó). La captura
auxiliar de stdout de report necesitó PYTHONUTF8=1 para interpretar correctamente Windows.
Una inspección posterior del sdist encontró un .env.example anidado de la copia de prueba,
sin secretos; se fijó only-include a rutas raíz y se ancló la excepción Git de .env.example.
La inspección y la instalación desde paquete limpio se repitieron tras esa corrección.
No se rebajaron aserciones para ocultar problemas; se corrigió causa/contrato y se repitió.

Warnings persistentes: deprecaciones NumPy/exchange-calendars y TestClient/Starlette;
generación de esquema Pydantic omite default de Path en JSON Schema, mientras la tabla
de CONFIGURATION documenta esos defaults; uv avisa sobre caché dentro del proyecto,
pero la lista explícita del sdist y la inspección prueban que no se empaqueta.

No ejecutado: lectura real de identidad/portafolio eToro, cotizaciones conectadas,
escritura Demo, certificación de stops/cierre en cuenta, datos de mercado licenciados,
GitHub Actions remoto, Linux real, publicación y trading real. No se presentan como skips
ni pruebas aprobadas. Los artefactos de API son contratos públicos y los trades fixtures.
