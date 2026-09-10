# Tareas

Cada cambio conserva prioridad: solo virtual, ausencia de duplicados, evidencia,
reproducibilidad y funcionalidad. Los IDs se mantienen al actualizar el estado.

| ID | Prioridad / responsable | Objetivo y archivos | Dependencias | Aceptación / evidencia |
|---|---|---|---|---|
| T01 | P0 / root | Entorno aislado, config, CLI, Git | ninguna | Python fijado, lock, rechazo de modos reales |
| T02 | P0 / data_research | domain, data, strategies y pruebas | T01 | 20 warmups, RVOL calculable, disponibilidad, calendario e importación |
| T03 | P0 / risk_execution | risk, execution, persistence, simulador | T02 contratos | Reservas atómicas, UNKNOWN, propiedad, recuperación, cobertura |
| T04 | P0 / etoro_broker | transporte/adaptador y auditoría oficial | T01 | allowlist y mocks; estados externos separados |
| T05 | P1 / data_research | backtesting, métricas e informes | T02/T03 | repetibilidad, costes, bootstrap por sesiones, etiquetas sintéticas |
| T06 | P1 / root | API local, UI española, comandos | T02/T03/T05 | recorrido HTTP completo y controles autenticados |
| T07 | P0 / root + agentes | revisión, gates, documentación | T01–T06 | pruebas, lint, formato, tipos, build, secretos y handoff exactos |
| X01 | P0 / usuario futuro | preflight real de lectura Demo | credenciales propias y autorización | evidencia de identidad mínima/permisos y portafolio virtual |
| X02 | P0 / usuario futuro | datos históricos/minuto y sesión compatibles | proveedor/licencia/procedencia | volumen negociado verificable, disponibilidad y cobertura |
| X03 | P0 / usuario futuro | primera escritura virtual | X01/X02, elegibilidad y protección, presupuesto, armado | smoke opt-in observado; nunca durante bootstrap |

Estado al cierre del bootstrap: T01, T02, T03, T05, T06 y T07 LOCAL_VERIFIED.
T04 CONTRACT_LOCAL_VERIFIED; integración de cuenta pendiente. Evidencia común:
358 pruebas, 16/16 gates, cobertura crítica ≥90%, instalación nueva offline y navegador.
T01 tiene una dependencia administrativa pendiente: nombre/correo auténticos para
commits; Git inicializado en main sin autor inventado. Ver docs/VERIFICATION.

X01–X03 son gates externos, no pruebas satisfechas con mocks. Siguen BLOCKED por
credenciales/autorización y por la integración de sesión/datos descrita en HANDOFF.
X04 (P0, depende de X01/X03): resolver estados y recuperación de cierre v1 antes de
habilitar runner. Aceptación: timeout después de aceptación, posiciones propias y
exposición residual reconciliados con contratos/evidencia; ninguna venta duplicada.
X05 (P2): ejecutar CI Windows/Linux en remoto solo cuando haya repositorio/destino
autorizados. Aceptación: mismos gates desde checkout limpio, sin secretos en PRs.
