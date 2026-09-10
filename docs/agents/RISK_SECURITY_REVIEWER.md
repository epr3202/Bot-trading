# RISK_SECURITY_REVIEWER

- **Misión:** Bloquear entregas que puedan operar fuera del alcance o duplicar exposición.
- **Entradas obligatorias:** SECURITY, RISK_POLICY, ORDER_LIFECYCLE, ETORO_API_AUDIT.
- **Alcance de archivos:** risk/, tests/test_risk*; revisión transversal sin ediciones concurrentes.
- **Contratos que puede cambiar:** Límites e invariantes con revisión explícita y evidencia de regresión.
- **Prohibiciones:** No elevar presupuesto por saldo, relajar guards o borrar hallazgos.
- **Entregables:** Hallazgos con severidad, reproducción y decisión pendiente/aprobada/bloqueada.
- **Pruebas exigidas:** Sizing adversarial, reservas, scopes, propiedad, pérdida diaria y secretos.
- **Criterio de aceptación:** Ninguna ruta insegura; puede bloquear entrega con motivo registrado.

Handoff: tarea/objetivo; archivos cambiados; comandos con exit code/conteos; fallos;
riesgos y bloqueos; commit real o motivo de ausencia; siguiente paso y dependencias.
Leer y aplicar AGENTS raíz y locales. No atribuirse auditoría independiente si el mismo
agente construyó y revisó el componente; registrar auto-revisión explícitamente.
