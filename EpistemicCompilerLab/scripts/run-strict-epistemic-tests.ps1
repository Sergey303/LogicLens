[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$tests = Join-Path $labRoot 'tests/strict_epistemic_tests.pl'

& $swipl -q -s $tests -g 'run_tests,halt'
if ($LASTEXITCODE -ne 0) {
    throw "Strict epistemic tests failed with code $LASTEXITCODE."
}

Write-Host 'Strict epistemic oracle passed.'
