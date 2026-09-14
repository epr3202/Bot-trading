# Tareas — Alpaca histórico, 2026-09-14

| Tarea | Estado |
|---|---|
| Proveedor Alpaca histórico separado de eToro | IMPLEMENTED; contrato MarketDataProvider preservado |
| SIP AAPL, 20 previas + objetivo | ATTEMPT_BLOCKED_BEFORE_NETWORK; feed efectivo desconocido |
| Volumen y parámetros | DOCUMENTED; no evidencia empírica Alpaca disponible |
| Mapeo, cuotas, páginas y feed identity | CONTRACT_TESTED |
| Comparación ORH/ORL/RVOL | SOFTWARE_TESTED; datos reales NOT_RUN |
| Shadow / órdenes / optimización | NOT_STARTED / DISABLED / NOT_PERFORMED |

Estado actual C: ALPACA_DATA_INSUFFICIENT_FOR_RVOL por contexto Alpaca no disponible;
no atribuirlo a entitlement. Próximo paso: captura desde proceso con variables dedicadas
ya configuradas, según docs/ALPACA_DATA_CONTRACT.md. Gates/commits en VERIFICATION.

## Hito anterior conservado — Market Data eToro

| Tarea actual | Estado |
|---|---|
| Preservar DEMO_READ_VERIFIED comunicado por el usuario | DONE; no repetir diagnóstico de cuenta |
| Capturar Market Data exclusivamente | DONE vía MCP; siete GET HTTP 200, raw y hashes locales |
| Identidad, quote, OHLC 1Min y sesión NY | AUDITED; AAPL/1001/Nasdaq; limitaciones temporales documentadas |
| Semántica de volume y 20 sesiones previas | BLOCKED; consolidación desconocida e histórico insuficiente |
| ORH/ORL/RVOL independiente y contraste motor | PARTIAL; ORH/ORL reales; RVOL y paridad numérica bloqueados; rechazo del motor comprobado |
| Shadow | NOT_STARTED_DATA_QUALITY_BLOCKED |
| Estrategia, riesgo y prohibición de mutaciones | PRESERVED |

Informe vigente: docs/ETORO_MARKET_DATA_VALIDATION.md. Gates y commits en VERIFICATION.
Las filas históricas X01 NOT_CONFIGURED de abajo quedan superadas por el hito Demo Read.

## Historia conservada — cierre de fase 3

| ID | Estado | Evidencia / siguiente acción |
|---|---|---|
| T01 Git | DONE | Identidad efectiva verificada. Base A y recuperación B preservadas sin mezclar staging; ramas locales y C reales |
| T02 Datos/estrategia local | LOCAL_VERIFIED | Mismos ORB/RVOL, 20 warmups y riesgo; importación sintética de B aprobada |
| T03 Ejecución/persistencia | LOCAL_VERIFIED | Propiedad, parciales, recuperación, costes y exposición separados; no inferir flat del cierre v1 |
| T04 Contratos | DOCUMENTED / CONTRACT_TESTED / PARTIALLY_BLOCKED | Matriz por campo en ETORO_API_AUDIT, v2 distinto de v1 y consultas de soporte no enviadas |
| T05 Investigación | BLOCKED_DATA | Ninguna muestra real validada, cálculo real, replay causal real ni shadow |
| T06 Panel | HTTP_VERIFIED / VISUAL_NOT_REPRODUCED | Chrome exit 1; depuración local no iniciada; sin cambios de seguridad |
| T07 Software | LOCAL_VERIFIED | A 358, B 420, C 435 pruebas; cada capa con su evidencia; 16 gates por batería |
| X01 | NOT_CONFIGURED | Titular: claves propias de aplicación y usuario Demo Read en el proceso; luego preflight existente |
| X02 | BLOCKED_EXTERNAL_DATA | Titular: archivo licenciado o acceso propio suficiente; 21 sesiones, mismo feed y semántica temporal auditada |
| X03 | DISABLED_THIS_PHASE | Ningún envío, cancelación, cierre o stop externo; resolver lectura no habilita mutaciones |
| X04 | EXTERNAL_NOT_OBSERVED / ACCOUNTING_BLOCKED | Soporte/integración: correlación legacy, fills/revisiones, costes finales y completitud del historial |
| X05 | NOT_EXECUTED | No remoto, CI remoto, publicación ni envío de preguntas a terceros |

Se añadieron únicamente regresiones de riesgos encontrados, sin modificar gates ni
umbrales para aumentar el recuento. El estado 2 de lookup quedó incluido junto con
los demás; 9/10 nunca se interpretan como cero ejecución. No se atribuyen las 420
pruebas de B a A ni las 435 de C a una conexión externa.

La fase termina aquí en cuanto a ampliación de producto. HANDOFF indica responsable,
evidencia faltante y acción mínima de cada dependencia. Identidad Git resuelta:
no pedirla otra vez. No crear fixtures ni infraestructura para ocultar X01/X02/X04.
