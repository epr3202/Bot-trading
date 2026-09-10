# ADR 004-single-executor: SQLite y ejecutor único

Estado: adoptado para bootstrap local, 2026-09-10.

Monolito con bloqueo OS no expirable, SQLite WAL/FULL y transacciones de intención/reserva. Consecuencia: no escala horizontalmente; un proceso vivo detenido conserva propiedad y no autoriza reemplazo automático.

Ver BOOTSTRAP_SPEC.md y las especificaciones del módulo. Una revisión debe mantener
las restricciones superiores y actualizar código/pruebas junto a la decisión.
