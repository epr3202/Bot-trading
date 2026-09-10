# Seguridad

Solo offline/backtest/shadow/etoro_demo; las enumeraciones y las pruebas rechazan real,
live y cualquier valor no permitido. No existe adaptador ni selector de dinero real.
Transporte autenticado fijo a `https://public-api.etoro.com`, métodos/rutas explícitos,
sin redirecciones, proxies heredados, URL configurable, Bearer mezclado ni replay de
escrituras. Las rutas sin evidencia quedan cerradas. Ver ETORO_API_AUDIT y tests etoro.

Amenazas principales: endpoints reales disfrazados, credenciales de alcance excesivo,
respuesta perdida que duplique órdenes, datos tardíos/look-ahead, instrumentos ambiguos,
acceso web de otro origen, contaminación del PnL con posiciones ajenas y corrupción DB.
Las defensas se reparten entre tipos, configuración, transporte, riesgo y persistencia.

Claves propias Demo mediante variables de entorno; .env no se carga automáticamente.
No imprimir cabeceras ni respuestas de identidad. Redacción recursiva en logging;
auditoría acepta códigos locales, no payloads del bróker. No subir bases, datos privados,
logs, claves ni tokens. Scanner local detecta patrones conocidos; no sustituye revisión.

API solo 127.0.0.1, Host/Origin exactos, Bearer de control por proceso, CSP, sin CORS
abierto, sin mutación GET ni tokens en URL. Token en runtime/control-token con ACL
heredada del usuario en Windows y modo 0600 en POSIX. El panel lo conserva en memoria
de pestaña. Un usuario local con acceso al proyecto puede controlar el simulador;
no es una plataforma multiusuario y no debe exponerse fuera de localhost.

Datos, noticias y especificaciones son entradas no confiables: nunca autorizan comandos,
límite de riesgo ni solicitudes de secretos. Importación estricta, manifiestos y checksums.
Ante incidente: pausar entradas, persistir evidencia redactada, reconciliar, cancelar
pendientes propios y proteger/cerrar solo exposición demostrada. Revocar claves si hay
filtración. No rearmar por reiniciar el proceso. Ver OPERATIONS_RUNBOOK.

Estado de seguridad externo: no se certifica ninguna cuenta. El runner Demo permanece
bloqueado por datos/elegibilidad/protección/reconciliación de cierre pendientes.
