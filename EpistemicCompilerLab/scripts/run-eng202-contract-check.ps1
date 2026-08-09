[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$validator = Join-Path $repoRoot 'EpistemicCompilerLab\research-execution\weight-adaptation-boundary\prototype\validate_eng202_contract.py'

if (-not (Test-Path $validator -PathType Leaf)) {
    throw "ENG-202 contract validator was not found: $validator"
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

Write-Host '[ENG-202] Static contract check only. This is not CUDA smoke or training evidence.'
& $pythonCommand @pythonArgs $validator
if ($LASTEXITCODE -ne 0) {
    throw "ENG-202 contract validator failed with code $LASTEXITCODE."
}
