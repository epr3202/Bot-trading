# Estado — fase 2, 2026-09-10

| Dimensión | Estado | Evidencia / límite |
|---|---|---|
| software_local | VERIFIED (suite y HTTP) | 420 pruebas, 16/16 gates; verificación visual Chrome falló al arrancar |
| close_reconciliation | BLOCKED externo / parte local CONTRACT_TESTED | Trazabilidad, parciales, recuperación y exposición observada probadas; enum v1, respuesta perdida sin ID y contabilidad final sin garantías |
| etoro_demo_read | NOT_CONFIGURED | Preflight local exit 2; ninguna lectura de cuenta |
| etoro_demo_write | NOT_TESTED | Ninguna escritura externa ejecutada |
| market_data | SYNTHETIC_ONLY | 26.910 barras; importación separada de 8.190 barras / 21 sesiones |
| research | BLOCKED_DATA | Replay sintético; sin muestra real, shadow observado ni rentabilidad validada |
| external_mutations | DISABLED | Sin bypass por configuración o permiso anterior; simulaciones solo en transporte mock |
| Git | GIT_IDENTITY_BLOCKED | main, 0 commits, sin remoto; índice original de 123 archivos, incremento sin commit |

Base reproducida: 358 pruebas/16 gates/90,432663% a las 16:35:45 UTC. Regresión final:
420 pruebas (0 fallos, 0 skips, 7 warnings), 16 gates, 90,610987% a las 17:08:10 UTC.
Riesgo 100%, transporte 99,20%, autorización 98,40%, ejecutor 95,31%, estados 100%,
persistencia 95,27%. Ruff/formato/mypy/build y recorrido HTTP aprobados.

El simulador conserva 4 órdenes y 0 posiciones; run actual 08d4d7a5962b5470f99f.
La revisión de cantidad observada no inventa precio, comisiones ni efectivo. Un 404,
ACK o portafolio vacío no demuestra flat. Toda ambigüedad material pausa entradas.

Disponibilidad sintética: +200 ms. ORH/ORL/RVOL calculados independientemente desde
CSV y prueba de futuro alterado aprobados. No se alteraron reglas, calentamiento,
presupuesto ni TTL. Auditoría pública limitada a eToro, Alpaca y Databento; sin compras.

Chrome: verificación visual NO_REPRODUCIDA (exit 1, depuración local no arrancó).
No se elevó permiso ni se modificó sandbox/TLS. La captura anterior no es evidencia
actual. No quedan servidor ni token de esta comprobación. Solo auto-revisión del agente.

Evidencia y omisiones: [VERIFICATION](docs/VERIFICATION.md), [base preservada](docs/phase2-baseline.json),
runtime/verification.json, phase2-preflight.json, import-evidence.json y coverage.json.
Continuidad y bloqueos externos: [HANDOFF](HANDOFF.md), [TASKS](TASKS.md).
