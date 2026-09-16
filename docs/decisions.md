## A7 WebSocket: spike bloqueado por handshake HTTP 403

Revision contractual permite eToro WebSocket conservando el gate de 3 s.
Diagnostico aislado: el handshake devuelve HTTP 403 con pagina Proxy WebGateway
EPM, antes de Authenticate; cero eventos, suscripciones u ordenes. No se ha
integrado el stream al runner ni se ha cambiado codigo productivo, riesgo,
Strategy 1, A6, Massive, contratos congelados o uv.lock. Reconnect productivo
y validacion en mercado abierto pendientes; no declarar migracion PASS.
Detalle: docs/A7_WEBSOCKET.md (desde docs: A7_WEBSOCKET.md).
A7 PARTIAL/BLOCKED: upgrade WebSocket rechazado por la infraestructura de red.

# Índice de decisiones

## A7 — continuación: preparación y diagnóstico externo, PARTIAL/BLOCKED

Se distingue rechazo previo al envío de UNKNOWN: preparación con intención
APPROVED, metadata durable y liberación de reservas solo con cero intentos de
mutación demostrados. Crash durante POST sigue UNKNOWN y nunca reenvía.
El usuario autorizó estímulo sintético A6 exclusivamente para el smoke Demo.
Identidad/scopes/elegibilidad/costes hipotéticos observados con credenciales
existentes PRESENT. La cotización externa falló: 81.588043s frente a máximo 3s.
Costes usa value frente a amount del esquema; contabilidad de cierre pendiente.
Cero órdenes/mutaciones. No se conectó aún el runner ni se habilitó Demo Write.
Detalles y partes pendientes: [continuación A7](A7_COMPLETION_ATTEMPT.md).
Las afirmaciones históricas de core intacto o UNKNOWN para todo rechazo quedan
actualizadas por este incremento; Strategy 1, riesgo, A6 y esquema se conservan.

## A7 — identidad fresca sin promover gates incompletos, 2026-09-16

La configuración, URL o presencia de demoCid no prueban acceso Demo: /me puede
incluir ambos CIDs. Se centraliza el acceso observado DEMO/REAL/UNKNOWN, con
scopes explícitos y portfolio Demo válido; UNKNOWN siempre rechaza. No se inventa
un campo isDemo ni se consulta portfolio Real. El adaptador y el transporte
comparten verificación fresca y comprueban el vínculo del permiso tras las lecturas.
La defensa inferior cubre llamadas directas y cambios entre revisión y despacho.
Se conserva la prohibición de mutaciones de red porque el runner A6 es sintético
y el cierre eToro no tiene normalización contable certificada. No sustituir esos
gates con booleans manuales. A7 PARTIAL/BLOCKED; [decisión completa](A7_DEMO_ONLY.md).

## A6 — frontera local fija y base vinculada a entradas, 2026-09-16

Se añade orquestación separada del OperationService antiguo para preservar el
recorrido fixture v0.1 y los bloqueos conectados. Strategy 1 v1, riesgo, Executor,
StateStore y SimulatorBroker se reutilizan sin cambios. A6 construye el simulador
concreto; no acepta adaptador externo ni factory. Contexto Demo por preflight con
MockTransport, siempre SIMULATED; no usar evidencia A5 antigua para armar nada.
La base offline dedicada se vincula mediante hash de configuración, barras y
entradas explícitas. Cambios de inputs requieren otra base. Idempotencia/UNKNOWN/
reservas/propiedad siguen en el core existente; no nuevo protocolo exactly-once.
Cierre local exige bid explícito vigente y reconciliación flat; parcial queda
BLOCKED. Sin migración ni escritura externa. [A6](A6_SESSION.md).

## A5 — evidencia conjunta Demo y barrera GET, 2026-09-16

