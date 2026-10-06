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

function Tiene-Agente([string]$Root) {
    Test-Path -LiteralPath (Join-Path $Root "00_agent_principal_ospost.md")
}

$sgc = $Workspace
if (-not (Tiene-Agente $sgc)) {
    $sgc = Join-Path $extensionRoot "biblioteca"
}
if (-not (Tiene-Agente $sgc)) {
    throw "No hay --sgc. Hace falta 00_agent_principal_ospost.md en el workspace o en la biblioteca de la extensión."
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
    "--profile", "enterprise_erp"
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
