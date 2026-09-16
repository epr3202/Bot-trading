## A7 WebSocket: spike bloqueado por handshake HTTP 403

Revision contractual permite eToro WebSocket conservando el gate de 3 s.
Diagnostico aislado: el handshake devuelve HTTP 403 con pagina Proxy WebGateway
EPM, antes de Authenticate; cero eventos, suscripciones u ordenes. No se ha
integrado el stream al runner ni se ha cambiado codigo productivo, riesgo,
Strategy 1, A6, Massive, contratos congelados o uv.lock. Reconnect productivo
y validacion en mercado abierto pendientes; no declarar migracion PASS.
Detalle: docs/A7_WEBSOCKET.md (desde docs: A7_WEBSOCKET.md).
A7 PARTIAL/BLOCKED: upgrade WebSocket rechazado por la infraestructura de red.

# A7 — PARTIAL / ejecución externa BLOCKED

## A7 — auditoria UTC/costes, PARTIAL/BLOCKED (2026-09-16)

La evidencia anterior era 81.588043 s, no 81588 s; ambiguedad de coma decimal.
Dos GET rates nuevos confirmaron retrasos de 35.860831 y 75.107782 s.
Recepcion HTTP registrada antes del parseo, UTC aware; limite 3 s intacto.
Costes value/amount normalizados dentro del adapter; fixture real sanitizado.
142 pruebas focales A7/A6 PASS. Gate externo QUOTE_STALE_OR_DELAYED;
cero ordenes/mutaciones; identidad DEMO y parser de costes PASS.
No se habilita el vertical de trading mientras falle frescura. No A8.
Detalle, cambios, comandos y evidencia: [auditoria A7](A7_QUOTE_COST_AUDIT.md).


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

2026-09-16. A7 está autorizado por el usuario. Se implementa la defensa de
identidad; **no se habilita todavía la ejecución automática externa**. La
prohibición histórica de iniciar A7 queda superada; sus dependencias técnicas no.
No confundir pruebas HTTP simuladas con DEMO_WRITE_VERIFIED.

## Diagnóstico y flujo

Antes de editar: AGENTS y guías locales, STATUS/HANDOFF/TASKS, contexto,
arquitectura, decisiones, changelog, pendientes, auditoría eToro, lifecycle y
riesgo revisados. Git ya contenía trabajo A2–A6 sin commit; se conserva.
Baseline focal: 364 passed, 5 warnings, 0 fallos, 29.95s, exit 0.
Huella inicial por archivo: runtime/a7/baseline-hashes.json.

Flujo existente:

`scripts/run_a6.py → DemoSessionRunner → ORBStrategy → EntryRequest →
Executor/RiskEngine → StateStore (reserva + intención durable) → SimulatorBroker
→ Executor.reconcile → cierre local`.

A6 fija SimulatorBroker, modo offline y datos sintéticos. No admite inyección
de un broker externo. CLI/OperationService rechazan sesiones conectadas.
EtoroDemoAdapter existe aparte, pero GuardedTransport.require_contract_transport
solo permite el MockTransport exacto para POST/PATCH/DELETE. No hay un runner
automático que lo active. No se añade un camino estrategia → HTTP directo.

## Implementación segura disponible

- brokers/identity.py centraliza AccountType DEMO/REAL/UNKNOWN, interpretación
  de /me y validación del portfolio Demo. El modelo clasifica acceso observado,
  no a la persona: un perfil puede contener ambos CIDs. REAL es exclusivamente
  un resultado de rechazo, nunca un modo ni un adaptador.
- perform_preflight conserva su restricción irreversible GET y reutiliza
  GuardedTransport.observe_demo; no carga .env ni arma órdenes.
- EtoroDemoAdapter._authorization comprueba la identidad antes de avanzar con
  submit/cancel/close/protect. Las validaciones locales siguen evitando lecturas
  para intenciones inválidas o posiciones sin propietario.
- GuardedTransport.request vuelve a verificar antes de cada mutación, incluso
  si otro caller evita el adaptador. No acepta un objeto de identidad aportado
  por el caller ni usa la autorización antigua como prueba suficiente.
- Ambas capas reutilizan verify_mutation_identity: GET /me, GET portfolio Demo,
  coincidencia de cuenta con autorización, scopes write Demo actuales y vínculo
  exacto con credenciales/sesión/configuración. Se comprueba la caducidad también
  después de las lecturas. Fallo invalida la autorización.
- Se exige HTTP 200 para identidad/portfolio y se rechazan campos JSON
  duplicados. Identidad incompleta, real, mixta, wildcard, ambigua, modificada,
  read-only o inaccesible bloquea. IDs/PII y respuesta de error no se registran.

El origen y la allowlist Demo siguen fijos. No hay base_url/account_id/username
configurables para trading ni modo real/live/production. Cambiar las claves
invalida el permiso; variables de entorno que aparenten Demo no prueban identidad.
settlementType="real" en el contrato existente significa subyacente frente a
CFD dentro de una ruta Demo: no selecciona una cuenta de dinero real.

**La barrera de red permanece.** También con Demo válida, la mutación solo puede
llegar al MockTransport de pruebas. No se añade flag que levante esa barrera.
La defensa nueva no se presenta como autorización para quitarla más adelante.

## Estado y límites de persistencia

