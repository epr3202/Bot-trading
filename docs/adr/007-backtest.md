# ADR 007-backtest: Replay de minutos conservador

Estado: adoptado para bootstrap local, 2026-09-10.

Señal conocida al recibir barra completa; orden aceptada tras latencia, fill posterior por minuto, stop ambiguo adverso, fees explícitos. Consecuencia: no precisión tick; fixtures prueban ingeniería y mantienen RESEARCH_BLOCKED_DATA.

Ver BOOTSTRAP_SPEC.md y las especificaciones del módulo. Una revisión debe mantener
las restricciones superiores y actualizar código/pruebas junto a la decisión.
