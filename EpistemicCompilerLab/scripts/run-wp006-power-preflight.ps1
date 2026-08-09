[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$root = Join-Path $repoRoot 'EpistemicCompilerLab\research-execution\power-analysis'
$complete = Join-Path $root 'prototype\validate_wp006_complete.py'
$calculator = Join-Path $root 'prototype\calculate_power.py'
$simulation = Join-Path $root 'prototype\simulate_power.py'

foreach ($path in @($complete, $calculator, $simulation)) {
    if (-not (Test-Path $path -PathType Leaf)) {
        throw "WP-006 required artifact was not found: $path"
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

Write-Host '[WP-006] Complete contract + gate negative controls. No GitHub Actions are used.'
& $pythonCommand @pythonArgs $complete
if ($LASTEXITCODE -ne 0) { throw "WP-006 complete validator failed with code $LASTEXITCODE." }

Write-Host '[WP-006] Frozen analytical primary and sensitivity grid.'
& $pythonCommand @pythonArgs $calculator --sensitivity
if ($LASTEXITCODE -ne 0) { throw "WP-006 power calculator failed with code $LASTEXITCODE." }

Write-Host '[WP-006] Frozen 20,000-replicate clustered Monte-Carlo cross-check.'
& $pythonCommand @pythonArgs $simulation --repetitions 20000 --seed 158006
if ($LASTEXITCODE -ne 0) { throw "WP-006 power simulation failed with code $LASTEXITCODE." }

Write-Host '[WP-006] Producer design preflight PASS only. Real benchmark inventory gate and independent statistical review remain separate.'
