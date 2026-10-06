$ErrorActionPreference = "Stop"
$extensionRoot = Split-Path $PSScriptRoot -Parent
$needles = @("c:\xampp\htdocs\SGC_Ai", "c:\xampp\htdocs\.ai")
$hits = @()
foreach ($dir in @("reglas", "instrucciones", "biblioteca", "scripts")) {
    $root = Join-Path $extensionRoot $dir
    if (-not (Test-Path -LiteralPath $root)) { continue }
    Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object { $_.Name -ne "verificar-reglas.ps1" } | ForEach-Object {
        $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $_.FullName
        foreach ($needle in $needles) {
            if ($text -and $text.Contains($needle)) {
                $hits += $_.FullName
            }
        }
    }
}
$gate = "GO_D2_PERIMETRO_DINAMICO"
if ($hits.Count -gt 0) { $gate = "NO_GO_D2_PERIMETRO_DINAMICO" }
[pscustomobject]@{ gate = $gate; hits = $hits } | ConvertTo-Json -Compress
if ($hits.Count -gt 0) { exit 1 }
