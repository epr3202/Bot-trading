# ADR 002-data-broker: Datos separados del bróker

Estado: adoptado para bootstrap local, 2026-09-10.

MarketDataProvider produce datos con procedencia y disponibilidad; ExecutionBroker administra órdenes. eToro candles no acredita volumen RVOL ni veinte sesiones. Consecuencia: el runner conectado queda bloqueado hasta disponer de fuente compatible.

Ver BOOTSTRAP_SPEC.md y las especificaciones del módulo. Una revisión debe mantener
las restricciones superiores y actualizar código/pruebas junto a la decisión.
