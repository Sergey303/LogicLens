[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$tests = Join-Path $labRoot 'tests/strict_epistemic_tests.pl'
$caseTests = Join-Path $labRoot 'tests/strict_epistemic_case_tests.pl'
$entry = Join-Path $labRoot 'prolog/strict_epistemic_entry.pl'
$caseEntry = Join-Path $labRoot 'prolog/strict_epistemic_case_entry.pl'

foreach ($testFile in @($tests, $caseTests)) {
    & $swipl -q -s $testFile -g 'run_tests,halt'
    if ($LASTEXITCODE -ne 0) {
        throw "Strict epistemic tests failed: $testFile"
    }
}

$completeRaw = (& $swipl -q -s $entry -- request-frame revision_a asd2 | Out-String).Trim()
$complete = $completeRaw | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $complete.status -ne 'supported' -or
    $null -ne $complete.askField -or
    $complete.proposition.predicate -ne 'uses_material') {
    throw "Complete request-frame JSON contract failed: $completeRaw"
}

$missingRaw = (& $swipl -q -s $entry -- request-frame missing asd2 | Out-String).Trim()
$missing = $missingRaw | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $missing.status -ne 'not_evaluated' -or
    $missing.askField -ne 'revision' -or $null -ne $missing.proposition) {
    throw "Missing-field request-frame JSON contract failed: $missingRaw"
}

$caseRaw = (& $swipl -q -s $caseEntry -- case-frame RX-TEST MX-TEST p1 n1 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $caseRaw -match 'ERROR:') {
    throw "Generic case-frame CLI emitted an error: $caseRaw"
}
$case = $caseRaw | ConvertFrom-Json
if ($case.status -ne 'conflicting' -or
    $case.action -ne 'report_conflict' -or @($case.evidence).Count -ne 2) {
    throw "Generic case-frame JSON contract failed: $caseRaw"
}

$invalidRaw = (& $swipl -q -s $caseEntry -- invalid 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $invalidRaw -match 'ERROR:') {
    throw "Generic case-frame fallback emitted an error: $invalidRaw"
}
$invalid = $invalidRaw | ConvertFrom-Json
if ($invalid.status -ne 'invalid_request' -or @($invalid.usage).Count -ne 1) {
    throw "Generic case-frame fallback contract failed: $invalidRaw"
}

Write-Host 'Strict epistemic fixture, generic oracle and JSON CLIs passed.'
