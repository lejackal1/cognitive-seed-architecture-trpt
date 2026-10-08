param(
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [string]$Workspace,
    [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$extensionRoot = Split-Path $PSScriptRoot -Parent

if (-not $Workspace) {
    $Workspace = (Get-Location).Path
}
$Workspace = (Resolve-Path -LiteralPath $Workspace).Path

$sgc = $Workspace
$perfilArchivo = Join-Path $Workspace "contextos\perfil.md"
$profile = ""
if (Test-Path -LiteralPath $perfilArchivo) {
    $linea = Select-String -LiteralPath $perfilArchivo -Pattern '^perfil:\s*(\S+)' | Select-Object -First 1
    if ($linea) { $profile = $linea.Matches[0].Groups[1].Value }
}
if (-not $profile) {
    throw "Falta el perfil. Escríbelo en contextos/perfil.md como 'perfil: <nombre>', o pásalo al orquestar. No hay valor por defecto."
}

$embebido = Join-Path $extensionRoot "ai6\runtime"
$runtime = $null
if (Test-Path -LiteralPath (Join-Path $embebido "ai6\cli.py")) {
    $runtime = $embebido
} elseif ($env:AI6_RUNTIME) {
    $runtime = (Resolve-Path -LiteralPath $env:AI6_RUNTIME).Path
} else {
    $junto = Join-Path $Workspace "ai6\runtime"
    if (Test-Path -LiteralPath (Join-Path $junto "ai6\cli.py")) {
        $runtime = $junto
    }
}
if (-not $runtime -or -not (Test-Path -LiteralPath (Join-Path $runtime "ai6\cli.py"))) {
    throw "No está el runtime AI6. Define AI6_RUNTIME con la carpeta que contiene ai6\cli.py."
}

$env:PYTHONPATH = $runtime
$cli = @(
    "-m", "ai6.cli", "pipeline",
    "--text", $Text,
    "--workspace", $Workspace,
    "--sgc", $sgc,
    "--profile", $profile
)
if ($DryRun) { $cli += "--dry-run" }

Push-Location $runtime
try {
    & python @cli
    if ($LASTEXITCODE -ne 0) { throw "ai6.cli terminó con código $LASTEXITCODE" }
}
finally {
    Pop-Location
}
