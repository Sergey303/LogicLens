[CmdletBinding()]
param(
    [string] $BaseModel = 'qwen2.5-coder:7b',
    [int] $Seed = 42,
    [int] $TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required

& (Join-Path $PSScriptRoot 'validate-compiled-frame.ps1')

$executionModel = & (Join-Path $PSScriptRoot 'ensure-ollama-cpu-profile.ps1') `
    -BaseModel $BaseModel |
    Select-Object -Last 1
& (Join-Path $PSScriptRoot 'test-ollama-model.ps1') -Model $executionModel

$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$safeModel = $executionModel -replace '[^A-Za-z0-9._-]', '_'
$outputRoot = Join-Path $labRoot "experiments/model-runs/$stamp-compiled-frame-$safeModel-seed$Seed"

python (Join-Path $PSScriptRoot 'run_compiled_frame.py') `
    --lab-root $labRoot `
    --output-root $outputRoot `
    --student-model $executionModel `
    --swipl $swipl `
    --seed $Seed `
    --timeout-seconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) {
    throw "Compiled-frame run failed with code $LASTEXITCODE. Artifacts: $outputRoot"
}

Write-Host "Compiled decision frame run completed: $outputRoot"
