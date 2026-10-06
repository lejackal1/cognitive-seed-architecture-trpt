param(
    [string]$Workspace,
    [string]$Destino
)
$ErrorActionPreference = "Stop"
$extensionRoot = Split-Path $PSScriptRoot -Parent
$seedRoot = Split-Path $extensionRoot -Parent
$reglas = Join-Path $extensionRoot "reglas"

if ($Workspace -and $Destino) {
    throw "Indica -Workspace o -Destino, no los dos."
}
if ($Workspace) {
    $ws = (Resolve-Path -LiteralPath $Workspace).Path
    $seed = (Resolve-Path -LiteralPath $seedRoot).Path
    if ($ws.TrimEnd("\") -eq $seed.TrimEnd("\")) {
        throw "No instales el paquete sobre la semilla de desarrollo."
    }
    $Destino = Join-Path $ws ".cursor\rules"
}
if (-not $Destino) {
    throw "Indica -Workspace <carpeta abierta> o -Destino <carpeta de reglas>. Este script no escribe en el perfil de usuario si no se lo pides."
}

if (-not (Test-Path -LiteralPath $Destino)) {
    New-Item -ItemType Directory -Force -Path $Destino | Out-Null
}
Copy-Item -Path (Join-Path $reglas "*.mdc") -Destination $Destino -Force
$n = (Get-ChildItem -LiteralPath $Destino -Filter "*.mdc").Count
$salida = $null
if ($Workspace) {
    $node = Get-Command node -ErrorAction SilentlyContinue
    if (-not $node) {
        throw "node no está en el PATH. Las reglas se copiaron; las carpetas de salida no."
    }
    $salidaJs = Join-Path $extensionRoot "src\salida.js"
    $salida = & node $salidaJs $ws
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear la salida visible en $ws" }
}
[pscustomobject]@{ destino = $Destino; reglas = $n; salida = $salida } | ConvertTo-Json -Compress
