# Evidencia de verificación local

Última batería completa: **2026-09-10T15:50:42.989442+00:00**, Windows, Python 3.12.12.
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
