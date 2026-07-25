[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $RunPath,

    [string] $SummaryPath,

    [switch] $Force
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v0.jsonl'

if (-not [IO.Path]::IsPathRooted($RunPath)) {
    $RunPath = Join-Path $repoRoot $RunPath
}
if (-not (Test-Path -LiteralPath $RunPath -PathType Leaf)) {
    throw "Run file not found: $RunPath"
}

if ([string]::IsNullOrWhiteSpace($SummaryPath)) {
    $SummaryPath = [IO.Path]::ChangeExtension($RunPath, '.summary.json')
}
elseif (-not [IO.Path]::IsPathRooted($SummaryPath)) {
    $SummaryPath = Join-Path $repoRoot $SummaryPath
}

if ((Test-Path -LiteralPath $SummaryPath) -and -not $Force) {
    throw "Summary already exists: $SummaryPath. Use -Force to replace it."
}

$cases = @{}
foreach ($line in Get-Content -LiteralPath $caseFile -Encoding utf8) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }
    $case = $line | ConvertFrom-Json -Depth 50
    $cases[[string] $case.id] = $case
}

$records = [Collections.Generic.List[object]]::new()
$seen = [Collections.Generic.HashSet[string]]::new()
foreach ($line in Get-Content -LiteralPath $RunPath -Encoding utf8) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    try {
        $record = $line | ConvertFrom-Json -Depth 100
    }
    catch {
        throw "Invalid JSONL record in ${RunPath}: $($_.Exception.Message)"
    }

    $caseId = [string] $record.caseId
    if (-not $cases.ContainsKey($caseId)) {
        throw "Run contains unknown case id '$caseId'."
    }
    if (-not $seen.Add($caseId)) {
        throw "Run contains duplicate case id '$caseId'."
    }
    $records.Add($record)
}

$missingCases = @($cases.Keys | Where-Object { $_ -notin $seen })
if ($missingCases.Count -gt 0) {
    throw "Run is incomplete. Missing cases: $($missingCases -join ', ')"
}

$first = $records[0]
$mode = [string] $first.mode
$model = [string] $first.model
$runId = [string] $first.runId
$commit = [string] $first.commit
$cliMode = $mode -in @('cli', 'cli-tails')
$caseScores = [Collections.Generic.List[object]]::new()

foreach ($record in $records) {
    if ($record.mode -ne $mode -or $record.model -ne $model -or $record.runId -ne $runId) {
        throw "Run mixes mode, model or runId values at case '$($record.caseId)'."
    }

    $case = $cases[[string] $record.caseId]
    $final = $record.final
    $runnerOk = [string]::IsNullOrWhiteSpace([string] $record.runnerError)
    $actionCorrect = $false
    $clarificationCorrect = $null
    $queryCorrect = $null
    $materialCorrect = $null
    $unknownCorrect = $null

    if ($case.expectedAction -eq 'ask_user') {
        $actionCorrect = $final.action -eq 'ask_user'
        $clarificationCorrect = (
            $final.status -eq 'need_user' -and
            $final.askField -eq $case.expectedField
        )
        if ($cliMode) {
            $queryCorrect = $record.planner.action -eq 'ask_user'
        }
    }
    else {
        $actionCorrect = $final.action -in @('answer', 'query')
        if ($cliMode) {
            $expectedRevision = [string] $case.query.arguments.revision
            $expectedDate = [int64] $case.query.arguments.date
            $queryCorrect = (
                $record.planner.action -eq 'query' -and
                $record.planner.operation -eq $case.query.operation -and
                ([string] $record.planner.revision).ToLowerInvariant() -eq $expectedRevision -and
                [int64] $record.planner.date -eq $expectedDate
            )
        }
    }

    $statusCorrect = $final.status -eq $case.expectedStatus
    if ($case.expectedStatus -eq 'success') {
        $materialCorrect = $final.material -eq $case.expectedMaterial
    }
    elseif ($case.expectedStatus -eq 'unknown') {
        $unknownCorrect = $final.status -eq 'unknown' -and $null -eq $final.material
    }

    $openedTails = @($record.openedTails)
    if ($null -eq $case.requiresTail) {
        $tailDecisionCorrect = $openedTails.Count -eq 0
    }
    else {
        $matchingTails = @($openedTails | Where-Object {
            $_.kind -eq $case.requiresTail -and
            $_.entity -eq $case.tailEntity -and
            $_.status -eq 'success'
        })
        $tailDecisionCorrect = $openedTails.Count -eq 1 -and $matchingTails.Count -eq 1
    }

    $checks = [Collections.Generic.List[bool]]::new()
    $checks.Add($runnerOk)
    $checks.Add($actionCorrect)
    $checks.Add($statusCorrect)
    $checks.Add($tailDecisionCorrect)
    if ($null -ne $clarificationCorrect) { $checks.Add([bool] $clarificationCorrect) }
    if ($null -ne $queryCorrect) { $checks.Add([bool] $queryCorrect) }
    if ($null -ne $materialCorrect) { $checks.Add([bool] $materialCorrect) }
    if ($null -ne $unknownCorrect) { $checks.Add([bool] $unknownCorrect) }
    $passed = @($checks | Where-Object { -not $_ }).Count -eq 0

    $caseScores.Add([ordered]@{
        caseId = [string] $case.id
        passed = $passed
        runnerOk = $runnerOk
        actionCorrect = $actionCorrect
        queryCorrect = $queryCorrect
        statusCorrect = $statusCorrect
        clarificationCorrect = $clarificationCorrect
        materialCorrect = $materialCorrect
        unknownCorrect = $unknownCorrect
        tailDecisionCorrect = $tailDecisionCorrect
        cliCalls = @($record.cliCalls).Count
        openedTails = $openedTails.Count
        final = $final
        runnerError = $record.runnerError
    })
}

