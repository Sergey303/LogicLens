[CmdletBinding()]
param(
    [string] $Dsn = $env:ENG197_POSTGRES_DSN,
    [string] $OutputPath
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Package = Join-Path $RepoRoot 'EpistemicCompilerLab\research-execution\relational-comparator'
$Requirements = Join-Path $Package 'requirements-eng197.txt'
$ManifestBuilder = Join-Path $Package 'prototype\build_freeze_manifest.py'
$Smoke = Join-Path $Package 'prototype\live_postgres_smoke.py'
$Equivalence = Join-Path $Package 'prototype\build_subset_equivalence_report.py'

if ([string]::IsNullOrWhiteSpace($Dsn)) {
    throw 'ENG197_POSTGRES_DSN or -Dsn is required. Use a disposable database whose name starts with eng197_.'
}
if (-not $OutputPath) {
    $OutputPath = Join-Path $RepoRoot 'artifacts\eng-197\postgres-smoke'
}
if (Test-Path $OutputPath) {
    $existing = Get-ChildItem -LiteralPath $OutputPath -Force -ErrorAction SilentlyContinue
    if ($existing) { throw "Output directory must be absent or empty: $OutputPath" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'python is required.' }

& $python.Source -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw "ENG-197 dependency install failed: $LASTEXITCODE" }

# Build the complete scientific/runtime closure from the exact checkout, then
# immediately require byte-identical check before touching PostgreSQL.
& $python.Source $ManifestBuilder
if ($LASTEXITCODE -ne 0) { throw "ENG-197 freeze manifest build failed: $LASTEXITCODE" }
& $python.Source $ManifestBuilder --check
if ($LASTEXITCODE -ne 0) { throw "ENG-197 freeze manifest check failed: $LASTEXITCODE" }

& $python.Source $Smoke --dsn $Dsn --output $OutputPath
if ($LASTEXITCODE -ne 0) { throw "ENG-197 live PostgreSQL smoke failed: $LASTEXITCODE" }

# This is deliberately post-smoke: the direct-source reference implementation
# never participates in database execution or pre-score result creation.
& $python.Source $Equivalence --smoke-output $OutputPath
if ($LASTEXITCODE -ne 0) { throw "ENG-197 relational subset equivalence check failed: $LASTEXITCODE" }

Write-Host "ENG-197 live PostgreSQL evidence: $OutputPath"
