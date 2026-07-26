[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v1.jsonl'
$ids = [Collections.Generic.HashSet[string]]::new()
$taskTypes = @('material_selection', 'clarification', 'explanation', 'exception_inspection')
$intents = @('select_material', 'explain_rule', 'inspect_exceptions')
$actions = @('query', 'ask_user')
$statuses = @('success', 'unknown', 'need_user')
$operations = @('current-material', 'expand')
$count = 0
$lineNumber = 0

function Require-Property {
    param($Object, [string] $Name, [string] $Context)
    if (-not $Object.PSObject.Properties[$Name]) {
        throw "Missing '$Name' in $Context."
    }
}

foreach ($line in Get-Content -LiteralPath $caseFile -Encoding utf8) {
    $lineNumber++
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    try { $case = $line | ConvertFrom-Json -Depth 40 }
    catch { throw "Invalid JSON at line ${lineNumber}: $($_.Exception.Message)" }

    $context = "benchmark-v1 line $lineNumber"
    foreach ($name in @('schemaVersion', 'id', 'taskType', 'questionRu', 'teacherFrame', 'expected')) {
        Require-Property $case $name $context
    }
    if ($case.schemaVersion -ne 1) { throw "Unsupported schemaVersion in '$($case.id)'." }
    if (-not $ids.Add([string] $case.id)) { throw "Duplicate id '$($case.id)'." }
    if ($case.taskType -notin $taskTypes) { throw "Invalid taskType in '$($case.id)'." }

    $frame = $case.teacherFrame
    foreach ($name in @('intent', 'revision', 'date', 'entity', 'tailKind', 'missingFields')) {
        Require-Property $frame $name "teacherFrame '$($case.id)'"
    }
    if ($frame.intent -notin $intents) { throw "Invalid intent in '$($case.id)'." }
    $missing = @($frame.missingFields)
    if (@($missing | Where-Object { $_ -notin @('revision', 'date') }).Count -gt 0) {
        throw "Invalid missingFields in '$($case.id)'."
    }

    $expected = $case.expected
    foreach ($name in @('action', 'status', 'plan', 'askField', 'material', 'scoring')) {
        Require-Property $expected $name "expected '$($case.id)'"
    }
    if ($expected.action -notin $actions -or $expected.status -notin $statuses) {
        throw "Invalid action or status in '$($case.id)'."
    }
    foreach ($name in @('material', 'unknown', 'clarification', 'tail')) {
        Require-Property $expected.scoring $name "scoring '$($case.id)'"
    }

    $plan = @($expected.plan)
    if ($expected.action -eq 'ask_user') {
        if ($expected.status -ne 'need_user' -or $plan.Count -ne 0) {
            throw "Clarification contract mismatch in '$($case.id)'."
        }
        if ($expected.askField -notin $missing -or -not $expected.scoring.clarification) {
            throw "askField mismatch in '$($case.id)'."
        }
    }
    else {
        if ($missing.Count -ne 0 -or $plan.Count -eq 0 -or $null -ne $expected.askField) {
            throw "Query contract mismatch in '$($case.id)'."
        }
    }

    foreach ($step in $plan) {
        Require-Property $step 'operation' "plan '$($case.id)'"
        Require-Property $step 'arguments' "plan '$($case.id)'"
        if ($step.operation -notin $operations) { throw "Invalid operation in '$($case.id)'." }
        if ($step.operation -eq 'current-material') {
            foreach ($name in @('revision', 'date')) {
                Require-Property $step.arguments $name "current-material '$($case.id)'"
            }
            if ($step.arguments.revision -ne $frame.revision -or $step.arguments.date -ne $frame.date) {
                throw "current-material invents or changes frame values in '$($case.id)'."
            }
        }
        else {
            foreach ($name in @('entity', 'kind')) {
                Require-Property $step.arguments $name "expand '$($case.id)'"
            }
            if ($step.arguments.entity -ne $frame.entity -or $step.arguments.kind -ne $frame.tailKind) {
                throw "expand invents or changes frame values in '$($case.id)'."
            }
        }
    }

    if ($case.taskType -ne 'material_selection' -and $expected.scoring.material) {
        throw "Non-selection task requires material in '$($case.id)'."
    }
    if ($case.taskType -eq 'explanation') {
        if ($frame.intent -ne 'explain_rule' -or $frame.tailKind -ne 'evidence' -or
            -not $expected.scoring.tail -or ($plan.operation -join ',') -ne 'current-material,expand') {
            throw "Explanation contract mismatch in '$($case.id)'."
        }
    }
    if ($case.taskType -eq 'exception_inspection') {
        if ($frame.intent -ne 'inspect_exceptions' -or $frame.tailKind -ne 'exceptions' -or
            $null -ne $frame.revision -or $null -ne $frame.date -or
            -not $expected.scoring.tail -or ($plan.operation -join ',') -ne 'expand') {
            throw "Exception contract mismatch in '$($case.id)'."
        }
    }

    $count++
}

if ($count -ne 9) { throw "Expected 9 benchmark-v1 cases, found $count." }
Write-Host "Benchmark v1 frames valid: $count"
