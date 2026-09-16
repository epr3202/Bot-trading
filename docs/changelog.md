## A7 WebSocket: spike bloqueado por handshake HTTP 403

Revision contractual permite eToro WebSocket conservando el gate de 3 s.
Diagnostico aislado: el handshake devuelve HTTP 403 con pagina Proxy WebGateway
EPM, antes de Authenticate; cero eventos, suscripciones u ordenes. No se ha
integrado el stream al runner ni se ha cambiado codigo productivo, riesgo,
Strategy 1, A6, Massive, contratos congelados o uv.lock. Reconnect productivo
y validacion en mercado abierto pendientes; no declarar migracion PASS.
Detalle: docs/A7_WEBSOCKET.md (desde docs: A7_WEBSOCKET.md).
A7 PARTIAL/BLOCKED: upgrade WebSocket rechazado por la infraestructura de red.

# Índice de cambios

## A7 — auditoria UTC/costes, PARTIAL/BLOCKED (2026-09-16)

La evidencia anterior era 81.588043 s, no 81588 s; ambiguedad de coma decimal.
Dos GET rates nuevos confirmaron retrasos de 35.860831 y 75.107782 s.
Recepcion HTTP registrada antes del parseo, UTC aware; limite 3 s intacto.
Costes value/amount normalizados dentro del adapter; fixture real sanitizado.
142 pruebas focales A7/A6 PASS. Gate externo QUOTE_STALE_OR_DELAYED;
cero ordenes/mutaciones; identidad DEMO y parser de costes PASS.
No se habilita el vertical de trading mientras falle frescura. No A8.
Detalle, cambios, comandos y evidencia: [auditoria A7](A7_QUOTE_COST_AUDIT.md).


## A7 — continuación: preparación y diagnóstico externo, PARTIAL/BLOCKED

Se distingue rechazo previo al envío de UNKNOWN: preparación con intención
APPROVED, metadata durable y liberación de reservas solo con cero intentos de
mutación demostrados. Crash durante POST sigue UNKNOWN y nunca reenvía.
El usuario autorizó estímulo sintético A6 exclusivamente para el smoke Demo.
Identidad/scopes/elegibilidad/costes hipotéticos observados con credenciales
existentes PRESENT. La cotización externa falló: 81.588043s frente a máximo 3s.
Costes usa value frente a amount del esquema; contabilidad de cierre pendiente.
Cero órdenes/mutaciones. No se conectó aún el runner ni se habilitó Demo Write.
Detalles y partes pendientes: [continuación A7](A7_COMPLETION_ATTEMPT.md).
Las afirmaciones históricas de core intacto o UNKNOWN para todo rechazo quedan
actualizadas por este incremento; Strategy 1, riesgo, A6 y esquema se conservan.

## 2026-09-16 — A7 parcial, defensa Demo-only

- Clasificación centralizada de identidad y portfolio; preflight A5 reutilizado.
- Verificación fresca en adaptador y transporte; permisos invalidados ante fallo.
- Pruebas negativas de cuatro mutaciones, bypass directo, cambios de binding,
  caducidad y configuración engañosa; integración local con SQLite/riesgo/ejecutor.
- No se habilitan mutaciones de red ni runner A7; dependencias y DoD pendientes
  explícitos en [A7](A7_DEMO_ONLY.md). A6/Strategy 1/core preservados.

## 2026-09-16 — A6 runner de sesión exclusivamente simulada

- execution/session.py orquesta contexto/elegibilidad/Strategy 1 v1/riesgo/
  intención durable/simulador/reconciliación y cierre coherente.
- session_inputs.py separa evidencias y conversión a EntryRequest; session_fixture.py
  y scripts/run_a6.py proporcionan escenarios sintéticos reproducibles.
- tests/test_demo_session.py cubre los siete casos mínimos, guardas de no red,
  parciales, pérdida de respuesta, recuperación e idempotencia.
- Core, estrategia congelada, esquema SQLite, dependencias y protecciones eToro
  intactos. Cero mutaciones externas; A7 pendiente. [Diseño](A6_SESSION.md).

## 2026-09-16 — A5 CLOSED, credenciales existentes y PASS real

Carga operacional explícita con uv --env-file .env; sin modificar .env ni código.
Confirmados identidad Demo, 16 scopes, credit virtual y AAPL con tres GET/HTTP 200.
Fallo inicial de red WinError 10061 superado en entorno autorizado, TLS intacto.
202 tests focales PASS; Ruff/mypy/inspector PASS. Diagnóstico, runbook y continuidad
actualizados. Sin A6, órdenes o Demo Write. [Evidencia](A5_PREFLIGHT.md).

## 2026-09-16 — A5 preflight de lectura, validación externa pendiente

- Servicio brokers/preflight.py y CLI existente ampliada con instrumento del
  manifiesto A2 e informe JSON saneado guardable mediante --evidence.
- Transporte limitado por instancia a tres GET; identidad/portfolio endurecidos,
  claves JSON duplicadas y estados HTTP inesperados rechazados.
- tests/test_demo_preflight.py cubre contratos, fallos, mutaciones y secretos.
- Prueba externa bloqueada antes de red: ambas claves ausentes. No A6 ni órdenes.
  Diseño/evidencia: [A5](A5_PREFLIGHT.md); checks: [VERIFICATION](VERIFICATION.md).

## 2026-09-15 — A4 replay_as_of_v1 y dos runs Massive reproducibles

