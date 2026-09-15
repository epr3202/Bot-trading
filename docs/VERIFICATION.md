# Evidencia de verificación local

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
