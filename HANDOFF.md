# Continuidad — Market Data, 2026-09-14

El usuario confirmó DEMO_READ_VERIFIED desde Bot 3, con conexión, autenticación e
identidad Demo verificadas y cero escrituras. Hito registrado en baseline.json,
sin repetir consultas de cuenta. X01 de las secciones históricas está superado;
no pedir claves ni reiniciar diagnóstico de conectividad.

Esta fase obtuvo siete respuestas HTTP 200 exclusivamente Market Data mediante
execute_read del conector eToro. La consulta local de instrumentos no pudo iniciarse
con el contexto de proceso del agente; no se atribuye al bot la captura MCP.
Datos reales, sin mocks de adquisición: AAPL/1001/Nasdaq, bid/ask, 1.000 minutos
asc/desc, 30 diarios y repetición de 10 minutos. No se consultó elegibilidad, cuenta,
portafolio ni otra ruta de trading. No se cambió la allowlist del transporte.

Resultado: ETORO_MARKET_DATA_INSUFFICIENT_FOR_RVOL. Volumen de unidades desconocidas;
0/20 sesiones previas completas, 0/20 aperturas históricas. La ventana regular actual
no tiene huecos entre minutos ya cerrados, pero el histórico requerido no cabe en
el contrato de 1.000 velas sin fecha/cursor. ORH=334,54, ORL=331,72 y volume de
apertura=1.181.044 calculados independientemente sobre AAPL 2026-09-14. RVOL y
comparación numérica con el motor bloqueados; este rechaza con
OBSERVED_AVAILABILITY_REQUIRED, sin alterar ninguna regla ni falsear disponibilidad.

Raw: data/raw/etoro-market-20260914T164913. Informe/CSV/manifiestos y hashes:
runtime/market-audit-20260914T164913/final-analysis. Cuerpos raw inmutables, revisiones
separadas y sin datos privados en Git. `scripts/audit_etoro_market_data.py` reproduce
el análisis sin red; requiere directorio de salida nuevo. Diez regresiones nuevas
cubren exclusión de vela abierta, huecos/duplicados, denominador sin hoy, OHLC,
zonas y cierre temprano. Estado de gates en VERIFICATION.

Batería final: 453 pruebas sin fallos/skips, 16/16 gates, cobertura 90,686683%.
Huella estable y lock intacto; evidencia final en final-gates dentro de la carpeta
de auditoría. Commit local `2d6eec3` conserva el cambio previo de proxy/CA; el commit
de auditoría contiene este informe y el analizador sin red. No hay publicación.

Shadow NO INICIADO. Se mantienen entries_armed=false, external_mutations=DISABLED,
order_submission_enabled=false, etoro_demo_write=NOT_TESTED. El parser de quote
rechaza el timestamp sin offset observado; el análisis lo interpreta como UTC por
contrato y mide 43,076s hasta retorno de herramienta, por encima del gate de 3s.
Esto también impide tratar la captura como cotización fresca operativa.

Siguiente dependencia: volumen consolidado/ajustes acreditados y 21 sesiones de
minutos de un proveedor apto, preservando MarketDataProvider e importación existentes;
o aclaración contractual de eToro y cobertura demostrada. No reducir warmup ni usar
volumen diario/ticks para simular RVOL. Los bloqueos contables X04 siguen vigentes;
resolver datos tampoco autoriza Demo Write. Detalle en ETORO_MARKET_DATA_VALIDATION.

## Historia conservada — fases anteriores

Actualización 2026-09-14: el usuario solicitó adaptar el manejo de proxy del script
de oficios. Se revisó `oficios.py` en la carpeta de generación/recuperación sin
ejecutarlo ni importar credenciales. `create_http_client` aplica proxy del entorno
y prioridad CA local `certs/epm-root.cer` → `REQUESTS_CA_BUNDLE` → defaults HTTPX.
No se desactiva TLS ni se cambia configuración global. CA/proxy inválidos producen
error redactado sin fallback. Transportes inyectados no heredan el entorno; el
panel local mantiene conexión directa. No cambian guardas de escritura, identidad,
reservas, propiedad, recuperación ni datos/tiempos de disponibilidad.

Verificación: ocho pruebas nuevas aprobadas con
`.\scripts\uv.ps1 run --frozen pytest -q tests/test_corporate_network.py`.
Primer pase completo: 15/16 gates; dos pruebas nuevas parcheaban el símbolo
incorrecto de HTTPX. La guarda de sockets bloqueó la conexión externa y hubo
resolución DNS fallida del proxy ficticio; ninguna consulta de cuenta ni respuesta
externa. Se corrigió el aislamiento. Evidencia inicial conservada en
`runtime/proxy-verification-first.json`. Batería final:
`.\scripts\uv.ps1 run --frozen python scripts/verify.py`, salida 0;
16/16 gates, 443 pruebas sin errores/fallos/skips, cobertura 90,686683% y módulos
críticos por encima del 90%. Ruff check/format, mypy, escaneo de secretos, recorridos
offline, bloqueos negativos, build y sintaxis JS aprobados. Evidencia exacta en
`runtime/verification.json`, credenciales retiradas y código estable durante checks.

Construcción del cliente con entorno actual aprobada, sin solicitudes HTTP.
Proxy presente; CA corporativa no configurada ni encontrada en la carpeta de
referencia. Falta aportar CA autorizada mediante la ruta/variable documentada en
OPERATIONS_RUNBOOK y comprobar conectividad en un alcance autorizado. No se
realizaron lecturas de cuenta, operaciones externas, commits ni publicación.
Python 3.12.12 y uv.lock conservados. Los bloqueos históricos siguientes permanecen.