- Boundary en backtesting/replay.py: procedencia histórica preservada, vistas
  observed filtradas por reloj, publicación explícita prioritaria, cierre de barra
  documentado como alternativa, orden atómico y primeras decisiones terminales.
- Integración mínima en backtesting/engine.py; run_metadata amplía el resultado
  existente. backtesting/a4.py y scripts/run_a4.py validan pins A2/A3, guardan
  disponibilidad por registro y comparan todo el resultado funcional.
- Dos runs reales consecutivos con Strategy 1 congelada: operaciones/summary
  idénticos, cero trades por RVOL_BELOW_THRESHOLD, no por bloqueo temporal.
  Artefactos JSON/JSONL/HTML en runtime/a4-replay/run-1 y run-2; comparación PASS.
- Tests nuevos en tests/test_replay_as_of.py, contrato REPLAY_AS_OF_V1 y evidencia
  A4_READINESS. Checks exactos de entrega en VERIFICATION. Sin cambios A2/A3/raw,
  riesgo, eToro, configuración congelada, lock, tuning o publicación.

## 2026-09-15 — A4 inspección, implementación bloqueada

- Verificados hashes A2/A3; rechazo real por captura OBSERVED_AVAILABILITY_REQUIRED.
- Informe docs/A4_READINESS.md, continuidad STATUS/HANDOFF/TASKS y decisiones/
  pendientes/VERIFICATION actualizadas; no se modifica software ni arquitectura.
- Evidencia diagnóstica local en runtime/a4-readiness/evidence.json con huella del
  código/configuración/datasets; no hay artefactos de runs ni reproducibilidad A4 PASS.
- Regresión focal: 63 passed, 5 warnings, cero fallos/skips. A4 BLOCKED por contrato
  temporal; propuestas diferidas y exclusiones de comparación documentadas.

## 2026-09-15 — congelación definitiva A3, ORB_RVOL_v1.0

- RS LONG estricta contra SPY y QQQ, desde apertura regular a primera candidata
  ORB, sin margen; tiempos exactos y disponibilidad causal, fallos explícitos.
- Configuración v1 explícita, contrato de parámetros/riesgo/costes, strategy_hash
  separado de datos/replay, snapshot y comando de inspección de hashes.
- Régimen/VWAP confirmation desactivados; ETF excluidos y benchmarks reference-only.
- Pruebas RS, empates, faltantes/tardíos/futuros, universo, importador y congelación;
  compatibilidad v0.1/A1/A2 conservada. No cambia riesgo, ejecución, providers o lock.
- B1–B4 aprobados; A3 DONE, A4 PENDING. Evidencia exacta en VERIFICATION.

## 2026-09-15 — A3 continuación histórica B1–B4

- Búsqueda sobre 15 commits locales, historial de configuraciones, líneas eliminadas
  y fuentes actuales; matriz E1/E2/E3 con referencias concretas en auditoría/snapshot.
- Recuperada exclusión ETF explícita y rol de benchmarks desde bootstrap; análisis
  de metadata Massive, representación interna y gates de elegibilidad eToro.
- Propuestas B1–B4 preparadas para revisión, sin adoptar reglas ni modificar código,
  configuración, tests o arquitectura. A3 BLOCKED; A4 pendiente.

## 2026-09-15 — A3 auditoría, congelación BLOCKED

- Inventario de reglas actuales y procedencia, snapshot strategy/risk/costs con
  hashes y commit base; discrepancias RS/régimen/VWAP/universo documentadas.
- Pruebas de configuración explícita, identidad, determinismo y extensiones
  desactivadas. No equivalen a validar una congelación final.
- A3 bloqueado por decisiones pendientes; A4 pendiente. Sin cambios de producción,
  proveedores, configuración ejecutable o reglas. Evidencia en STRATEGY_1_A3_AUDIT.

## 2026-09-15 — A2 validación real Massive

- Captura histórica limitada ampliada a SPY/QQQ; identidad, paginación y calidad
  preservadas. AAPL previo reutilizado sin alterar raw.
- Auditor y CLI A2: 21 sesiones alineadas, ORH/ORL/RVOL con comparación independiente,
  VWAP HLC3, RS frente a ambos benchmarks y manifiesto reproducible.
- Pruebas nuevas de benchmarks/allowlist, campos faltantes, historia insuficiente,
  timestamps, procedencia fabricada bloqueada, aritmética y serialización.
- Siete criterios de datos PASS reales; régimen no definido en v0.1 documentado.
  Strategy 1 intacta. Detalle: [A2](MASSIVE_A2.md), checks en VERIFICATION.

## 2026-09-15 — cierre de los dos criterios A1

- Massive seleccionable por DataConfig y load_bundle mediante data.path al
  directorio de captura offline. Dispatch explícito, errores visibles, sin fallback.
- Batería focal final Massive: 69 passed; regresión de configuración/importación/
  servicio: 36 passed. Gate oficial: 589 pruebas, 16/16 PASS; cobertura crítica intacta.
- Documentación y esquema de configuración actualizados. Histórico real preservado;
  sin cambios ORB/RVOL, ejecución, disponibilidad observed, shadow o Demo Write.
  A2 no se inicia. Comandos exactos en [VERIFICATION](VERIFICATION.md).

El registro canónico es [CHANGELOG](../CHANGELOG.md). La evidencia de comandos
y versiones pertenece a [VERIFICATION](VERIFICATION.md). Este documento de
continuidad referencia ambas fuentes para evitar historiales contradictorios.
