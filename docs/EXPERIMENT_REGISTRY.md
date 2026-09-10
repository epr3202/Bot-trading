# Registro de experimentos

Registro técnico inicial; no evidencia de alpha ni resultado fuera de muestra.

| ID | Hipótesis / variante | Estado y evidencia |
| --- | --- | --- |
| ENG-001 | ORB_RVOL_v0.1 con 20 warmups + 3 sesiones sintéticas | Motor y pruebas `tests/test_backtest_replay.py`; RESEARCH_BLOCKED_DATA. |
| ENG-002 | Costes mayores deterioran el ejemplo fijo de ENG-001 | Aserción de net_return y costes en test de sensibilidad; ingeniería, no estadística. |
| ENG-003 | Latencia 12s supera TTL 10s | Rechazos SIGNAL_EXPIRED, cero trades, sin extensión de TTL. |
| PLAN-001 | ORB base frente a ORB+RVOL | `controlled_comparison` ejecutable; datos de mercado pendientes. |
| PLAN-002 | Sensibilidad a latencia 2s y costes x2 | Función ejecutable; registrar cada run local, no seleccionar solo ganador. |
| FUT-001 | Fuerza relativa desde apertura SPY/QQQ | Fórmula helper, filtro desactivado, hipótesis/ventana pendientes. |
| FUT-002 | Régimen, VWAP y retroceso | Especificaciones y datos pendientes; nunca activar dentro de v0.1. |

Cada ejecución debe conservar JSON del BacktestResult y una entrada JSONL mediante
`backtesting.experiments.append_experiment`, con hipótesis, commit, config_hash,
data_sha256, run_id, estado y métricas. Los artefactos pesados/privados se guardan bajo
directorios ignorados; no editar retrospectivamente el registro para ocultar resultados.
Este índice distingue pruebas ejecutadas de planes, y no contiene commits inventados.
