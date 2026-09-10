# Arquitectura

Monolito modular Python 3.12.12: Pydantic, httpx, SQLite, exchange-calendars,
pandas/Parquet, FastAPI y HTML/CSS/JavaScript locales. No servicios persistentes.

```mermaid
flowchart LR
  A[Fixtures o CSV/Parquet] --> D[Contratos y calendario]
  D --> S[ORB / RVOL]
  S --> R[RiskEngine]
  R --> E[Ejecutor único]
  E <--> DB[(SQLite)]
  E --> B[Simulador local]
  E -. gate de integración pendiente .-> T[Adaptador eToro Demo]
  T --> G[Transporte con allowlist]
  S --> BT[Replay de investigación]
  R --> BT
  BT --> REP[Informes y registro]
  UI[Panel español] --> API[API autenticada localhost]
  API --> E
  API --> REP
```

Domain define Instrument/Bar/Signal/Manifest. Execution añade intención, orden del
bróker, fill, posición, sesión y auditoría. MarketDataProvider se mantiene independiente
de ExecutionBroker: eToro puede aportar bid/ask sin satisfacer RVOL histórico.

OperationService es propietario único de comandos, con exclusión OS y mutex para HTTP.
Cada operación SQLite abre su conexión en el hilo que la usa. Los comandos CLI de
control se dirigen a ese servidor; no lanzan otro bot. Una demo-offline autónoma puede
adquirir el mismo bloqueo si no existe servidor. Estados se separan por modo.

Recorrido de demostración: 20 warmups sintéticos → selección congelada → señales →
cotizaciones sintéticas explícitas → riesgo → dos aperturas persistidas → pausa → dos
cierres → informe. Las cotizaciones de este recorrido prueban ciclo de vida. El backtest
separado usa posteriores aperturas de minuto y escenarios de fricción; no confundirlos.

La interfaz no guarda claves eToro. El token local se genera por proceso y queda fuera
de HTML/URLs. Las lecturas públicas de documentación se usaron durante desarrollo;
ningún arranque offline consulta eToro ni obtiene credenciales del conector MCP.
