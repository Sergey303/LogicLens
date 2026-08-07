[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Package = Join-Path $RepoRoot 'EpistemicCompilerLab\research-execution\router-comparator'
$Verify = Join-Path $Package 'prototype\verify.py'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'python is required.'
}
if (-not (Get-Command swipl -ErrorAction SilentlyContinue)) {
    throw 'SWI-Prolog (swipl) is required.'
}

Push-Location $Package
try {
    & python 'prototype\generate_policy.py'
    if ($LASTEXITCODE -ne 0) { throw "generate_policy failed: $LASTEXITCODE" }
    & python 'prototype\generate_visible_catalogue.py'
    if ($LASTEXITCODE -ne 0) { throw "generate_visible_catalogue failed: $LASTEXITCODE" }
    & python $Verify --require-swipl
    if ($LASTEXITCODE -ne 0) { throw "router verification failed: $LASTEXITCODE" }
}
finally {
    Pop-Location
}
