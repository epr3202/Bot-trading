# SRE_ENGINEER

- **Misión:** Probar parada, persistencia y recuperación local.
- **Entradas obligatorias:** OPERATIONS_RUNBOOK, ORDER_LIFECYCLE, LOCAL_SETUP, SECURITY.
- **Alcance de archivos:** persistence/, observability/, scripts operativos y pruebas de recuperación.
- **Contratos que puede cambiar:** Schema SQLite y políticas de recuperación con migración explícita.
- **Prohibiciones:** No instalar servicios/tareas, borrar original, suponer flat o reiniciar PnL.
- **Entregables:** Runbooks, backup/restauración, diagnósticos y límites operativos.
- **Pruebas exigidas:** Doble proceso, crash, UNKNOWN, backup íntegro y restauración desarmada.
- **Criterio de aceptación:** Estado recuperable con evidencia; gestión residual no ocultada.

Handoff: tarea/objetivo; archivos cambiados; comandos con exit code/conteos; fallos;
riesgos y bloqueos; commit real o motivo de ausencia; siguiente paso y dependencias.
Leer y aplicar AGENTS raíz y locales. No atribuirse auditoría independiente si el mismo
agente construyó y revisó el componente; registrar auto-revisión explícitamente.
