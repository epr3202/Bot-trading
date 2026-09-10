# Tareas — continuidad de fase 2

| ID | Estado | Evidencia / pendiente |
|---|---|---|
| T01 | LOCAL_VERIFIED / GIT_IDENTITY_BLOCKED | Entorno y lock conservados; base reproducida/preservada, sin commits auténticos |
| T02 | LOCAL_VERIFIED | ORB/RVOL sin nuevos filtros; manifiesto/importación reforzados, 20 warmups intactos |
| T03 | LOCAL_VERIFIED | Intenciones, parciales, PnL, reinicio, propiedad y exposición observada vs contabilidad |
| T04 | CONTRACT_TESTED | Guardas de lectura/mutación y consultas de cierre; cuenta y contrato completo pendientes |
| T05 | LOCAL_VERIFIED / BLOCKED_DATA | Replay sintético, aritmética CSV independiente y futuro invariante; no investigación económica aprobada |
| T06 | HTTP_VERIFIED / CHROME_NOT_REPRODUCED | Mismo panel, controles Demo deshabilitados, dimensiones visibles; fallo de depuración local documentado |
| T07 | LOCAL_VERIFIED | 420 pruebas/16 gates/90,61%; paquete y evidencias en VERIFICATION, sin revisión independiente |
| X01 | NOT_CONFIGURED | Preflight propio solo lectura exit 2; requiere claves Demo Read del usuario |
| X02 | BLOCKED_EXTERNAL_DATA | eToro sin historia/volumen/finalidad suficientes; dos alternativas documentadas, ninguna contratada |
| X03 | DISABLED_THIS_PHASE | No primera escritura ni gestión externa; requiere futuro alcance explícito y gates resueltos |
| X04 | LOCAL_CONTRACT_TESTED / EXTERNAL_BLOCKED | Resolver enum de cierre v1, respuesta perdida sin ID, identidad/acumulación de fills y contabilidad final con evidencia del bróker |
| X05 | NOT_EXECUTED | CI remoto Windows/Linux y publicación no autorizados; no remoto creado |

La base previa de 358 pruebas se reprodujo; 62 escenarios adicionales llevan a 420,
sin borrar/omitir tests ni bajar cobertura. La expectativa del cierre sin propietario
se reforzó: bloqueo antes de leer; ahora existe matriz de cierres propios trazables.

Aceptación X04 local: intención persistida antes del envío simulado, ACK distinto de
fill, timeout sin reenvío, reinicio, partial/restante, duplicados, estados desconocidos,
404 y consultas fallidas, snapshots viejos, stop/horario y posiciones ajenas; cantidades
y PnL no se duplican. Esto no acredita una garantía ausente del contrato externo.

La identidad Git sigue siendo la única acción inmediata solicitada al usuario.
HANDOFF enumera los otros bloqueos. No construir otro motor/panel ni contratar datos
para simular resolución. Estados de datos, lectura, escritura y software son separados.
