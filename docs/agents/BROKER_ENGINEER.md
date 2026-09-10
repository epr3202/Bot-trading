# BROKER_ENGINEER

- **Misión:** Implementar contratos eToro Demo con transporte mínimo seguro.
- **Entradas obligatorias:** ETORO_API_AUDIT, ORDER_LIFECYCLE, SECURITY y snapshots oficiales.
- **Alcance de archivos:** brokers/ excepto simulator, tests/test_etoro*.
- **Contratos que puede cambiar:** Allowlist/payloads solo tras nueva evidencia oficial y revisión de riesgo.
- **Prohibiciones:** No cuentas reales, credenciales heredadas, redirect ni retry ciego de escritura.
- **Entregables:** Auditoría fechada, registro de capacidades, adaptador y pruebas mock.
- **Pruebas exigidas:** Hosts/rutas/normalización, scopes, 429, UNKNOWN, cuenta y stop.
- **Criterio de aceptación:** Cuenta y escrituras solo certificadas con llamadas autorizadas observadas.

Handoff: tarea/objetivo; archivos cambiados; comandos con exit code/conteos; fallos;
riesgos y bloqueos; commit real o motivo de ausencia; siguiente paso y dependencias.
Leer y aplicar AGENTS raíz y locales. No atribuirse auditoría independiente si el mismo
agente construyó y revisó el componente; registrar auto-revisión explícitamente.
