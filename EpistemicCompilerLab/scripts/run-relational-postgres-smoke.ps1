[CmdletBinding()]
param(
    [string] $Dsn = $env:ENG197_POSTGRES_DSN,
    [string] $OutputPath
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Package = Join-Path $RepoRoot 'EpistemicCompilerLab\research-execution\relational-comparator'
$Requirements = Join-Path $Package 'requirements-eng197.txt'
$RuntimePath = Join-Path $Package 'RUNTIME_DEPENDENCIES.json'
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

# Execution is never allowed to manufacture a new freeze boundary. A producer may
# intentionally regenerate ENG-197_FREEZE_MANIFEST.json only as a separate freeze
# operation before the candidate is handed off. The smoke itself is check-only.
& $python.Source $ManifestBuilder --check
if ($LASTEXITCODE -ne 0) { throw "ENG-197 freeze manifest drift: $LASTEXITCODE" }

$runtime = Get-Content -LiteralPath $RuntimePath -Raw | ConvertFrom-Json
$expectedDigest = [string] $runtime.postgresql.required_container_image_digest
$actualDigest = [string] $env:ENG197_POSTGRES_IMAGE_DIGEST
if ([string]::IsNullOrWhiteSpace($expectedDigest)) {
    throw 'ENG-197 frozen PostgreSQL container digest is missing from RUNTIME_DEPENDENCIES.json.'
}
if ([string]::IsNullOrWhiteSpace($actualDigest)) {
    throw 'ENG197_POSTGRES_IMAGE_DIGEST is required. Re-review evidence must use the frozen pre-execution container digest.'
}
if ($actualDigest -cne $expectedDigest) {
    throw "ENG-197 PostgreSQL image digest drift. Expected '$expectedDigest', got '$actualDigest'."
}

& $python.Source -m pip install --disable-pip-version-check -r $Requirements
if ($LASTEXITCODE -ne 0) { throw "ENG-197 dependency install failed: $LASTEXITCODE" }

& $python.Source $Smoke --dsn $Dsn --output $OutputPath
if ($LASTEXITCODE -ne 0) { throw "ENG-197 live PostgreSQL smoke failed: $LASTEXITCODE" }

# This is deliberately post-smoke: the direct-source reference implementation
# never participates in database execution or pre-score result creation.
& $python.Source $Equivalence --smoke-output $OutputPath
if ($LASTEXITCODE -ne 0) { throw "ENG-197 relational subset equivalence check failed: $LASTEXITCODE" }

Write-Host "ENG-197 live PostgreSQL evidence: $OutputPath"
