[CmdletBinding()]
param(
    [string] $CodexModel,
    [int] $TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$outputRoot = Join-Path $labRoot "experiments/model-runs/$stamp-compiled-frame-replication-candidate"

$codexParameters = @{}
if (-not [string]::IsNullOrWhiteSpace($CodexModel)) {
    $codexParameters.Model = $CodexModel
}
& (Join-Path $PSScriptRoot 'test-codex-cli.ps1') @codexParameters

$arguments = @(
    (Join-Path $PSScriptRoot 'generate_replication_cases.py'),
    '--lab-root', $labRoot,
    '--output-root', $outputRoot,
    '--swipl', $swipl,
    '--timeout-seconds', $TimeoutSeconds
)
if (-not [string]::IsNullOrWhiteSpace($CodexModel)) {
    $arguments += @('--codex-model', $CodexModel)
}

python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Replication generation failed with code $LASTEXITCODE. Artifacts remain under $outputRoot"
}

Write-Host "Replication candidate generated: $outputRoot"
Write-Host 'Do not run it as a benchmark until the attached ZIP has been reviewed and frozen.'
