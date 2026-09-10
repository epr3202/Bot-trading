# Continuidad — fase 2

Proyecto existente: C:/Users/epulgare/Nueva carpeta/Bot 3. Se conservó arquitectura,
Python 3.12.12, uv 0.12.12, lockfile, presupuesto y estrategia ORB_RVOL_v0.1.
No se repitió bootstrap ni se publicaron archivos. No se usaron subagentes en esta
fase: revisión propia del agente, sin auditoría independiente ficticia.

Base original preservada antes de modificar producto: docs/phase2-baseline.json
contiene hashes de 123 archivos del índice y working tree, versiones, pytest y lock.
runtime/phase2-baseline/reviewed-source.zip conserva bytes revisados sin privados;
SHA del manifiesto 96ac15232483b818eb9b4b88dac33d244f4ff1978d7453d311aa83194a0fe077.
El manifiesto no se incluye en su propio hash. Git main tiene 0 commits, sin remoto
ni identidad auténtica. índice original intacto; cambios de fase en working tree y
archivos nuevos sin staging. No equiparar la copia local o el índice con un commit.

Verificación de base reproducida: 358 pruebas/16 gates/90,43%. Regresión de incremento
final 2026-09-10T17:08:10.046894+00:00: 420 pruebas/16 gates/90,61%, sin skips ni fallos,
7 warnings visibles. Huella 75c12a9e7e320fff518d04dd10f26ad7c00557781d8ae0090ac6bbaf1a7d7e47.
Riesgo 100%, transporte 99,20%, autorización 98,40%, ejecutor 95,31%, persistencia
95,27%. docs/VERIFICATION conserva fallos intermedios y comandos/omisiones exactos.

Cambios: GuardedTransport bloquea toda mutación externa incluso con permisos viejos;
POST de coste/elegibilidad también limitado a mock en esta fase. Solo el mock exacto
recibe escrituras contractuales; nunca pasa por un cliente HTTP/mount de red. Cuota
conservadora global y por grupos, cinco plazas reservadas para reconciliar.

EtoroDemoAdapter._query_close ya correlaciona cuenta, intención, orden, posición
propia e instrumento. Lookup v2 de apertura observa remainingUnits/state/lastUpdate;
v1 de cierre observa unidades cerradas/occurred cuando son Únicas y coherentes.
Position separa units contables de observed_units/observed_at/accounting_complete.
Cero observado sin libro final no libera efectivo, riesgo ni permite otra venta.
La estructura JSON del esquema SQLite 1 sigue legible con defaults de campos nuevos.

Límite X04 aún abierto: v1 statusID no tiene enum público; perdida de respuesta sin
orderId no ofrece lookup por referencia garantizado; filas múltiples no tienen IDs
estables/acumulación especificada; rate/proceeds no certifican fees/taxes finales.
El historial v1 expone orderId y fees sin atribución suficiente a cada cierre/fill;
v3 solo admite aperturas. No se migró API ni se añadió una ruta de historial ficticia.
Estado externo de reconciliación BLOCKED; pruebas locales CONTRACT_TESTED. No abrir
ni cerrar posiciones del usuario para investigar esas ambigüedades.

El ejecutor/persistencia ahora bloquean falso flat ante consulta fallida, revisiones
de precio acumulado sin cantidad y observaciones atrasadas/contradictorias. Comisiones
tardías de cierre actualizan también PnL de posición. Stop/horario/manual comparten
la intención propia. Tests inyectan aceptación sin fill, antes/después de timeout,
crash tras persistir/antes de respuesta, parcial/restante, duplicados/reordenados,
rechazo, 404, cuenta/posición ajena y exposición cerrada con libro pendiente.

Datos: provider=fixtures; 26.910 barras, 20 warmups/3 evaluaciones, +200 ms sintéticos.
Importador conserva IDs, exige coherencia de synthetic/volume, cobertura con zona y
acquired_at para historical_download; impide backdating. Datos reales sin evidencia
observed no generan decisiones. El esquema no certifica licencia/recepción/universo.
Informes de datos reales y sintéticos no comparten directorio. No hay muestra real.

Recorrido nuevo probado: .\scripts\uv.ps1 run python scripts/verify_import.py.
Genera un directorio único y YAML registrado en runtime/import-evidence.json, luego
invoca los comandos existentes data validate y backtest. 8.190 barras/21 sesiones;
cálculo CSV independiente ORH=100,70 ORL=99,80 RVOL=3 y futuro alterado invariantes.
Salida en reports/runs/synthetic-import, sin shadow real observado. No hay bucle
futuro programado. No rebajar 20 sesiones, TTL, umbrales o costes para obtener señales.

X01: no ETORO_API_KEY/ETORO_USER_KEY en proceso ni .env del proyecto; preflight exit 2
CREDENTIALS_MISSING_OR_INVALID, NOT_CONFIGURED. Ninguna cuenta leída, ningún write.
Procedimiento Demo Read sin eco en docs/OPERATIONS_RUNBOOK.md. No extraer claves de
ChatGPT, otro conector o proyecto; preflight aprobado nunca arma esta fase.
X02: candles hasta 1000 sin fecha/cursor ni volumen/finalidad/ajustes demostrados.
Alpaca y Databento auditados documentalmente; capacidades reales, licencia y acceso
siguen pendientes. No adquirir planes o crear cuentas comerciales para desbloquear.
X03: TODAS las mutaciones externas DISABLED, incluso salidas; escritura NOT_TESTED.

Panel: HTTP/sintaxis JS pasan, dimensiones y unidades contables/observadas visibles,
controles Demo deshabilitados. Chrome exit 1: depuración local no arrancó; no elevar
permisos para salvarlo. Captura del bootstrap histórica, no reutilizable como evidencia
actual. Servidor/token de verificación retirados. No hay servicios instalados.

Única acción inmediata del usuario: configurar nombre/correo Git auténticos localmente
siguiendo docs/GIT_WORKFLOW.md. Después revisar el índice preservado y crear baseline
real antes de rama/commits coherentes del incremento. No global, no remoto, no push.
Los demás bloqueos constan arriba para la siguiente fase, sin preguntas repetidas.
