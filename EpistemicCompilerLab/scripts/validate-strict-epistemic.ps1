[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    'sources/strict-epistemic-v0.md',
    'prolog/strict_epistemic.pl',
    'tests/strict_epistemic_tests.pl',
    'research/STRICT_EPISTEMIC_ABLATION.md',
    'scripts/run-strict-epistemic-tests.ps1'
)

foreach ($relative in $required) {
    $path = Join-Path $labRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing strict epistemic asset: $relative"
    }
    $lines = @(Get-Content -LiteralPath $path -Encoding utf8)
    if ($lines.Count -eq 0) { throw "Empty strict epistemic asset: $relative" }
    if ($lines.Count -gt 149) { throw "Human-maintained file exceeds 149 lines: $relative" }
}

$oracle = Get-Content (Join-Path $labRoot 'prolog/strict_epistemic.pl') -Raw -Encoding utf8
foreach ($marker in @('supported', 'refuted', 'unknown', 'conflicting')) {
    if ($oracle -notmatch "claim_status\(Proposition, $marker\)") {
        throw "Strict epistemic oracle is missing status: $marker"
    }
}
foreach ($forbidden in @('probability(', 'membership(', 'confidence(')) {
    if ($oracle -match [regex]::Escape($forbidden)) {
        throw "Premature numeric uncertainty construct found: $forbidden"
    }
}

$tokens = $null; $errors = $null
foreach ($relative in @($required | Where-Object { $_ -like '*.ps1' })) {
    [void] [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $labRoot $relative), [ref] $tokens, [ref] $errors
    )
    if (@($errors).Count -gt 0) { throw "PowerShell parse failed: $relative" }
}

& (Join-Path $PSScriptRoot 'run-strict-epistemic-tests.ps1')
Write-Host 'Strict epistemic assets valid: typed statuses, provenance and policy are separated.'
