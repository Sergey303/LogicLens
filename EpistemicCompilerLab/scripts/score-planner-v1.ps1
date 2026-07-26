[CmdletBinding()]
param(
    [Parameter(Mandatory)][string] $RunPath,
    [Parameter(Mandatory)][string] $SummaryPath
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v1.jsonl'
if (-not [IO.Path]::IsPathRooted($RunPath)) { $RunPath = Join-Path $repoRoot $RunPath }
if (-not [IO.Path]::IsPathRooted($SummaryPath)) { $SummaryPath = Join-Path $repoRoot $SummaryPath }
if (-not (Test-Path -LiteralPath $RunPath -PathType Leaf)) { throw "Run not found: $RunPath" }

$cases = @{}
Get-Content -LiteralPath $caseFile -Encoding utf8 | Where-Object { $_.Trim() } | ForEach-Object {
    $case = $_ | ConvertFrom-Json -Depth 40
    $cases[[string] $case.id] = $case
}
$records = @(
    Get-Content -LiteralPath $RunPath -Encoding utf8 | Where-Object { $_.Trim() } |
        ForEach-Object { $_ | ConvertFrom-Json -Depth 50 }
)
if ($records.Count -ne $cases.Count) { throw "Incomplete run: $($records.Count)/$($cases.Count)." }
if (@($records.caseId | Sort-Object -Unique).Count -ne $records.Count) { throw 'Duplicate case IDs.' }

function Test-Step($Actual, $Expected) {
    if ($null -eq $Actual -or $Actual.operation -ne $Expected.operation) { return $false }
    if ($Expected.operation -eq 'current-material') {
        return $Actual.arguments.revision -eq $Expected.arguments.revision -and
            [int64] $Actual.arguments.date -eq [int64] $Expected.arguments.date
    }
    return $Actual.arguments.entity -eq $Expected.arguments.entity -and
        $Actual.arguments.kind -eq $Expected.arguments.kind
}

$results = foreach ($record in $records) {
    $case = $cases[[string] $record.caseId]
    if ($null -eq $case) { throw "Unknown case '$($record.caseId)'." }
    $actual = $record.plan
    $expected = $case.expected
    $runnerOk = [string]::IsNullOrWhiteSpace([string] $record.runnerError)
    $actionCorrect = $runnerOk -and $actual.action -eq $expected.action
    $askCorrect = if ($expected.action -eq 'ask_user') {
        $actual.askField -eq $expected.askField
    } else { $null }
    $actualPlan = @($actual.plan)
    $expectedPlan = @($expected.plan)
    $planCorrect = $actualPlan.Count -eq $expectedPlan.Count
    if ($planCorrect) {
        for ($i = 0; $i -lt $expectedPlan.Count; $i++) {
            if (-not (Test-Step $actualPlan[$i] $expectedPlan[$i])) {
                $planCorrect = $false
                break
            }
        }
    }
    [pscustomobject][ordered]@{
        caseId = [string] $case.id
        taskType = [string] $case.taskType
        passed = $runnerOk -and $actionCorrect -and $planCorrect -and
            ($null -eq $askCorrect -or $askCorrect)
        runnerOk = $runnerOk
        actionCorrect = $actionCorrect
        planCorrect = $planCorrect
        askFieldCorrect = $askCorrect
        actual = $actual
        expectedPlan = $expectedPlan
        runnerError = $record.runnerError
    }
}

$byTask = [ordered]@{}
foreach ($taskType in @($results.taskType | Sort-Object -Unique)) {
    $group = @($results | Where-Object taskType -eq $taskType)
    $byTask[$taskType] = [ordered]@{
        passed = @($group | Where-Object passed).Count
        total = $group.Count
    }
}
$first = $records[0]
$summary = [ordered]@{
    schemaVersion = 1
    runId = [string] $first.runId
    inputMode = [string] $first.inputMode
    model = [string] $first.model
    commit = [string] $first.commit
    sourceRun = $RunPath
    scoredAt = [DateTimeOffset]::UtcNow.ToString('o')
    metrics = [ordered]@{
        totalCases = $results.Count
        passedCases = @($results | Where-Object passed).Count
        actionCorrect = @($results | Where-Object actionCorrect).Count
        planCorrect = @($results | Where-Object planCorrect).Count
        askFieldCorrect = @($results | Where-Object askFieldCorrect -eq $true).Count
        askFieldApplicable = @($results | Where-Object { $null -ne $_.askFieldCorrect }).Count
        runnerErrors = @($results | Where-Object { -not $_.runnerOk }).Count
        elapsedMs = (@($records.elapsedMs) | Measure-Object -Sum).Sum
        byTaskType = $byTask
    }
    cases = @($results)
}
New-Item -ItemType Directory -Path (Split-Path -Parent $SummaryPath) -Force | Out-Null
$summary | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $SummaryPath -Encoding utf8
Write-Host "Planner v1 summary: $SummaryPath"
Write-Host "Passed: $($summary.metrics.passedCases)/$($summary.metrics.totalCases)"
Write-Host "Actions: $($summary.metrics.actionCorrect); plans: $($summary.metrics.planCorrect)"
