[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$outputRoot = Join-Path $labRoot "experiments/model-runs/$stamp-strict-epistemic-benchmark-candidate"

python (Join-Path $PSScriptRoot 'generate_strict_epistemic_benchmark.py') `
    --lab-root $labRoot --output-root $outputRoot --swipl $swipl
if ($LASTEXITCODE -ne 0) { throw "Strict benchmark generation failed: $LASTEXITCODE" }

$cases = Join-Path $outputRoot 'strict-epistemic-benchmark-v0.candidate.jsonl'
$sources = Join-Path $outputRoot 'strict-epistemic-source-v0.candidate.jsonl'
python (Join-Path $PSScriptRoot 'validate_strict_epistemic_benchmark.py') `
    --lab-root $labRoot --cases $cases --source-catalog $sources --swipl $swipl
if ($LASTEXITCODE -ne 0) { throw "Strict benchmark validation failed: $LASTEXITCODE" }

Write-Host "Strict epistemic benchmark candidate generated: $outputRoot"
Write-Host 'Do not run Qwen until cases and source catalog are reviewed and frozen together.'
