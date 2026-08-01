[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$tests = Join-Path $labRoot 'tests/strict_epistemic_tests.pl'
$entry = Join-Path $labRoot 'prolog/strict_epistemic_entry.pl'

& $swipl -q -s $tests -g 'run_tests,halt'
if ($LASTEXITCODE -ne 0) {
    throw "Strict epistemic tests failed with code $LASTEXITCODE."
}

$completeRaw = (& $swipl -q -s $entry -- request-frame revision_a asd2 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Complete request-frame CLI failed.' }
$complete = $completeRaw | ConvertFrom-Json
if ($complete.status -ne 'supported' -or
    $null -ne $complete.askField -or
    $complete.proposition.predicate -ne 'uses_material' -or
    $complete.proposition.revision -ne 'revision_a' -or
    $complete.proposition.material -ne 'asd2') {
    throw "Complete request-frame JSON contract failed: $completeRaw"
}

$missingRaw = (& $swipl -q -s $entry -- request-frame missing asd2 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Missing-field request-frame CLI failed.' }
$missing = $missingRaw | ConvertFrom-Json
if ($missing.status -ne 'not_evaluated' -or
    $missing.action -ne 'ask_clarification' -or
    $missing.askField -ne 'revision' -or
    $null -ne $missing.proposition) {
    throw "Missing-field request-frame JSON contract failed: $missingRaw"
}

Write-Host 'Strict epistemic oracle and JSON CLI passed.'
