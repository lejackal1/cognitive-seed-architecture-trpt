$ErrorActionPreference = "Stop"
$extensionRoot = Split-Path $PSScriptRoot -Parent
$seedRoot = Split-Path $extensionRoot -Parent
$manifiestoPath = Join-Path $extensionRoot "manifiesto.json"
$destRoot = Join-Path $extensionRoot "biblioteca"
$manifiesto = Get-Content -Raw -Encoding UTF8 $manifiestoPath | ConvertFrom-Json

$missing = @()
$copied = @()
foreach ($rel in $manifiesto.incluir) {
    $relText = [string]$rel
    if ($relText -like "*_PARA_ELIMINAR*") {
        throw "El manifiesto intenta incluir _PARA_ELIMINAR: $relText"
    }
    $src = Join-Path $seedRoot ($relText -replace "/", "\")
    if (-not (Test-Path -LiteralPath $src)) {
        $missing += $relText
        continue
    }
    $dest = Join-Path $destRoot ($relText -replace "/", "\")
    $destDir = Split-Path $dest -Parent
    if (-not (Test-Path -LiteralPath $destDir)) {
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    }
    Copy-Item -LiteralPath $src -Destination $dest -Force
    $copied += $relText
}

$gate = "GO_D1_MANIFIESTO"
if ($missing.Count -gt 0) { $gate = "NO_GO_D1_MANIFIESTO" }

[pscustomobject]@{
    gate    = $gate
    copied  = $copied.Count
    missing = $missing
} | ConvertTo-Json -Compress
if ($missing.Count -gt 0) { exit 1 }
