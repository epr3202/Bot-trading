# Gates independientes

| Gate | Prueba / criterio | Estado durante bootstrap |
|---|---|---|
| Software local | instalación congelada, lint/formato/tipos, suite, paquete, recorrido HTTP y CLI | Consultar STATUS y evidencia de última ejecución |
| Riesgo/transportes/ciclo | escenarios adversariales, cobertura objetivo ≥90% y ramas relevantes | Revisar runtime/coverage.json y resumen versionado |
| Recuperación | backup/restauración no destructiva, PnL e intenciones persistentes, doble proceso | tests/test_persistence_recovery.py |
| Bróker lectura | claves propias, identidad/permisos y portafolio Demo observados | NOT_CONFIGURED; no llamadas de cuenta |
| Bróker escritura | presupuesto, gates, armado temporal, smoke opt-in y gestión de salida | BLOCKED: runner y cierre reconciliado pendientes |
| Datos históricos | OHLCV negociado, cobertura, procedencia/licencia, disponibilidad, calidad | SYNTHETIC_ONLY en esta entrega |
| Investigación | protocolo temporal y criterios estadísticos registrados antes del test | RESEARCH_BLOCKED_DATA |

Fase 2: todos los gates locales originales se conservaron; 420 pruebas/16 checks.
El gate operativo de cierres sigue BLOCKED por contrato externo incompleto, aunque
su parte local/contractual está probada. Mutaciones externas DISABLED, escritura
NOT_TESTED. Chrome no se reprodujo en esta fase; pruebas HTTP del panel sí aprobadas.

Una prueba mock satisface el contrato local de transporte, no conexión al bróker.
OUT_OF_SAMPLE_EVALUATED no implica rentabilidad ni permite dinero real. Ningún gate
permite promoción automática. Los defectos detectados se registran, no se ocultan con skips.
