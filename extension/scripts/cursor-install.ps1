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
[pscustomobject]@{ destino = $Destino; reglas = $n } | ConvertTo-Json -Compress
