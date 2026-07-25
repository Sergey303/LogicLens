[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$version = (& $swipl --version 2>&1 | Out-String).Trim()

Write-Host "SWI-Prolog: $swipl"
Write-Host "Version: $version"
Write-Host 'Running EpistemicCompilerLab tests...'

& (Join-Path $PSScriptRoot 'run-tests.ps1')

Write-Host 'Running CLI smoke test...'
& (Join-Path $PSScriptRoot 'query.ps1') current-material b 20260810
