[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$requiredFiles = @(
    'representations/knowledge.compact.json',
    'runner/prompts/direct.md',
    'runner/prompts/planner.md',
    'runner/prompts/tail-planner.md',
    'runner/prompts/finalize.md',
    'scripts/run-representation.ps1',
    'scripts/score-representation.ps1',
    'scripts/test-ollama-model.ps1',
    'scripts/run-representation-baseline.ps1',
    'scripts/launch.ps1'
)

foreach ($relativePath in $requiredFiles) {
    $path = Join-Path $labRoot $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing representation-runner asset: $relativePath"
    }
    if ((Get-Item -LiteralPath $path).Length -eq 0) {
        throw "Empty representation-runner asset: $relativePath"
    }
}

$compactPath = Join-Path $labRoot 'representations/knowledge.compact.json'
try {
    $compact = Get-Content -LiteralPath $compactPath -Raw -Encoding utf8 | ConvertFrom-Json -Depth 50
}
catch {
    throw "Invalid compact knowledge JSON: $($_.Exception.Message)"
}

if ($compact.schemaVersion -ne 1) {
    throw "Unsupported compact knowledge schemaVersion '$($compact.schemaVersion)'."
}
if (@($compact.supportedRevisions).Count -eq 0) {
    throw 'Compact knowledge has no supported revisions.'
}
if ($null -eq $compact.transitionDate) {
    throw 'Compact knowledge has no transition date.'
}

$parseTargets = @(
    'scripts/run-representation.ps1',
    'scripts/score-representation.ps1',
    'scripts/test-ollama-model.ps1',
    'scripts/run-representation-baseline.ps1',
    'scripts/validate-runner.ps1',
    'scripts/launch.ps1'
)
foreach ($relativePath in $parseTargets) {
    $path = Join-Path $labRoot $relativePath
    $tokens = $null
    $errors = $null
    [void] [System.Management.Automation.Language.Parser]::ParseFile(
        $path,
        [ref] $tokens,
        [ref] $errors
    )

    if (@($errors).Count -gt 0) {
        $messages = @($errors | ForEach-Object {
            "line $($_.Extent.StartLineNumber): $($_.Message)"
        }) -join '; '
        throw "PowerShell parse errors in ${relativePath}: $messages"
    }
}

Write-Host 'Representation runner assets valid: compact JSON, 4 prompts, 6 PowerShell scripts.'
