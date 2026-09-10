# Estado — fase 3, 2026-09-10

| Dimensión | Estado | Evidencia / límite |
|---|---|---|
| software_local | VERIFIED | C: 435 pruebas, 16/16 gates, cobertura 90,650293%; sin fallos ni skips |
| reconciliación contractual | DOCUMENTED / CONTRACT_TESTED / BLOCKED por campo | Matriz en ETORO_API_AUDIT: lookup v2 aclara estados y exposición; faltan garantías contables de cierres |
| reconciliación externa observada | NOT_OBSERVED | Ningún cierre ni lectura de órdenes de cuenta ejecutados |
| etoro_demo_read | NOT_CONFIGURED | Preflight real del proceso salió 2: ambas claves ausentes |
| etoro_demo_write | NOT_TESTED | Ninguna mutación externa ejecutada |
| market_data | SYNTHETIC_ONLY / BLOCKED_DATA | Sin muestra real descargada; acceso público falló con WinError 10061; candidato limitado a cuatro registros |
| research | BLOCKED_DATA | Sin ORH/ORL/RVOL reales, replay causal real, shadow observado o rentabilidad validada |
| external_mutations | DISABLED | Guardas de red, CLI y panel conservadas; ni configuración ni permiso anterior habilitan envíos |
| panel_http | VERIFIED | Suite HTTP local aprobada |
| panel_visual | NOT_REPRODUCED | Único intento Chrome salió 1: no arrancó depuración; token retirado |
| Git | VERSIONED_LOCAL | A, B y C conservados; rama feat/phase3-readonly-evidence, sin remoto ni publicación |

A: `6af05f1b16b8e3488a5cd959dc0e7f889b258fd6`, base original de 123 archivos:
358 pruebas en instalación aislada. B: `ef8bf5564f6e15bd04ae084c18cd63dd27ba380b`,
los 33 modificados y seis nuevos de Fase 2: 420 pruebas, importación sintética y
paquete offline aprobados. C: `b51506a97771d04a5edfb45d46e8fac4c31f307f`,
correcciones puntuales de Fase 3: 435 pruebas. El incremento documental posterior
comparte exactamente el código de C; no se le atribuye otra ejecución de la suite.

La identidad Git efectiva ya está configurada y se comprobó antes de los commits.
No volver a pedir nombre/correo. El índice original se conservó antes del primer
git add. No se borraron cambios, no hubo push ni se habilitaron mutaciones externas.

Se detiene la ampliación del producto: quedan acceso Demo Read propio, datos
autorizados suficientes y aclaraciones del bróker. Responsables y acciones mínimas
en [HANDOFF](HANDOFF.md); comandos, huellas y versiones en
[VERIFICATION](docs/VERIFICATION.md). Las 435 pruebas son evidencia local.
