$ErrorActionPreference = "Stop"
$extensionRoot = Split-Path $PSScriptRoot -Parent
$needle = "c:\xampp\htdocs\SGC_Ai"
$hits = @()
foreach ($dir in @("reglas", "instrucciones")) {
    $root = Join-Path $extensionRoot $dir
    Get-ChildItem -LiteralPath $root -File -Recurse | ForEach-Object {
        $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $_.FullName
        if ($text -and $text.Contains($needle)) {
            $hits += $_.FullName
        }
    }
}
$gate = "GO_D2_PERIMETRO_DINAMICO"
if ($hits.Count -gt 0) { $gate = "NO_GO_D2_PERIMETRO_DINAMICO" }
[pscustomobject]@{ gate = $gate; hits = $hits } | ConvertTo-Json -Compress
if ($hits.Count -gt 0) { exit 1 }
