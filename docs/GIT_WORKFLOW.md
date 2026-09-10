# Versionado

Fase 2: la base original de 123 archivos se conserva con SHA-256 por ruta/índice y
working tree en docs/phase2-baseline.json. La copia de bytes revisados está en
runtime/phase2-baseline/reviewed-source.zip, excluye secretos y estado privado y tiene
su propio SHA. El manifiesto no se incluye en su hash. Es una referencia local,
**no un commit**. El índice conserva la base y el incremento queda en working tree.
No se cambió rama, identidad, remoto ni permisos del sistema durante esta fase.

La identidad sigue GIT_IDENTITY_BLOCKED. El usuario puede configurarla únicamente
en este repositorio, con sus valores auténticos (comandos no ejecutados por el agente):

```powershell
git config --local user.name (Read-Host 'Tu nombre para los commits')
git config --local user.email (Read-Host 'Tu correo para los commits')
```

Después revisar el índice original contra el manifiesto y su verificación conservada,
crear el primer commit de esa base, luego una rama de fase y commits del incremento.
No mezclar los cambios posteriores al primer índice bajo la etiqueta baseline.
Documentación Git: [identidad local](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup),
[contenido del índice](https://git-scm.com/docs/git-add). No hay push ni publicación.

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
