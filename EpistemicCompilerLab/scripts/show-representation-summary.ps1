[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $SummaryPath
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot

if (-not [IO.Path]::IsPathRooted($SummaryPath)) {
    $SummaryPath = Join-Path $repoRoot $SummaryPath
}
if (-not (Test-Path -LiteralPath $SummaryPath -PathType Leaf)) {
    throw "Summary file not found: $SummaryPath"
}

$summary = Get-Content -LiteralPath $SummaryPath -Raw -Encoding utf8 |
    ConvertFrom-Json -Depth 100
$metrics = $summary.metrics

Write-Host "Mode: $($summary.mode); model: $($summary.model)"
Write-Host "Passed: $($metrics.passedCases)/$($metrics.totalCases); status: $($metrics.statusCorrect)/$($metrics.totalCases)"
Write-Host "Actions: $($metrics.actionCorrect)/$($metrics.totalCases); runner errors: $($metrics.runnerErrors)"

if ($metrics.queryApplicable -gt 0) {
    Write-Host "Queries: $($metrics.queryCorrect)/$($metrics.queryApplicable); CLI calls: $($metrics.totalCliCalls)"
}
if ($metrics.clarificationApplicable -gt 0) {
    Write-Host "Clarifications: $($metrics.clarificationCorrect)/$($metrics.clarificationApplicable)"
}
if ($metrics.materialApplicable -gt 0) {
    Write-Host "Materials: $($metrics.materialCorrect)/$($metrics.materialApplicable)"
}
if ($metrics.tailDecisionApplicable -gt 0) {
    Write-Host "Tails: $($metrics.tailDecisionCorrect)/$($metrics.tailDecisionApplicable)"
}

$failed = @($summary.cases | Where-Object { -not $_.passed })
if ($failed.Count -eq 0) {
    Write-Host 'Failed cases: none'
    return
}

Write-Host "Failed cases: $($failed.Count)"
foreach ($case in $failed) {
    $reasons = [Collections.Generic.List[string]]::new()
    foreach ($check in @(
        'runnerOk',
        'actionCorrect',
        'queryCorrect',
        'statusCorrect',
        'clarificationCorrect',
        'materialCorrect',
        'unknownCorrect',
        'tailDecisionCorrect'
    )) {
        $property = $case.PSObject.Properties[$check]
        if ($null -ne $property -and $null -ne $property.Value -and $property.Value -eq $false) {
            $reasons.Add($check)
        }
    }

    $final = $case.final
    $actual = @(
        "action=$($final.action)",
        "status=$($final.status)",
        "material=$($final.material)",
        "askField=$($final.askField)"
    ) -join ', '
    Write-Host "- $($case.caseId): $($reasons -join ', '); $actual"

    if (-not [string]::IsNullOrWhiteSpace([string] $case.runnerError)) {
        Write-Host "  runnerError=$($case.runnerError)"
    }
}