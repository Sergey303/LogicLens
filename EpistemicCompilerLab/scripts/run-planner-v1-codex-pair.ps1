[CmdletBinding()]
param(
    [string] $Model,
    [string] $OutputRoot
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$runner = Join-Path $PSScriptRoot 'run-planner-v1-codex.ps1'
$scorer = Join-Path $PSScriptRoot 'score-planner-v1.ps1'
$selection = if ([string]::IsNullOrWhiteSpace($Model)) { 'account-default' } else { $Model }
$safeModel = $selection -replace '[^A-Za-z0-9._-]', '_'
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $labRoot "experiments/model-runs/$stamp-planner-v1-codex-$safeModel"
} elseif (-not [IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot = Join-Path $repoRoot $OutputRoot
}
if (Test-Path -LiteralPath $OutputRoot) { throw "Output already exists: $OutputRoot" }
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

function Invoke-PlannerMode([string] $Mode) {
    $modeRoot = Join-Path $OutputRoot $Mode
    $parameters = @{ InputMode = $Mode; OutputRoot = $modeRoot }
    if (-not [string]::IsNullOrWhiteSpace($Model)) { $parameters.Model = $Model }
    & $runner @parameters
    $runPath = Join-Path $modeRoot 'run.jsonl'
    $summaryPath = Join-Path $modeRoot 'summary.json'
    & $scorer -RunPath $runPath -SummaryPath $summaryPath
    return Get-Content -LiteralPath $summaryPath -Raw -Encoding utf8 | ConvertFrom-Json -Depth 80
}

$raw = Invoke-PlannerMode 'raw'
$frame = Invoke-PlannerMode 'teacher-frame'
$comparison = [ordered]@{
    schemaVersion = 1
    kind = 'planner-v1-input-compilation-comparison'
    provider = 'codex-cli'
    model = $selection
    commit = [string] $raw.commit
    createdAt = [DateTimeOffset]::UtcNow.ToString('o')
    cases = [int] $raw.metrics.totalCases
    raw = $raw.metrics
    teacherFrame = $frame.metrics
    delta = [ordered]@{
        passedCases = [int] $frame.metrics.passedCases - [int] $raw.metrics.passedCases
        actionCorrect = [int] $frame.metrics.actionCorrect - [int] $raw.metrics.actionCorrect
        planCorrect = [int] $frame.metrics.planCorrect - [int] $raw.metrics.planCorrect
        runnerErrors = [int] $frame.metrics.runnerErrors - [int] $raw.metrics.runnerErrors
        elapsedMs = [int64] $frame.metrics.elapsedMs - [int64] $raw.metrics.elapsedMs
    }
}
$comparisonPath = Join-Path $OutputRoot 'comparison.json'
$comparison | ConvertTo-Json -Depth 80 | Set-Content -LiteralPath $comparisonPath -Encoding utf8
$rows = @(
    [pscustomobject]@{
        inputMode = 'raw'; passedCases = $raw.metrics.passedCases
        actionCorrect = $raw.metrics.actionCorrect; planCorrect = $raw.metrics.planCorrect
        runnerErrors = $raw.metrics.runnerErrors; elapsedMs = $raw.metrics.elapsedMs
    },
    [pscustomobject]@{
        inputMode = 'teacher-frame'; passedCases = $frame.metrics.passedCases
        actionCorrect = $frame.metrics.actionCorrect; planCorrect = $frame.metrics.planCorrect
        runnerErrors = $frame.metrics.runnerErrors; elapsedMs = $frame.metrics.elapsedMs
    }
)
$csvPath = Join-Path $OutputRoot 'comparison.csv'
$rows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8
$rows | Format-Table -AutoSize

$artifactPath = "$OutputRoot.zip"
if (Test-Path -LiteralPath $artifactPath) { Remove-Item -LiteralPath $artifactPath -Force }
Compress-Archive -Path (Join-Path $OutputRoot '*') -DestinationPath $artifactPath -Force

Write-Host "Codex planner v1 pair completed: $OutputRoot"
Write-Host "Model selection: $selection"
Write-Host "Comparison JSON: $comparisonPath"
Write-Host "Comparison CSV: $csvPath"
Write-Host "Artifact ZIP: $artifactPath"
Write-Output '[CGR_ARTIFACT_TITLE] Epistemic Compiler planner-v1 Codex pair'
Write-Output ("[CGR_ARTIFACT] {0}" -f $artifactPath)
