[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$version = (& $swipl --version 2>&1 | Out-String).Trim()

Write-Host "SWI-Prolog: $swipl"
Write-Host "Version: $version"
Write-Host 'Validating benchmark v0...'
& (Join-Path $PSScriptRoot 'validate-cases.ps1')

Write-Host 'Validating benchmark v1 teacher frames...'
& (Join-Path $PSScriptRoot 'validate-benchmark-v1.ps1')

Write-Host 'Validating teacher-loop pilot...'
& (Join-Path $PSScriptRoot 'validate-teacher-loop.ps1')

Write-Host 'Validating representation runner...'
& (Join-Path $PSScriptRoot 'validate-runner.ps1')

Write-Host 'Running benchmark oracle...'
& (Join-Path $PSScriptRoot 'verify-oracle.ps1')

Write-Host 'Running EpistemicCompilerLab tests...'
& (Join-Path $PSScriptRoot 'run-tests.ps1')

Write-Host 'Running CLI smoke test...'
& (Join-Path $PSScriptRoot 'query.ps1') current-material b 20260810

Write-Host 'EpistemicCompilerLab doctor passed.'
