[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$executionRoot = Join-Path $repoRoot 'EpistemicCompilerLab\research-execution'
$validator = Join-Path $executionRoot 'scripts\validate_oracle_boundary.py'
$boundary = Join-Path $executionRoot 'oracle\INDEPENDENCE_BOUNDARY.md'
$mutations = Join-Path $executionRoot 'oracle\MUTATION_MATRIX.yaml'

foreach ($path in @($validator, $boundary, $mutations)) {
    if (-not (Test-Path $path -PathType Leaf)) {
        throw "WP-005 required artifact was not found: $path"
    }
}

$pythonCommand = $null
$pythonArgs = @()

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & $py.Source -3.11 -c "import sys; print(sys.version)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $pythonCommand = $py.Source
        $pythonArgs = @('-3.11')
    }
}

if (-not $pythonCommand) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw 'Python was not found. Install Python 3.11 or expose python/py on PATH.'
    }
    $pythonCommand = $python.Source
}

Write-Host '[WP-005] Running local semantic/oracle boundary validation. No GitHub Actions are used.'
& $pythonCommand @pythonArgs $validator --preflight --boundary $boundary --mutations $mutations
if ($LASTEXITCODE -ne 0) {
    throw "WP-005 semantic/oracle validation failed with code $LASTEXITCODE."
}

Write-Host '[WP-005] Producer preflight PASS only. Independent review and GATE-001 approval are still separate.'
