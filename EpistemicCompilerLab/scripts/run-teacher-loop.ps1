[CmdletBinding()]
param(
    [ValidateSet('prompt', 'prolog', 'combined')]
    [string] $Track = 'combined',
    [ValidateRange(0, 10)]
    [int] $Epochs = 1,
    [string] $BaseModel = 'qwen2.5-coder:7b',
    [int] $Seed = 42,
    [string] $CodexModel,
    [int] $TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $PSScriptRoot 'run_teacher_loop.py'
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required

$executionModel = & (Join-Path $PSScriptRoot 'ensure-ollama-cpu-profile.ps1') `
    -BaseModel $BaseModel |
    Select-Object -Last 1
& (Join-Path $PSScriptRoot 'test-ollama-model.ps1') -Model $executionModel

$codexParameters = @{}
if (-not [string]::IsNullOrWhiteSpace($CodexModel)) {
    $codexParameters.Model = $CodexModel
}
& (Join-Path $PSScriptRoot 'test-codex-cli.ps1') @codexParameters

$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$safeModel = $executionModel -replace '[^A-Za-z0-9._-]', '_'
$outputRoot = Join-Path $labRoot "experiments/model-runs/$stamp-teacher-loop-$Track-$safeModel-seed$Seed"

$arguments = @(
    $runner,
    '--lab-root', $labRoot,
    '--output-root', $outputRoot,
    '--student-model', $executionModel,
    '--track', $Track,
    '--epochs', $Epochs,
    '--seed', $Seed,
    '--swipl', $swipl,
    '--timeout-seconds', $TimeoutSeconds
)
if (-not [string]::IsNullOrWhiteSpace($CodexModel)) {
    $arguments += @('--codex-model', $CodexModel)
}

python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Teacher loop failed with code $LASTEXITCODE. Artifacts remain under $outputRoot"
}

$summaryPath = Join-Path $outputRoot 'summary.json'
$summary = Get-Content -LiteralPath $summaryPath -Raw -Encoding utf8 | ConvertFrom-Json -Depth 50
$teacherEpochs = @($summary.epochs | Where-Object { [int] $_.epoch -gt 0 })
$nonInfrastructureResults = @(
    $teacherEpochs | Where-Object { $_.status -ne 'teacher_error' }
)
if ($Epochs -gt 0 -and $teacherEpochs.Count -gt 0 -and $nonInfrastructureResults.Count -eq 0) {
    throw "All teacher epochs failed in infrastructure before a candidate result. Artifact preserved: $outputRoot.zip"
}

Write-Host "Teacher loop completed: $outputRoot"
