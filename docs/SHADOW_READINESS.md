# Decisión de fase — 2026-09-14

**BLOCKED_BY_EXTERNAL_CONFIGURATION**. Motivo observado:
**ALPACA_CREDENTIALS_UNAVAILABLE**. **SHADOW_NOT_READY**.

Partida: `43c9cc5b7d6366ee72d38dd17542ec7341e4e7e1`, rama
`feat/phase3-readonly-evidence`, árbol e índice limpios. Se leyeron AGENTS,
STATUS, HANDOFF, TASKS y las especificaciones existentes antes de editar.
No hubo delegación, reconstrucción, cambios de ORB_RVOL_v0.1, riesgo o eToro.

Ambas variables dedicadas se comprobaron únicamente por presencia y resultaron
ausentes. No se buscaron secretos en perfiles, otros proyectos ni prompts.
La CLI oficial se ejecutó con `--capture --feed sip --target 2026-09-11`:
resultado ALPACA_CREDENTIALS_UNAVAILABLE antes de construir el cliente HTTP.
Salida del lanzador PowerShell: 1; salida semántica de main(): 2, probada por test.
Evidencia: `runtime/alpaca-audits/20260914T195435-d5744088/result.json`.
Se ejecutó sobre cambios locales con HEAD de partida; no se atribuye ese código
al commit inicial. No hay respuesta HTTP, autenticación ni entitlement observados.

Consulta prevista: Alpaca/AAPL/1Min/SIP/split, 2026-08-13 13:30Z a
2026-09-11 19:59Z inclusive: 20 sesiones previas + objetivo. Recuperadas: cero
sesiones, cero barras; requested_feed=sip, observed_feed=null, FEED_UNVERIFIED,
availability_class=HISTORICAL_DOWNLOAD y raw_sha256 vacío. No existe hash de
datos Alpaca, ni descarga efectiva, ni latencia medible.

ORH_independent, ORL_independent, V5_target, V5_previous_mean, RVOL_independent y
resultado real del motor: null / NOT_RUN. Los valores eToro anteriores pertenecen
a otro proveedor y otra sesión; no sustituyen estas métricas. Paridad Fraction/
Decimal y perturbación de futuro se comprueban solo con datos fabricados.

## Resultado y requisitos pendientes

1. Credenciales presentes, conexión y autenticación: BLOCKED. Responsable: titular
   del acceso; iniciar un proceso que herede ALPACA_API_KEY y ALPACA_API_SECRET y
   repetir el comando documentado. No pegar valores ni comprar/activar planes.
2. Feed observado, 21 sesiones y semántica empírica: BLOCKED. Las respuestas usuales
   no repiten feed; la petición SIP sola no satisface el criterio estricto de esta
   fase. Resolver evidencia del proveedor, manteniendo FEED_UNVERIFIED mientras falte.
3. Calidad y comparación independiente reales: BLOCKED. Completar el primer gate
   antes de ampliar. El software produce conteos por AAPL y agregado; datos inválidos
   no se rellenan y un parseo interrumpido deja conteos desconocidos.
4. Universo ampliado: NOT_STARTED, condicionado al primer gate. Propuesta fija del
   usuario: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, AVGO, NFLX; mínimo 60
   sesiones completas por símbolo, registrando cada exclusión. El capturador sigue
   limitado a AAPL/21; la ampliación no se implementa ni ejecuta antes de su gate.
5. Baseline real, sensibilidad 1x/2x/3x, métricas y OOS: NOT_STARTED. No hay ganancias,
   pérdidas, win rate, profit factor, drawdown, exposición, turnover, holding time
   ni concentraciones reales que reportar. Los escenarios de tests son sintéticos.
6. Disponibilidad histórica: bloqueo de investigación adicional. El motor conserva
   OBSERVED_AVAILABILITY_REQUIRED. Un snapshot descargado hoy no permite backdating
   de received_at/available_at; coincidencia numérica no demuestra replay causal.
   Antes del baseline real debe resolverse evidencia de disponibilidad compatible
   con el motor existente. No se autoriza reducir ese gate o simular latencia.
