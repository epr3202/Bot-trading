# ADR 005-order-lifecycle: Intención antes de envío

Estado: adoptado para bootstrap local, 2026-09-10.

Separar intención, ACK, fill, posición y UNKNOWN. Referencias estables y cantidades acumuladas; no exactly-once externo. Consecuencia: algunos incidentes requieren reconciliación/escalamiento y no se resuelven reenviando.

Ver BOOTSTRAP_SPEC.md y las especificaciones del módulo. Una revisión debe mantener
las restricciones superiores y actualizar código/pruebas junto a la decisión.
