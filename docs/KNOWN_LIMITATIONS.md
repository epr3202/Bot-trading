# Limitaciones verificables

## Vigente — 2026-09-14, antes de fase shadow

Decisión: BLOCKED_BY_EXTERNAL_CONFIGURATION, ALPACA_CREDENTIALS_UNAVAILABLE;
no es evidencia de datos insuficientes ni suscripción faltante. No hay autenticación,
feed SIP observado, histórico Alpaca o RVOL real. Reportes de calidad/aritmética
solo están comprobados con muestras fabricadas. Un error de parser conserva
conteos desconocidos; no existe informe ampliado real de 60 sesiones.

Feed explícito en query es solicitud contractual; sin eco en cada página se
mantiene FEED_UNVERIFIED. El servidor habitual no repite ese campo: queda pendiente
resolver evidencia del proveedor sin inventarla ni ampliar rutas de cuenta.
El motor conserva OBSERVED_AVAILABILITY_REQUIRED: snapshots históricos y paridad
numérica no certifican replay causal ni habilitan baseline real con backdating.

Universo ampliado, métricas/1x-2x-3x reales, OOS, interfaces shadow y realtime:
NOT_STARTED, sujetos a gates previos. No se declara rentabilidad ni ventaja.
eToro Demo Read conserva su hito histórico comunicado; no se repitió la cuenta.
Demo Write NOT_TESTED; mutaciones DISABLED; no shadow. [Detalle](SHADOW_READINESS.md).
Los estados NOT_CONFIGURED/SYNTHETIC_ONLY siguientes son historia anterior.

Fase 3 prevalece sobre el antecedente siguiente: 435 pruebas / 16 gates locales;
identidad Git resuelta y capas A/B/C versionadas. Lookup v2 sí describe aperturas,
cierres, estados y exposición. Faltan garantías contables de cierre, no todo el
contrato de reconciliación. Ya no se infiere exposición restante de units v1.
Demo Read NOT_CONFIGURED; muestra pública no descargada (WinError 10061) y candidata
insuficiente (limit=4). Sin datos reales auditados ni shadow. Chrome no reproducido,
HTTP verificado. Matriz y responsables en ETORO_API_AUDIT y HANDOFF.

Actualización fase 2: 420 pruebas/16 gates locales aprobados; Chrome no inició su
depuración local y la verificación visual de esta fase no está reproducida. Todas
las mutaciones externas permanecen DISABLED. Las siguientes carencias externas
siguen abiertas, con reconciliación local reforzada en ORDER_LIFECYCLE.

Cierre v1: ya se valida trazabilidad y cantidad observada, pero no hay enum público
statusID, recuperación garantizada si se pierde orderId ni contrato de comisiones
finales/identidad de fills múltiples. `units` contables no desaparecen por observar
cero; se conserva accounting_complete=false y capital inmovilizado hasta evidencia.
El historial y v3 fueron revisados y no resuelven esos límites documentales.

Manifest: ahora rechaza etiquetas sintéticas incoherentes y recepción anterior a una
descarga histórica declarada. La procedencia observada sigue siendo una declaración
que requiere auditoría; no basta pasar el parser para marcar REAL_SAMPLE_AUDITED.

1. Ninguna credencial propia ni lectura/escritura de cuenta fue validada. Los mocks
   no demuestran conexión. La CLI Demo devuelve BLOCKED, sin sustitución sintética.
2. Falta orquestador de sesión Demo validado, feed OHLCV compatible, sizing con reglas
   de instrumento de cuenta, equity utilizable y reconciliación completa de cierre v1.
   Existe adaptador contractual con guardas, pero no debe activarse directamente.
3. eToro candles ofrece hasta 1000 barras sin fecha/cursor documentados en el contrato
   elegido. Consolidación de volumen, finalidad, retraso y licencias no demostrados.
4. Solo fixtures: 26.910 barras, tres símbolos inventados claramente etiquetados,
   veinte warmups y tres sesiones de evaluación. No son histórico ni prueba de ventaja.
5. Backtest por minutos aproxima ejecuciones y stops; la secuencia intrabar, profundidad,
   colas, suspensiones reales y slippage de mercado no están medidos. Drawdown es diario.
6. Importador verifica forma, timestamps y checksum; procedencia/licencia/ajustes y
   universo punto-en-el-tiempo declarados requieren validación humana independiente.
7. Fuerza relativa/VWAP tienen helpers; régimen, beta y retroceso requieren hipótesis y
   variantes propias. Todos los filtros de extensión permanecen desactivados.
8. El dashboard administra el simulador local. Los controles de Demo muestran su gate;
   no existe supervisor externo activo ni alertas remotas, servicios o tareas programadas.
9. Pruebas ejecutadas en Windows; compatibilidad Linux tiene código y CI, aún no ejecución
   remota. Deprecaciones de FastAPI/Starlette/NumPy se conservan visibles.
10. Scanner de secretos por patrones, no una garantía absoluta. Revisión Git sigue siendo
    obligatoria. Estado real de commits/identidad/remoto se registra en HANDOFF.