Se reutiliza el preflight existente: demoCid positivo, scopes Demo explícitos sin
permisos reales/wildcards y respuesta válida de portfolio Demo. No se inventa
isDemo; realCid en me no implica lectura de cuenta real. Ausencia de scopes para
claves bloquea, sin inferencia por configuración. JSON duplicado, IDs ambiguos,
campos inválidos o HTTP inesperado fallan cerrados. El transporte usado queda
restringido a tres GET incluso con mocks/autorización previa; no reutilizarlo para
operar. Metadata compartida del símbolo A2 no acredita elegibilidad ni RVOL;
credit no se llama efectivo reconciliado ni se le inventa moneda.
El catálogo oficial se revalidó. La continuación cargó las claves existentes de
.env con uv --env-file .env, sin cambiar el código ni las protecciones. CLI real
PASS: tres GET/HTTP 200. La ausencia previa era del entorno exportado, no del archivo.
La red restringida falló con WinError 10061; el entorno autorizado permitió el
PASS con TLS conservado. No introducir carga implícita que altere tests/offline. Evidencia y límites en [A5](A5_PREFLIGHT.md).

## A4 — contrato temporal aprobado por el responsable, 2026-09-15

La autorización explícita actual sustituye la parada anterior. historical_download
se conserva como procedencia; observed en replay solo significa visible al reloj.
replay_as_of_v1 prioriza publicación explícita; las capturas A2 no la contienen y
su intervalo t/inicio +60s está documentado inequívocamente. Se adopta ese cierre
como disponibilidad lógica modelada, nunca como evidencia de publicación realtime.

Se preservan barras/recepciones originales y se persiste el vínculo por registro.
No hay reclasificación global, cambio de Strategy 1 o rebaja del gate observed.
Lotes simultáneos atómicos y decisión terminal fija evitan depender del orden de
símbolos o permitir entradas retrospectivas con benchmarks tardíos.

Se reutiliza el registro de resultados existente y se fija SHA-256 de referencias
aprobadas A2/A3; sus cambios requieren revisión explícita. La identidad incorpora
commit y SHA-256 del árbol real, configuración/calendario y schedule temporal.
Comparación exacta de resultados completos, trades incluidos; solo se excluyen
started_at/finished_at informativos. Contexto Decimal local de precisión 28,
Python/lock fijados. [Contrato y límites](REPLAY_AS_OF_V1.md), [runs](A4_READINESS.md).

## A4 — parada por incompatibilidad temporal, 2026-09-15

Se mantienen sin alterar identidades A2 (SHA-256 de capture.json/páginas del
manifiesto aprobado) y A3 (snapshot, configuración efectiva y SHA-256 de fuentes).
El rechazo OBSERVED_AVAILABILITY_REQUIRED impide cumplir A4: no se transforma
historical_download en observed ni se retrofechan received_at/available_at.
Igualdad de dos resultados vacíos por bloqueo no demostraría un backtest válido.
El commit base se distingue de la huella del árbol con cambios A2/A3 sin commit.

No se introduce arquitectura o metadata paralela. La propuesta diferida reutiliza
BacktestResult/save_report/append_experiment; metadata de ejecución se excluiría
de comparación, nunca tiempos de operaciones ni valores/orden de trades o summary.
Resolver un contrato explícito de disponibilidad modelada requeriría una tarea y
versionado separados; no queda aprobado aquí. [Diagnóstico](A4_READINESS.md).

## A3 definitivo — decisiones E1 del responsable, 2026-09-15

- **B1 / A3-RS:** ORB_RVOL_v1.0 exige retorno desde apertura regular hasta candidata
  superior estrictamente a SPY y QQQ simultáneamente. Margen 0, sin fallback;
  datos sincronizados disponibles al decidir. Empates/faltantes/tardíos rechazan.
- **B2 / A3-REGIME:** no se utiliza filtro de régimen en v1.
- **B3 / A3-VWAP:** VWAP no confirma entradas; capacidad HLC3 conservada.
- **B4 / A3-UNIVERSE:** solo acciones comunes elegibles USD XNYS/XNAS; ETF fuera,
  SPY/QQQ exclusivamente referencias. No es una limitación técnica temporal.

Las cuatro decisiones sustituyen los pendientes históricos inferiores. La primera
candidata ORB sigue siendo terminal: si falla RS no se buscan entradas posteriores.
La evaluación no espera a benchmarks tardíos ni cambia el instante de señal.
No se añade short a la estrategia larga existente. Parámetros/riesgo/costes previos
preservados, config explícita y fuentes verificables en snapshot.
**A4 debe ejecutar Strategy 1 v1 exactamente como queda congelada al cerrar A3.**
Cambios posteriores requieren nueva versión; no se eligen reglas mediante A4.

