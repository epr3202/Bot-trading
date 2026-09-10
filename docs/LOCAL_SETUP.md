# Instalación local

Verificado en Windows mediante PowerShell, Git 2.52.0 y CPython 3.12.12 gestionado
localmente por uv 0.12.12. `.python-version` fija Python y `uv.lock` fija dependencias.

Con uv disponible: `uv sync --frozen`; después `uv run bot doctor` y
`uv run bot demo-offline`. El fixture está versionado como generador determinista y
manifiesto bajo tests/fixtures, no requiere una descarga de datos.

En este workspace uv se instaló en `.tools/bin/uv.exe`; usar
` .\scripts\uv.ps1 sync --frozen` y ` .\scripts\uv.ps1 run bot demo-offline`.
El wrapper fija caché y Python dentro del proyecto. No modifica PATH global.
Python del sistema se encontró mediante `py --list-paths`, porque `python` apuntaba
al alias Microsoft Store. La instalación local empleó `py -3.14 -m pip install
--target .tools uv==0.12.12`, descarga Python con uv y `uv sync`.

Panel: `uv run bot dashboard --host 127.0.0.1`, abrir http://127.0.0.1:8765 e introducir
el contenido de runtime/control-token. Ctrl+C termina. No se configura servicio.

Linux/WSL: mismos comandos uv desde clon limpio con Python 3.12.12; el bloqueo usa
flock en lugar de msvcrt y el token modo 0600. Está contemplado y configurado en CI,
pero no se ejecutó una máquina Linux durante este bootstrap Windows.

Credenciales: opcionales para offline; `.env.example` solo describe nombres. No copiar
claves a YAML. El preflight requiere exportación deliberada de ETORO_API_KEY y
ETORO_USER_KEY propias Demo. Los permisos del conector no se transfieren al programa.
