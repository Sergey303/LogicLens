[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('markdown', 'compact-json', 'prolog-text', 'cli', 'cli-tails')]
    [string] $Mode,

    [Parameter(Mandatory)]
    [string] $Model
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$runRoot = Join-Path $labRoot 'experiments/model-runs'
$safeModel = $Model -replace '[^A-Za-z0-9_.-]', '_'
$timestamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$baseName = "$timestamp-$Mode-$safeModel"
$runPath = Join-Path $runRoot ($baseName + '.jsonl')
$summaryPath = Join-Path $runRoot ($baseName + '.summary.json')

New-Item -ItemType Directory -Path $runRoot -Force | Out-Null

& (Join-Path $PSScriptRoot 'test-ollama-model.ps1') -Model $Model

$runError = $null
try {
    & (Join-Path $PSScriptRoot 'run-representation.ps1') `
        -Mode $Mode `
        -Model $Model `
        -OutputPath $runPath
}
catch {
    $runError = $_.Exception.Message
    Write-Warning $runError
}

if (-not (Test-Path -LiteralPath $runPath -PathType Leaf)) {
    throw "Representation run did not create an output file: $runPath"
}

& (Join-Path $PSScriptRoot 'score-representation.ps1') `
    -RunPath $runPath `
    -SummaryPath $summaryPath `
    -Force

Write-Host "Representation baseline completed."
Write-Host "Run: $runPath"
Write-Host "Summary: $summaryPath"

if ($null -ne $runError) {
    throw "Representation baseline preserved and scored a run with errors: $runError"
}
