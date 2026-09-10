# Continuidad del proyecto

Repositorio efectivo: `C:\Users\epulgare\Nueva carpeta\Bot 3` (nombre lógico
intraday-etoro-lab), originalmente vacío. Windows/PowerShell, Git 2.52.0, uv 0.12.12
en .tools/bin, Python 3.12.12 en .python y entorno .venv. Nada instalado como servicio
ni en PATH global. BOOTSTRAP_SPEC conserva la petición completa; STATUS contiene
los estados ortogonales actuales.

Se construyó el recorrido completo local: FixtureProvider → ORBStrategy → RiskEngine
→ Executor/StateStore/SimulatorBroker → cierre → BacktestResult JSON/HTML → panel.
AppConfig compone modelos de módulos; source_revision incorpora hash del código y
marca UNCOMMITTED mientras no haya un commit auténtico. Estrategia y riesgo se
comparten con replay. No usar cotizaciones sintéticas como evidencia de datos eToro.

Comandos desde este directorio: `.\scripts\uv.ps1 sync --frozen`,
`.\scripts\uv.ps1 run bot doctor`, `.\scripts\uv.ps1 run bot demo-offline`,
`.\scripts\uv.ps1 run bot dashboard --host 127.0.0.1`.
Panel en http://127.0.0.1:8765; token por proceso en runtime/control-token.
La verificación de navegador terminó y retiró sus archivos de control. Sin servidor,
los comandos de control no arrancan otro bot. El fixture persistido conserva 4 órdenes
y ninguna posición; para repetir desde cero crear otra runtime_dir, no borrar la DB.

Última batería completa: `python scripts/verify.py`, **16/16 checks**. Incluyó instalación
frozen offline, Ruff, formato, mypy, 358 tests bajo CI=true con cobertura/JUnit, scanner,
doctor/validación/demo/backtest y fallos seguros esperados. Resultado: 0 fallos, 0 skips,
7 warnings de dependencias. Cobertura global 90,43%; módulos críticos 94,52–100% salvo
autorización 98,40% y transporte 99,12%. Paquete nuevo offline y navegador Chrome también
probados. Run reproducible: `42ff34b0e40a7f44e861`. Ver docs/VERIFICATION y runtime/*.json.

Problemas resueltos: uv/Python ausentes de PATH; descarga inicial restringida; ACL de
uv local y temporales pytest Windows; falso positivo del scanner por cruzar líneas vacías;
comando de reconciliación no confirmado registrado incorrectamente como DONE.
El scanner usa whitespace horizontal; temporales de test heredan ACL local; el comando
sin resultado confirmado queda BLOCKED. Los fallos iniciales se conservan en VERIFICATION.

Tres subagentes reales implementaron módulos disjuntos; alcanzaron límite de uso y
root completó integración/revisión. La revisión final es auto-revisión, no auditoría
independiente. Leer docs/AGENT_WORKFLOW y la guía del rol de la siguiente tarea.

Git: rama main inicializada y 123 archivos preparados en el índice; **no hay commits**,
identidad name/email no configurada. El working tree aún no constituye un commit.
Se pidió identidad al usuario, sin respuesta al cierre. No inventar identidad ni tocar
git config --global. Archivos preparados para revisión/versionado; no remoto/publicación.
Cuando el usuario aporte identidad, configurar solo localmente, revisar/scannear staged
y crear hitos reales. No afirmar que ya existen los commits propuestos en el encargo.

Siguiente tarea técnica prioritaria (X02/X03): diseñar y validar la orquestación de sesión
Demo sobre un MarketDataProvider con volumen negociado/historia/recepción compatibles;
resolver equity/cash utilizables, reglas de instrumento y reconciliación de cierre v1
antes de habilitar entradas. Requiere contratos/evidencia, no otra bandera de bypass.
X01: recibir claves propias y autorización para preflight real de lectura. Primera
escritura requiere otra activación explícita, presupuesto, gates y permiso temporal.
No se autorizaron ni ejecutaron operaciones de cuenta durante este bootstrap.
