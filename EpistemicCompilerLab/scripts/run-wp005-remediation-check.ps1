[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$executionRoot = Join-Path $repoRoot 'EpistemicCompilerLab\research-execution'
$semanticValidator = Join-Path $executionRoot 'scripts\validate_oracle_semantics.py'
$boundaryValidator = Join-Path $executionRoot 'scripts\validate_oracle_boundary.py'
$goldValidator = Join-Path $executionRoot 'scripts\validate_oracle_gold_governance.py'
$boundary = Join-Path $executionRoot 'oracle\INDEPENDENCE_BOUNDARY.md'
$mutations = Join-Path $executionRoot 'oracle\MUTATION_MATRIX.yaml'

foreach ($path in @($semanticValidator, $boundaryValidator, $goldValidator, $boundary, $mutations)) {
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

Write-Host '[WP-005] Running dedicated semantic contract validation.'
& $pythonCommand @pythonArgs $semanticValidator
if ($LASTEXITCODE -ne 0) {
    throw "WP-005 dedicated semantic validation failed with code $LASTEXITCODE."
}

Write-Host '[WP-005] Checking versioned boundary wrapper availability. This is not semantic execution evidence.'
& $pythonCommand @pythonArgs $boundaryValidator --preflight --boundary $boundary --mutations $mutations
if ($LASTEXITCODE -ne 0) {
    throw "WP-005 boundary wrapper preflight failed with code $LASTEXITCODE."
}

Write-Host '[WP-005] Running blind-gold and candidate-wide lifecycle governance validation.'
& $pythonCommand @pythonArgs $goldValidator
if ($LASTEXITCODE -ne 0) {
    throw "WP-005 gold/lifecycle governance validation failed with code $LASTEXITCODE."
}

Write-Host '[WP-005] Producer remediation preflight PASS only. Path B implementation, human/dependency audits, independent review and GATE-001 remain separate.'
