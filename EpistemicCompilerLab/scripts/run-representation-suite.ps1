[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $Model
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$runRoot = Join-Path $labRoot 'experiments/model-runs'
$modes = @('markdown', 'compact-json', 'prolog-text', 'cli', 'cli-tails')
$timestamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$safeBase = $Model -replace '[^A-Za-z0-9_.-]', '_'
$suiteId = "$timestamp-suite-$safeBase"
$suiteRoot = Join-Path $runRoot $suiteId
$comparisonPath = Join-Path $suiteRoot 'comparison.json'
$csvPath = Join-Path $suiteRoot 'comparison.csv'

New-Item -ItemType Directory -Path $suiteRoot -Force | Out-Null

$profileModel = & (Join-Path $PSScriptRoot 'ensure-ollama-cpu-profile.ps1') `
    -BaseModel $Model |
    Select-Object -Last 1
if ([string]::IsNullOrWhiteSpace([string] $profileModel)) {
    throw "CPU-safe profile was not resolved for '$Model'."
}

& (Join-Path $PSScriptRoot 'test-ollama-model.ps1') -Model $profileModel

$rows = [Collections.Generic.List[object]]::new()
$failures = [Collections.Generic.List[string]]::new()
foreach ($mode in $modes) {
    Write-Host "`n=== Representation mode: $mode ==="
    $runPath = Join-Path $suiteRoot ($mode + '.jsonl')
    $summaryPath = Join-Path $suiteRoot ($mode + '.summary.json')
    $runError = $null

    try {
        & (Join-Path $PSScriptRoot 'run-representation.ps1') `
            -Mode $mode `
            -Model $profileModel `
            -OutputPath $runPath
    }
    catch {
        $runError = $_.Exception.Message
        Write-Warning $runError
    }

    if (-not (Test-Path -LiteralPath $runPath -PathType Leaf)) {
        $failures.Add("${mode}: no run file")
        continue
    }

    try {
        & (Join-Path $PSScriptRoot 'score-representation.ps1') `
            -RunPath $runPath `
            -SummaryPath $summaryPath `
            -Force
        & (Join-Path $PSScriptRoot 'show-representation-summary.ps1') `
            -SummaryPath $summaryPath
    }
    catch {
        $failures.Add("${mode}: scoring failed: $($_.Exception.Message)")
        continue
    }

    $summary = Get-Content -LiteralPath $summaryPath -Raw -Encoding utf8 |
        ConvertFrom-Json -Depth 100
    $metrics = $summary.metrics
    $row = [pscustomobject][ordered]@{
        mode = $mode
        passedCases = $metrics.passedCases
        totalCases = $metrics.totalCases
        statusCorrect = $metrics.statusCorrect
        actionCorrect = $metrics.actionCorrect
        queryCorrect = $metrics.queryCorrect
        queryApplicable = $metrics.queryApplicable
        clarificationCorrect = $metrics.clarificationCorrect
        clarificationApplicable = $metrics.clarificationApplicable
        materialCorrect = $metrics.materialCorrect
        materialApplicable = $metrics.materialApplicable
        tailCorrect = $metrics.tailDecisionCorrect
        tailApplicable = $metrics.tailDecisionApplicable
        runnerErrors = $metrics.runnerErrors
        elapsedMs = $metrics.elapsedMs
        runPath = $runPath
        summaryPath = $summaryPath
        runError = $runError
    }
    $rows.Add($row)

    if ($null -ne $runError) {
        $failures.Add("${mode}: $runError")
    }
}

$commit = (& git -C $repoRoot rev-parse HEAD 2>&1 | Out-String).Trim()
$comparison = [ordered]@{
    schemaVersion = 1
    suiteId = $suiteId
    createdAt = [DateTimeOffset]::UtcNow.ToString('o')
    commit = $commit
    baseModel = $Model
    executionModel = $profileModel
    executionProfile = 'cpu-safe:num_gpu=0,num_ctx=2048,num_batch=64'
    modes = @($rows)
    failures = @($failures)
}

$comparison | ConvertTo-Json -Depth 100 |
    Set-Content -LiteralPath $comparisonPath -Encoding utf8
@($rows) | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8

Write-Host "`n=== Representation comparison ==="
@($rows) | Format-Table mode, passedCases, statusCorrect, actionCorrect, runnerErrors, elapsedMs -AutoSize
Write-Host "Suite: $suiteRoot"
Write-Host "Comparison JSON: $comparisonPath"
Write-Host "Comparison CSV: $csvPath"

if ($failures.Count -gt 0) {
    throw "Representation suite preserved results with $($failures.Count) failure(s): $($failures -join ' | ')"
}