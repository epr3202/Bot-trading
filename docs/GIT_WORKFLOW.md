# Versionado verificable

La identidad local aportada por el usuario se verificó mediante git config y
git var GIT_AUTHOR_IDENT / GIT_COMMITTER_IDENT antes de crear los commits.
Está CONFIGURED; no se inventó identidad ni se cambiaron valores globales.
Sin fechas retroactivas, remotos, push o publicación.

| Capa | Commit real | Árbol Git | Contenido comprobado |
|---|---|---|---|
| A — main | 6af05f1b16b8e3488a5cd959dc0e7f889b258fd6 | 457998f3c919c0ff03d1c3bf1afcd1930e6bcf02 | Índice original, 123 archivos; 358 pruebas aisladas |
| B — recovery/phase2-reviewed | ef8bf5564f6e15bd04ae084c18cd63dd27ba380b | f8e132b821babcd96d42d9128978e6cb75450a51 | 33 modificados + seis nuevos de Fase 2; 420 pruebas |
| C — feat/phase3-readonly-evidence | b51506a97771d04a5edfb45d46e8fac4c31f307f | 2cd8ee28a1b196d75518fec08536bb30cc7a752f | Cuatro archivos de correcciones contractuales; 435 pruebas |

El incremento documental posterior a C recoge la auditoría y no cambia su código.
Su hash se obtiene del historial real, sin insertar un imposible hash de sí mismo
en su propio contenido: `git log --format='%H %T %s'`. VERIFICATION vincula suite,
huella de código, versión, comandos y archivos de evidencia.

Antes del primer git add se cotejó cada blob del índice con index_sha256 de
docs/phase2-baseline.json y se escanearon secretos: 123 coincidencias, cero hallazgos.
Se comprobó también el SHA del ZIP original. A se materializó sin modificar archivos
de trabajo en runtime/phase3/baseline-A y se instaló con su propia .venv y caché local.
El primer commit utilizó exclusivamente el índice ya existente, sin -a ni rutas.

Después se creó recovery/phase2-reviewed conservando B y se revisaron los 39 paths.
Su staging explícito se comparó con los 129 archivos de trabajo revisados, teniendo
en cuenta la normalización CRLF→LF declarada en .gitattributes. Se escanearon los
blobs reales del índice, no solo las copias de trabajo. B se conservó como incremento
coherente único, sin fabricar commits retrospectivos por componentes.

Huellas de bytes de A y B previas a commits:
runtime/phase3/layers-before-commits.json; ZIP B revisado:
runtime/phase3/phase2-B-reviewed.zip. El manifiesto original de Fase 2 mantiene sus
datos históricos, incluido el estado de identidad entonces ausente. No sustituye
los commits. La verificación aislada reutilizó metadatos Git solo para lectura con
GIT_WORK_TREE apuntando a A y una copia local del índice; no creó otro repositorio.

La primera escritura de commit en el sandbox falló al crear .git/index.lock.
La revisión automática permitió después las escrituras Git específicamente
solicitadas por el usuario. No hubo rechazo de aprobación automática ni cambios
de ACL, seguridad, TLS, sandbox o configuración del sistema.

Para futuros cambios: revisar diff y secretos, ejecutar comprobaciones pertinentes,
añadir únicamente paths revisados y comprobar git diff --cached --check y los blobs
del índice antes de commit. Nunca git add . indiscriminado, commit -a, reset --hard,
clean, stash/checkout destructivo, force-push o publicación implícita.

Referencias primarias revalidadas: [contenido de un commit](https://git-scm.com/docs/git-commit)
y [configuración Git](https://git-scm.com/docs/git-config). El commit sin paths conserva
el índice; añadir paths a git commit puede seleccionar contenido del working tree.
