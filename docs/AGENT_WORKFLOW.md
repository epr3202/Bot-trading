# Trabajo de agentes

Lectura mínima: AGENTS → STATUS → HANDOFF → tarea en TASKS y especificaciones de módulo.
La herramienta real de esta sesión permite spawn_agent y mensajería entre agentes.
Se asignaron tres subtareas reales y archivos disjuntos: data_research (datos/estrategia/
replay), risk_execution (riesgo/SQLite/ejecución/simulador), etoro_broker (auditoría y
adaptador). Root integró configuración, CLI, API/UI, documentación y gates.

Los subagentes alcanzaron límite de uso antes del cierre; sus archivos quedaron en el
workspace y root continuó la integración y revisión. No hay firmas ni aprobación
independiente inventadas. La revisión final de riesgo/seguridad es auto-revisión del
integrador, respaldada por pruebas; no equivale a auditoría externa.

Las guías de rol no se cargan automáticamente por existir. La asignación debe pedir
leer la guía correspondiente con la herramienta de archivos, además de AGENTS locales.
No se modificó configuración global para forzar carga. En este bootstrap las guías
se completaron después de asignar tareas; no afirmar que guiaron retroactivamente a
los tres subagentes. Se dejan operativas para sesiones posteriores.

Roles: [Tech lead](agents/TECH_LEAD.md), [Cuantitativo](agents/QUANT_RESEARCHER.md),
[Datos](agents/DATA_ENGINEER.md), [Bróker](agents/BROKER_ENGINEER.md),
[Riesgo/seguridad](agents/RISK_SECURITY_REVIEWER.md), [QA](agents/QA_ENGINEER.md),
[SRE](agents/SRE_ENGINEER.md), [UI](agents/UI_ENGINEER.md).

Cada asignación contiene objetivo, archivos, dependencias, criterios y evidencia.
Evitar ediciones concurrentes; para revisión compartir contratos y luego integrar por
el responsable. Usar worktree/ramas cuando haya historial y aislamiento lo justifique.
Handoff incluye cambios, comandos/resultados, fallos, riesgos, commit auténtico y próximo
paso. El revisor de riesgo puede bloquear una entrega; registrar motivo sin reescribir
historial ni afirmar aprobación. No lanzar agentes desde el circuito de trading.
