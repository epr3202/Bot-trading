# ADR 006-arming: Armado temporal y gestión separada

Estado: adoptado para bootstrap local, 2026-09-10.

Autorización en memoria ligada a cuenta/sesión/config/credenciales con gates y presupuesto. Entrada expira/reinicio desarma; gestión tiene permiso separado. Consecuencia: no persistir tokens de armado ni dejar una falsa sesión habilitada.

Ver BOOTSTRAP_SPEC.md y las especificaciones del módulo. Una revisión debe mantener
las restricciones superiores y actualizar código/pruebas junto a la decisión.