Proyecto existente C:/Users/epulgare/Nueva carpeta/Bot 3. Se mantuvieron Python
3.12.12, uv 0.12.12, uv.lock, ORB_RVOL_v0.1, 20 warmups, presupuesto, riesgo y TTL.
No hubo nuevo repositorio, migración de API, proveedor nuevo ni revisión independiente.
Revisión propia del agente; no se delegó esta fase.

Las dos capas ya están versionadas. Base A en main:
`6af05f1b16b8e3488a5cd959dc0e7f889b258fd6` (123 archivos idénticos al índice
original y su manifiesto, 358 pruebas en instalación aislada).
B en recovery/phase2-reviewed:
`ef8bf5564f6e15bd04ae084c18cd63dd27ba380b` (33 modificados + seis nuevos,
420 pruebas, importación y paquete offline).
C en feat/phase3-readonly-evidence:
`b51506a97771d04a5edfb45d46e8fac4c31f307f` (435 pruebas/16 gates).
La documentación de fase 2 que menciona identidad pendiente queda conservada en B
como historia; el bloqueo fue resuelto por el usuario. No volver a solicitarlo.

Fase 3 corrigió riesgos concretos: lookup exige exactamente un identificador;
una respuesta action=close no se contabiliza como apertura; status.id debe ser
entero y los estados 3/5/9/10 requieren evidencia de cantidad ejecutada. Los estados
9/10 conservan fills aunque su remanente sea terminal. El detalle v1 de cierre ya
no permite inferir remainingUnits a partir de la cantidad solicitada. La exposición
explícita del lookup de apertura continúa separada del libro, caja y PnL.

Lookup v2 sí documenta action=open/close, IDs de cuenta/orden/posición y estado.
OpeningData sigue siendo apertura; no existe closingData en el esquema consultado.
No extrapolar el enum v2 a statusID v1. Matriz de campos, diferencias guía/OpenAPI,
idempotencia por versión y preguntas de soporte NO ENVIADAS en ETORO_API_AUDIT.
La normalización contable de cierres y recuperación legacy sin ID siguen bloqueadas.

| Bloqueo | Responsable | Evidencia pendiente | Acción mínima |
|---|---|---|---|
| X01 Demo Read NOT_CONFIGURED | Titular de cuenta/aplicación | Clave de aplicación y clave de usuario Demo Read en el proceso; identidad/scopes/portfolio verificados por el bot | Configurarlas localmente según OPERATIONS_RUNBOOK y ejecutar el preflight existente una vez tras el cambio; no pegar secretos |
| X02 BLOCKED_DATA | Titular del acceso/dataset | CSV/Parquet autorizado, 21 sesiones completas, volumen comparable, ajustes/procedencia/tiempos; o acceso ya licenciado sin gasto | Aportar el archivo y manifiesto localmente; el candidato público de cuatro registros es insuficiente y su descarga falló con WinError 10061 |
| X04 Contabilidad externa BLOCKED | Soporte eToro y responsable de integración | Enlace v1→lookup, enum legacy, fills estables/revisiones, costes/moneda y completitud histórica | Obtener aclaraciones contractuales; revisar ejemplos redactados de operaciones existentes solo con acceso autorizado; no crear operaciones de prueba |
| Visual NOT_REPRODUCED | Responsable del entorno local | Arranque de depuración Chrome y captura actual | Investigar en un entorno permitido; esta fase agotó su único intento sin cambiar seguridad ni cerrar sesiones personales |
| X03 Mutaciones DISABLED | Futuro alcance explícito del usuario | Todos los gates operativos y autorización separados | No activar nada al resolver lectura o datos |
| X05 CI remoto/publicación | Usuario, si lo solicita en otro alcance | Destino y autorización explícitos | Ninguna acción ahora |

Preflight real del proceso: 2026-09-10T19:24:54Z, exit 2; ETORO_API_KEY y
ETORO_USER_KEY ausentes, sin .env. Ninguna consulta de cuenta. Las suites también
ejercitan el caso negativo con credenciales retiradas; no equivalen a reintentos de
la configuración real. El conector solo aportó catálogo/OpenAPI.

La búsqueda pública de datos fue acotada a los proveedores ya auditados. No se
adquirieron servicios, créditos ni suscripciones. No hay archivo real validado ni
ORH/ORL/RVOL real calculado. Un histórico final real no es sintético por carecer de
recepción histórica: puede permitir aritmética exploratoria, pero no sortear el
gate observed del motor ni demostrar latencia. Sin shadow ni tarea futura.

Panel HTTP aprobado; Chrome salió 1 a las 19:33:13Z por depuración no iniciada.
Servidor de comprobación cerrado y token retirado. No usar captura del bootstrap
como verificación actual. Las guardas de mutación siguen cubiertas por tests con
transporte espía, incluidos permisos antiguos: ninguna solicitud de escritura
llega a la red. La consulta del bróker no está conectada al runner operativo.

Evidencia local ignorada: runtime/phase3 (A aislada, B/C suites, huellas de capas,
preflight, descarga fallida y navegador). Evidencia portable y matriz Git en
docs/VERIFICATION.md y docs/GIT_WORKFLOW.md. El commit documental posterior a C
no cambia software. Consultar `git log --format=fuller` y `git status --short`
para el historial y estado reales. Sin remotos, publicación o mutación de cuenta.

Criterio de parada alcanzado: capas preservadas, revisión contractual focalizada
agotada y recorridos externos posibles intentados. No abrir otra ronda de motores,
fixtures o interfaz para sustituir las dependencias anteriores.