function Count-True {
    param([string] $Property)
    @($caseScores | Where-Object { $_.$Property -eq $true }).Count
}

function Count-Applicable {
    param([string] $Property)
    @($caseScores | Where-Object { $null -ne $_.$Property }).Count
}

$summary = [ordered]@{
    schemaVersion = 1
    runId = $runId
    mode = $mode
    model = $model
    commit = $commit
    scoredAt = [DateTimeOffset]::UtcNow.ToString('o')
    sourceRun = $RunPath
    metrics = [ordered]@{
        totalCases = $caseScores.Count
        passedCases = @($caseScores | Where-Object { $_.passed }).Count
        runnerErrors = @($caseScores | Where-Object { -not $_.runnerOk }).Count
        actionCorrect = Count-True 'actionCorrect'
        statusCorrect = Count-True 'statusCorrect'
        queryCorrect = Count-True 'queryCorrect'
        queryApplicable = Count-Applicable 'queryCorrect'
        clarificationCorrect = Count-True 'clarificationCorrect'
        clarificationApplicable = Count-Applicable 'clarificationCorrect'
        materialCorrect = Count-True 'materialCorrect'
        materialApplicable = Count-Applicable 'materialCorrect'
        unknownCorrect = Count-True 'unknownCorrect'
        unknownApplicable = Count-Applicable 'unknownCorrect'
        tailDecisionCorrect = Count-True 'tailDecisionCorrect'
        totalCliCalls = (@($caseScores | ForEach-Object { $_.cliCalls }) | Measure-Object -Sum).Sum
        totalOpenedTails = (@($caseScores | ForEach-Object { $_.openedTails }) | Measure-Object -Sum).Sum
        promptEvalCount = (@($records | ForEach-Object { $_.usage.promptEvalCount }) | Measure-Object -Sum).Sum
        evalCount = (@($records | ForEach-Object { $_.usage.evalCount }) | Measure-Object -Sum).Sum
        elapsedMs = (@($records | ForEach-Object { $_.elapsedMs }) | Measure-Object -Sum).Sum
    }
    cases = @($caseScores)
}

$summaryDirectory = Split-Path -Parent $SummaryPath
New-Item -ItemType Directory -Path $summaryDirectory -Force | Out-Null
$summary | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $SummaryPath -Encoding utf8

Write-Host "Representation summary written: $SummaryPath"
Write-Host "Passed: $($summary.metrics.passedCases)/$($summary.metrics.totalCases)"
Write-Host "Status: $($summary.metrics.statusCorrect)/$($summary.metrics.totalCases); tails: $($summary.metrics.tailDecisionCorrect)/$($summary.metrics.totalCases)"
if ($cliMode) {
    Write-Host "Queries: $($summary.metrics.queryCorrect)/$($summary.metrics.queryApplicable); CLI calls: $($summary.metrics.totalCliCalls)"
}
