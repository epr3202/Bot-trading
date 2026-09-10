# Contribuir

Leer AGENTS → STATUS → HANDOFF → TASKS y especificación del módulo. Crear una rama de
trabajo cuando ya haya commits; no borrar cambios ajenos. Mantener monolito modular,
Python 3.12.12, dependencias fijadas mediante uv y datos públicos/sintéticos en Git.

Cada PR describe problema y comportamiento resultante, comandos y resultados, límites
y evidencia de seguridad. Cualquier cambio de ruta necesita contrato oficial y tests
de transporte; cualquier cambio de reglas necesita versión y registro experimental.
Riesgo, persistencia y ejecución exigen escenarios de recuperación, no solo happy path.

Gates: pytest, Ruff lint/formato, mypy src, scanner, build y demo-offline. Las pruebas
son sin red externa y sin secretos. No relajar aserciones, límites o scopes para obtener
verde. Un revisor de riesgo puede bloquear la entrega y dejar evidencia del motivo.
Actualizar STATUS/HANDOFF/TASKS y docs afectadas junto al cambio, sin aprobarse como
auditoría independiente cuando la revisión la realizó el mismo agente.