7. Interfaces/configuración shadow y WebSocket: NOT_STARTED, condicionadas al gate
   histórico, calidad y paridad. No se presentan como implementadas o verificadas.

## Gates obligatorios para una fase shadow futura

Todos requieren evidencia de una fase separada; ninguno queda aprobado por mocks
ni por este documento. Mientras falte uno, **SHADOW_NOT_READY**:

- MARKET_DATA_REALTIME_AUTH_VERIFIED
- SIP_REALTIME_FEED_VERIFIED
- CLOCK_SYNC_VERIFIED
- BAR_COMPLETENESS_VERIFIED
- STALE_DATA_GUARD_VERIFIED
- RECONNECT_VERIFIED
- NO_DUPLICATE_SIGNAL_VERIFIED
- NO_EXTERNAL_ORDER_PATH_VERIFIED

La preparación futura deberá definir event_timestamp, provider_receive_timestamp,
bot_receive_timestamp y decision_timestamp, distinguiendo campo disponible de
campo desconocido; umbral de frescura y políticas de datos stale, desconexión,
reconexión, duplicados, eventos tardíos y deriva de reloj. No se inventan marcas
temporales ni se conecta WebSocket durante esta fase.

READY_FOR_SHADOW_PHASE requiere todos los 19 criterios de la solicitud: acceso y
SIP real, 21 sesiones, ORH/ORL/RVOL coincidentes, volumen adecuado, dataset ampliado,
baseline y costes, revisión temporal, documentación, gates y Git limpios, sin
shadow ni Demo Write ni ruta externa habilitada. Esta fase no los cumple.
Aunque se cumplieran, el estado solo permitiría proponer la fase separada.

## Seguridad y alcance preservados

eToro DEMO_READ_VERIFIED es evidencia histórica comunicada por el usuario y
registrada localmente; no se vuelve a consultar la cuenta. entries_armed=false,
external_mutations=DISABLED, order_submission_enabled=false, Demo Write NOT_TESTED.
Solo se consultó documentación pública; cero peticiones de cuenta o trading,
cero órdenes externas, ningún shadow, WebSocket, compra, remoto o publicación.
Raw anterior inmutable; no se versionan datasets ni estado privado.

Los comandos, cobertura y commits observados se registran en
[VERIFICATION](VERIFICATION.md), autoridad única de comprobaciones de esta fase.

| Dimensión | Estado | Alcance |
|---|---|---|
| Software | VERIFIED | 512 pruebas, 16/16 gates; paquete instalado offline |
| Git | VERIFIED | Partida limpia; commits locales revisados, sin publicación |
| eToro Demo Read | OBSERVED | DEMO_READ_VERIFIED histórico comunicado; no repetido |
| Alpaca Authentication | BLOCKED | Variables ausentes, antes de red |
| Alpaca SIP Historical | BLOCKED | Sin respuestas ni feed observado |
| Data Quality | BLOCKED | Solo pruebas de software; cero datos Alpaca reales |
| ORB | IMPLEMENTED_NOT_VERIFIED | Estrategia intacta; comparación Alpaca real pendiente |
| RVOL | IMPLEMENTED_NOT_VERIFIED | Paridad local probada; RVOL Alpaca real pendiente |
| Real Historical Backtest | NOT_STARTED | Gate de datos no aprobado |
| OOS | NOT_STARTED | Sin muestra ni resultado OOS |
| Realtime | NOT_STARTED | Sin conexión ni autenticación realtime |
| Shadow | NOT_STARTED | SHADOW_NOT_READY; sin arranque |
| eToro Demo Write | NOT_STARTED | NOT_TESTED |
| External Mutations | VERIFIED | DISABLED; cero escrituras externas |
