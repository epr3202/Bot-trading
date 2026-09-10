# Operación e incidentes

Fase 2: toda gestión externa, incluso salidas/stops/cancelaciones Demo, está
DESHABILITADA. La tabla de incidentes describe comportamiento del simulador y requisitos
de una futura sesión; no autoriza operar posiciones existentes del usuario.

Para lectura propia, generar en eToro Settings → Trading → API Key Management una
clave con Environment Demo y permiso Read, según
[autenticación oficial](https://api-portal.etoro.com/core/getting-started/authentication).
El programa usa exactamente ETORO_API_KEY y ETORO_USER_KEY del proceso; no carga .env
automáticamente ni hereda un conector de ChatGPT. Nunca pegar las claves en el chat.
Este bloque de PowerShell pide los valores sin eco ni incluirlos en el historial:

```powershell
$botAppSecret = Read-Host 'ETORO_API_KEY propia' -AsSecureString
$botUserSecret = Read-Host 'ETORO_USER_KEY Demo Read propia' -AsSecureString
$env:ETORO_API_KEY = [System.Net.NetworkCredential]::new('', $botAppSecret).Password
$env:ETORO_USER_KEY = [System.Net.NetworkCredential]::new('', $botUserSecret).Password
$env:ORDER_SUBMISSION_ENABLED = 'false'
try { .\scripts\uv.ps1 run bot etoro preflight --read-only }
finally {
    Remove-Item Env:ETORO_API_KEY, Env:ETORO_USER_KEY -ErrorAction SilentlyContinue
    $botAppSecret.Dispose()
    $botUserSecret.Dispose()
}
```

El origen fijo y la ruta Demo, junto con demoCid, scopes y concordancia de CID del
portafolio, sustentan la identidad; el nombre de la clave no lo demuestra. El preflight
reduce la respuesta y no guarda CID, perfil ni portafolio. 401 significa fallo de
autenticación; 403 bloquea el permiso; 429 respeta Retry-After/cuota sin fallback.
Un éxito no arma, no prueba escritura, datos OHLCV, elegibilidad ni cash utilizable.
No ejecutar un POST de prueba: el transporte de fase 2 lo bloqueará.

Recorrido de datos disponible ahora:
`.\scripts\uv.ps1 run python scripts/verify_import.py` produce un YAML único cuya
ruta queda en runtime/import-evidence.json. Con esa ruta real puede repetirse
`bot data validate --config RUTA` y `bot backtest --config RUTA`. El script ya ejecuta
ambos. Es replay sintético; `run --mode shadow` permanece BLOCKED sin feed adecuado.
No existe una sesión futura programada ni proceso de mercado en segundo plano.

Inicio local: `uv sync --frozen`, `uv run bot doctor`, `uv run bot demo-offline`.
Abrir panel: `uv run bot dashboard --host 127.0.0.1`; consultar runtime/control-token
localmente e introducirlo en la página. No compartir token ni carpeta runtime.
Ctrl+C detiene el servidor sin crear servicios ni tareas programadas. El siguiente
arranque desarma entradas. El token anterior se invalida y nunca queda en la URL.

Con dashboard activo, `pause-entries`, `reconcile` y `cancel-pending-entries` van por
API al mismo ejecutor. Sin servidor, devuelven BLOCKED. `demo-offline` termina; repetirlo
reconoce las mismas intenciones de la sesión sintética y no duplica entradas ni PnL.
Para otra evaluación limpia usar otra runtime_dir en un YAML, conservar la anterior.

| Situación | Respuesta requerida / evidencia de salida |
|---|---|
| Fin diario normal | Calendario Nueva York: solicitar cierre cinco minutos antes; confirmar posiciones=0 y ningún UNKNOWN/pendiente. No inferir flat del horario. |
| Festivo / cierre anticipado | Consultar calendario XNYS; no crear una sesión regular ficticia. La hora Bogotá cambia con DST estadounidense. |
| Desconexión o revocación | Pausar entradas, conservar DB y referencias. Al volver, identidad Demo y reconciliación; no reenvío automático. |
| Datos ausentes/atrasados | Excluir universo incompleto y registrar motivo. No rellenar volumen ni ampliar TTL de 10s. |
| Reloj desajustado | Bloquear entradas; comparar UTC/recepción/disponibilidad. Corregir reloj por medios autorizados y hacer preflight nuevo. |
| Timeout de apertura/cierre | UNKNOWN persistente; consulta por referencia documentada/orden conocida, mantén reservas. Escalar si no existe evidencia concluyente. |
| Fill parcial/cancelación cruzada | Reconciliar cantidades acumuladas; contabilizar incremento una sola vez y mantener cupo por exposición restante. |
| Stop ausente/rechazado | Incidente, pausa, cancelar pendientes propios y solicitar reducción/cierre propios. No ampliar distancia ni afirmar protección por ACK. |
| Suspensión / exposición tardía | Mantener gestión y reconciliación disponible. Registrar posición residual; no informar flat ni liquidación garantizada. |
| Diferencia de posición | Revisar IDs y propiedad. Posiciones manuales/copias se excluyen; propiedad dudosa bloquea cambios. |
| Pérdida diaria | Realizado+no realizado conservador neto; pausa/cancelación/cierre. Reiniciar no reinicia el diario. |
| DB inaccesible/corrupta | No operar. Conservar original y archivos WAL; restaurar copia a ruta nueva y verificar integridad antes de reconciliar. |
| Doble proceso | El segundo falla con otro ejecutor propietario. No eliminar locks de un proceso vivo; la muerte libera el bloqueo OS. |
| Servidor local cerrado abruptamente | Reiniciar dashboard adquiere bloqueo y reemplaza token local. Si falla, comprobar el proceso propietario; no arrancar otro ejecutor. |

Backup: `uv run bot backup --destination runtime/backups/fecha-unica.sqlite`.
Restore: `uv run bot restore --source runtime/backups/fecha-unica.sqlite --destination
runtime/restored-copia.sqlite`. El destino debe ser nuevo. La copia conserva PnL,
UNKNOWN y auditoría, elimina readiness y desarma sesiones. No sustituye automáticamente
la DB original; comparar y elegir la copia explícitamente en una revisión de recuperación.

Preflight futuro: claves Demo propias en variables de entorno y `uv run bot etoro
preflight --read-only`. Es una acción de cuenta explícita, no parte del doctor/bootstrap.
`arm-demo --confirm DEMO_ONLY --budget 10000` y `flatten-owned-demo --confirm DEMO_ONLY`
requieren servidor y confirmación, pero actualmente devuelven BLOCKED por integración
de sesión incompleta. No eludir ese gate invocando métodos de adaptador directamente.

No hay daemon de mercado, supervisor de posiciones virtuales externas ni alertas remotas
activados. Es un laboratorio local; completar X01–X03 antes de una sesión Demo autorizada.
