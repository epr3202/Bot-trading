# Tareas — cierre de fase 3

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
