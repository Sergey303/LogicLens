[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$labRoot = Split-Path -Parent $PSScriptRoot
$tests = Join-Path $labRoot 'tests/knowledge_tests.pl'

& $swipl -q -s $tests -g 'run_tests,halt'

if ($LASTEXITCODE -ne 0) {
    throw "SWI-Prolog tests failed with code $LASTEXITCODE."
}
