# intraday-etoro-lab

Laboratorio ejecutable de ORB de cinco minutos + RVOL para investigación intradía,
con riesgo Decimal, simulación persistente, backtesting e interfaz local en español.
**Exclusivamente virtual. No existe trading real ni promoción automática.**

Fase 2 completada en el proyecto existente: base preservada, 420 pruebas y 16/16 gates
locales aprobados (90,61% de cobertura). La comprobación HTTP del panel pasó; Chrome no
arrancó en esta fase y su verificación visual no se declara reproducida.
**Todas las mutaciones externas están deshabilitadas, incluso cierres y stops Demo.**
La reconciliación conserva exposición observada separada de la contabilidad pendiente;
el contrato externo de cierre todavía no permite resolver todos los estados/comisiones.
eToro permanece NOT_CONFIGURED; datos SYNTHETIC_ONLY; investigación BLOCKED_DATA.
Los mocks no acreditan conexión. No hubo ninguna lectura de cuenta ni orden externa.

Para instalar y recorrer una sesión desde la raíz:

```powershell
uv sync --frozen
uv run bot doctor
uv run bot demo-offline
uv run bot data validate --config configs/offline.yaml
uv run bot backtest --config configs/offline.yaml
uv run bot dashboard --host 127.0.0.1
```

En este Windows uv está instalado dentro del proyecto; sustituye `uv` por
`.\scripts\uv.ps1`. Ejemplo: `.\scripts\uv.ps1 run bot demo-offline`.
No se modificó PATH global. Se fija Python 3.12.12 y 52 paquetes mediante uv.lock.

El panel abre en **http://127.0.0.1:8765**. Lee `runtime/control-token` localmente e
introdúcelo en el formulario; nunca lo envíes por chat. Ctrl+C termina el servidor.
Desde el panel puedes ejecutar una sesión completa o abrir/cerrar el fixture por pasos,
pausar y reconciliar. Las órdenes y posiciones tienen vistas separadas; UNKNOWN es visible.
Los controles Demo requieren confirmación y muestran el bloqueo de integración vigente.

El generador produce 26.910 barras sintéticas de un minuto, tres símbolos ficticios,
20 warmups y tres sesiones de evaluación. RVOL calculable: SIMA=3, SIMB=2, SIMC=1 en la
primera sesión. La demo persiste dos entradas y dos cierres, termina sin exposición y
al repetirla no duplica intenciones ni PnL. Sus cotizaciones sintéticas prueban lifecycle.
El backtest separado simula próximas aperturas de minuto, costes y stops conservadores.
**SYNTHETIC — NO EVIDENCE OF PROFITABILITY.** No hay históricos de mercado ni alpha validado.

Los JSON/HTML están en `reports/runs/`; `bot report --run-id ID_EXISTENTE` muestra un
informe existente. Cada resultado lleva manifiesto, hashes, fuente/calendario, semilla,
modelo de ejecución y revisión de código. `experiments.jsonl` conserva todas las ejecuciones.
CSV/Parquet requiere esquema y manifiesto: [contratos](docs/DATA_CONTRACTS.md).

Para lectura eToro, seguir la [configuración segura](docs/OPERATIONS_RUNBOOK.md) de
ETORO_API_KEY y ETORO_USER_KEY propias, Demo Read. `uv run bot etoro preflight --read-only`
consulta identidad mínima y portafolio virtual; sin claves devuelve BLOCKED, exit 2.
Ni un preflight aprobado ni una autorización anterior habilitan escrituras en esta fase.
`uv run python scripts/verify_import.py` prueba importación/validación/replay con 20
warmups y una evaluación sintéticos, cálculo independiente y perturbación futura.
La [auditoría de datos](docs/DATA_PROVIDER_AUDIT.md) recoge carencias eToro y solo dos
alternativas públicas, sin contrataciones ni muestras reales obtenidas.

Git sigue en main sin commits ni remoto: GIT_IDENTITY_BLOCKED. El índice conserva la
base de 123 archivos; el incremento está en working tree. Huellas y referencia local
en [phase2-baseline.json](docs/phase2-baseline.json); procedimiento de identidad auténtica
en [versionado](docs/GIT_WORKFLOW.md). Staging no equivale a historial.

Verificación local:

```powershell
uv run pytest --cov=intraday_etoro_lab --cov-branch --cov-report=json:runtime/coverage.json
uv run python scripts/check_coverage.py
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/scan_secrets.py
uv build --offline
```

La suite bloquea sockets externos y no requiere secretos. CI está preparado para Windows
y Linux con permisos mínimos, aún sin ejecución remota/publicación. También se probó
instalar el paquete en un entorno nuevo y ejecutar offline usando solo caché local.

Estructura: `src/intraday_etoro_lab/{domain,data,strategies,risk,execution,brokers,
persistence,backtesting,api,ui,observability}`, `configs`, `tests`, `scripts`, `docs`.
Empieza por [STATUS](STATUS.md), [HANDOFF](HANDOFF.md), [AGENTS](AGENTS.md) y
[TASKS](TASKS.md). [Runbooks](docs/OPERATIONS_RUNBOOK.md),
[auditoría eToro](docs/ETORO_API_AUDIT.md), [configuración](docs/CONFIGURATION.md)
y [protocolo de investigación](docs/BACKTEST_PROTOCOL.md) explican los límites concretos.
