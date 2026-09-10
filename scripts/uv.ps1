# Project-local uv launcher; only sets environment in this PowerShell process.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:UV_CACHE_DIR = Join-Path $projectRoot '.uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $projectRoot '.python'
$env:PYTHONUTF8 = '1'
& (Join-Path $projectRoot '.tools\bin\uv.exe') @args
exit $LASTEXITCODE
