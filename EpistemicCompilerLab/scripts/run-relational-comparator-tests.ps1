[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$test = Join-Path $labRoot 'research-execution\relational-comparator\prototype\verify.py'

if (-not (Test-Path $test -PathType Leaf)) {
    throw "ENG-197 relational comparator verification was not found: $test"
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
    throw "ENG-197 relational comparator verification failed with code $LASTEXITCODE."
}
