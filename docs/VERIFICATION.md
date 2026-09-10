# Evidencia de verificación local

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
