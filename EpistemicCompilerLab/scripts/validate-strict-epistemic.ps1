[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    'sources/strict-epistemic-v0.md',
    'prolog/strict_epistemic.pl',
    'prolog/strict_epistemic_request.pl',
    'prolog/strict_epistemic_entry.pl',
    'tests/strict_epistemic_tests.pl',
    'research/STRICT_EPISTEMIC_ABLATION.md',
    'scripts/run-strict-epistemic-tests.ps1',
    'scripts/strict_epistemic_benchmark_core.py',
    'scripts/generate_strict_epistemic_benchmark.py',
    'scripts/validate_strict_epistemic_benchmark.py',
    'scripts/run-generate-strict-epistemic-benchmark.ps1'
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

$pythonCheck = @'
import ast, pathlib, sys
path = pathlib.Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
ast.parse(source)
if len(source.splitlines()) > 149:
    raise SystemExit(f"human-maintained file exceeds 149 lines: {path}")
'@
foreach ($relative in @($required | Where-Object { $_ -like '*.py' })) {
    $pythonCheck | python - (Join-Path $labRoot $relative)
    if ($LASTEXITCODE -ne 0) { throw "Python validation failed: $relative" }
}

$tokens = $null; $errors = $null
foreach ($relative in @($required | Where-Object { $_ -like '*.ps1' })) {
    [void] [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $labRoot $relative), [ref] $tokens, [ref] $errors
    )
    if (@($errors).Count -gt 0) { throw "PowerShell parse failed: $relative" }
}

& (Join-Path $PSScriptRoot 'run-strict-epistemic-tests.ps1')
Write-Host 'Strict epistemic assets valid: oracle, request policy and frozen-candidate generator are separated.'
