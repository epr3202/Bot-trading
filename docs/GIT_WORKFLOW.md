# Versionado

El directorio inicial estaba vacío y no tenía repositorio padre. Se inicializó main
localmente en la raíz del workspace, sin repositorios anidados ni remoto.
Los commits dependen de identidad auténtica del usuario. Si no está configurada,
continuar con archivos y verificaciones, registrar bloqueo y no inventar autor.

Antes de cada commit: pruebas pertinentes, `git diff`, scanner de secretos, `git add`
con rutas explícitas, `git diff --cached --check` y `git diff --cached` completo.
Nunca reset --hard, clean -fd, force-push, git add . indiscriminado o configuración global.
La revisión se enfoca en disponibilidad temporal, duplicados, propiedad y allowlists.

Después de recibir nombre/correo, configurar solo con `git config --local user.name`
y `user.email`. Hitos sugeridos: bootstrap; datos/estrategia; riesgo/ejecución;
adaptador; UI/informes; recuperación/documentación. No crear commits vacíos ni fingir
que son previos a su verificación. Consultar HANDOFF para el historial real al cierre.

GitHub es entrega independiente: no existe publicación autorizada ni URL inventada.
Si el usuario proporciona destino y autorización, primero revisar staged y secretos;
después añadir remoto privado explícito y usar push normal. No publicar por defecto.
