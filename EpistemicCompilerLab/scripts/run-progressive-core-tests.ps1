[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$test = Join-Path $labRoot 'progressive-dsl\core-v0\verify_contract.py'

if (-not (Test-Path $test -PathType Leaf)) {
    throw "Epistemic core contract test was not found: $test"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if (-not $python) {
        throw 'Python was not found on PATH.'
    }
    & $python.Source -3 $test
}
else {
    & $python.Source $test
}

if ($LASTEXITCODE -ne 0) {
    throw "Epistemic core contract test failed with code $LASTEXITCODE."
}