No cambian Executor, RiskEngine, StateStore, schema, Strategy 1 o A6. Las pruebas
con SQLite ejercitan riesgo → reserva/intención SUBMITTING → adaptador → ACK →
lookup/fill, con HTTP simulado. ACK sigue sin equivaler a FILLED.
En rechazo de identidad el adaptador lanza un BrokerBlocked estático, sin mutar
la intención ni inventar posiciones. El Executor existente conserva UNKNOWN,
pausa entradas y retiene reservas ante excepciones de envío; no reenvía. Su
auditoría SUBMISSION_AMBIGUOUS no distingue aún el rechazo previo del resultado
ambiguo posterior. Esta limitación queda explícita, no se certifica un runner A7.

## Bloqueos para conectar el runner

1. Feed operativo con disponibilidad observada y calentamiento compatible con
   ORB/RVOL y benchmarks. A2/A4 históricos y el fixture A6 no lo acreditan.
2. Elegibilidad, precisión de unidades, costes y stop nativo efectivos por cuenta
   e instrumento, sin usar valores sintéticos de configuración como evidencia.
3. Contabilidad de cierres y recuperación verificable. Se reconsultaron las
   especificaciones oficiales getMe, getTradingInfoDemoOrdersLookup y
   getTradingInfoDemoCloseOrdersByOrderId el 2026-09-16, solo documentación.
   Lookup v2 admite action=close pero expone openingData, no closingData.
   Close v1 conserva statusID sin enum y referenceID nullable, con unidades,
   precio y fecha opcionales. No acredita aquí fills estables, atribución/finalidad
   de costes ni recuperación garantizada del cierre sin orderID.
4. El runner conectado debe validar estos gates, presupuesto y autorización
   temporal ligados a la sesión. El test que compone Executor/adapter es un
   contrato simulado, no un nuevo comando operativo ni una validación externa.

Responsable del siguiente paso: integración de datos/bróker con evidencia
operativa y aclaraciones contractuales eToro. No se enviaron mensajes a soporte.
Los campos pendientes se detallan en [ETORO_API_AUDIT](ETORO_API_AUDIT.md).
Fuentes oficiales: [lookup v2](https://api-portal.etoro.com/api-reference/trading--demo/get-order-information-and-position-details)
y [cierre v1](https://api-portal.etoro.com/api-reference/trading--demo/get-close-order-information-and-closed-position-details).
No se ejecutaron consultas de cuenta ni mutaciones externas en A7; A5 real sigue
siendo evidencia histórica separada.

## Pruebas y revisión

tests/test_demo_only_identity.py contiene clasificación, matrices de cuatro
operaciones, llamada directa, cambios durante lectura, caducidad, JSON ambiguo,
configuración engañosa y composición con SQLite/Executor/RiskEngine.
Los spies exigen cero mutaciones, no solo una excepción. Tests anteriores no
eliminados: fixtures de autorización aportan ahora respuestas Demo explícitas.
En los tests de adaptador/seguridad responde el handler bajo prueba, sin sustitución.

Evidencia negativa principal:

- test_adapter_rejects_identity_with_zero_mutations[real/unknown/identity_error]
- test_direct_transport_cannot_bypass_identity[real/unknown/error]
- test_identity_changed_between_adapter_and_transport_blocks_write
- test_deceptive_demo_environment_and_real_keys_cannot_authorize
- test_executor_identity_guards_preserve_durable_state[real/unknown/error]

Revisión de escapes: submit/cancel/close/protect convergen en request; únicas
mutaciones enumeradas son Demo y despachan al mock fijado. CLI y servicio siguen
bloqueados; script A6 conserva simulador concreto. No factory, job, worker,
comando administrativo, flag ni ruta REAL nuevos. Checks exactos finales en
[VERIFICATION](VERIFICATION.md) y runtime/a7/verification.json.

## Definition of Done

| # | Criterio | Estado de esta entrega |
|---|---|---|
| 1 | Runner puede mutar eToro Demo externo verificado | BLOCKED: dependencias anteriores; solo contratos mock |
| 2 | REAL rechazada antes de mutar | PASS: matriz adaptador y transporte, cero mutaciones |
| 3 | UNKNOWN rechazada | PASS: misma matriz |
| 4 | Error de identidad rechazado | PASS: HTTP 403 y timeout, cero mutaciones |
| 5 | Sin configuración que habilite REAL | PASS: enum cerrado, campos extra prohibidos |
| 6 | Env/base URL/ID/modo/claves no evitan guard | PASS: origen fijo, allowlist y vínculo comprobado |
| 7 | Config/credenciales válidas + REAL = cero | PASS: autorización previa válida y respuesta REAL simulada |
| 8 | Guard junto a mutación | PASS: transporte comprueba identidad de nuevo |
| 9 | Riesgo A6 sigue aplicándose | PASS: core intacto, regresión y test compuesto |
| 10 | Persistencia/reconciliación A7 externa | BLOCKED: local preservada; cierre externo no certificado |
| 11 | Regresión A6 | PASS: 39 casos en suite final |
| 12 | Nuevas pruebas Demo-only | PASS: 64 casos, suite final 822/16 gates |
| 13 | Documentación | PASS: estado parcial y bloqueos explícitos |
| 14 | Cambios de esta entrega limitados a A7 | PASS: comparación con huella inicial; trabajo previo separado |
| 15 | Sin soporte REAL oculto | PASS: ninguna ruta/flag de trading REAL |

A7 no está cerrado; no existe evidencia DEMO_WRITE_VERIFIED.