## A3 — evidencia histórica y propuestas B1–B4, 2026-09-15

Revisados los 15 commits alcanzables localmente, pickaxe, blame, diffs y árboles.
Se recupera E1 en bootstrap inicial: ETF excluidos explícitamente, SPY/QQQ solo
referencias y extensiones desactivadas. FUT-001/FUT-002 confirman reglas pendientes;
no existe aprobación histórica de filtros activos ni ampliación ETF.
E1 de exclusión no resuelve la solicitud ampliada: **A3 BLOCKED**.
Opciones, complejidad, efectos, información faltante y preguntas de aprobación
en [A3_PENDING_DECISIONS](A3_PENDING_DECISIONS.md). Todas PROPOSED, ninguna adoptada.

## A3 — no congelar reglas indefinidas, 2026-09-15

**A3 BLOCKED**. Bootstrap, ADR 003, código y YAML coinciden: ORB_RVOL_v0.1
excluye ETF y mantiene RS/régimen/VWAP desactivados. La solicitud A3 contempla
esos elementos; faltan reglas de entrada y la resolución del universo. No inventar
umbrales ni convertir el NOT_APPLICABLE de A2 en aprobación de A3.
La decisión pendiente del usuario es conservar explícitamente esas exclusiones
o especificar una nueva versión. Detalle B1–B4 en [auditoría](STRATEGY_1_A3_AUDIT.md).

**A4 consume Strategy 1 congelada; A4 no modifica Strategy 1 para mejorar resultados.**
Todo cambio de filtros, parámetros, universo, riesgo o entradas/salidas requiere
nueva versión y reabrir A3 o una tarea equivalente. A4 no se inicia.

## A2 — decisiones de validación, 2026-09-15

Se conserva RVOL de cinco minutos contra las veinte aperturas inmediatamente
anteriores y calendario XNYS, zona IANA America/New_York.
Exigir todas las barras regulares; ningún relleno ni salto de
sesiones. SPY/QQQ solo amplían la allowlist histórica, con validación de identidad
por respuesta y página; no se abre un selector arbitrario de instrumentos.
VWAP usa HLC3 existente y volumen v; no requiere vw opcional ni se afirma exactitud
trade-a-trade. Comparación independiente con tolerancia Decimal 1e-20; ORB/RVOL
conservan igualdad exacta. RS usa el mismo intervalo desde apertura en los tres
símbolos. Régimen NOT_APPLICABLE: falta regla en v0.1, no se inventa para A2.
JSON con hashes reutiliza el patrón existente; raw privado inmutable fuera de Git.
Provenance NETWORK_HTTP es trazabilidad local, no firma criptográfica del proveedor.
La evidencia de acceso real son las capturas observadas, nunca tests fabricados.

## A1 — selección histórica Massive, 2026-09-15

Se reutiliza `data.path` como directorio de captura Massive, sin nuevos campos.
La configuración exige directorio existente; el lector valida el contenido.
`data.manifest` externo se rechaza para Massive: la fuente es capture.json dentro
de path. Fixtures/import mantienen sus contratos. El dispatch enumera los tres
proveedores y propaga errores; nunca usa fallback automático a fixtures/import.
Massive sigue separado de broker/ejecución: esta ruta carga histórico offline,
sin autenticación/red, y conserva HISTORICAL_DOWNLOAD y el gate observed.
No se modifica la estrategia ni se avanza a A2.

Las decisiones de arquitectura canónicas permanecen en [adr](adr):
[solo virtual](adr/001-demo-only.md), [datos/bróker](adr/002-data-broker.md),
[estrategia](adr/003-strategy-v01.md), [ejecutor](adr/004-single-executor.md),
[órdenes](adr/005-order-lifecycle.md), [armado](adr/006-arming.md) y
[backtest](adr/007-backtest.md).

Decisión de 2026-09-14: [BLOCKED_BY_EXTERNAL_CONFIGURATION](SHADOW_READINESS.md).
Ausencia de credenciales se distingue de insuficiencia de datos; una query SIP
no acredita feed observado; duplicados no aprueban calidad; histórico descargado
no se reclasifica como recepción realtime. Las reglas ejecutables y la taxonomía
pertenecen a [ALPACA_DATA_CONTRACT](ALPACA_DATA_CONTRACT.md).
