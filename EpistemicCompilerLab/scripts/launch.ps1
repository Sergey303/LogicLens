[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet(
        'sync-doctor',
        'doctor',
        'tests',
        'cases',
        'oracle',
        'runner-check',
        'ollama-smoke',
        'representation-run',
        'representation-score',
        'representation-baseline',
        'query'
    )]
    [string] $Action = 'sync-doctor',

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Arguments,

    [string] $RepoRoot = 'D:\projects\ChatPilotGroup\LogicLens'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $RepoRoot -PathType Container)) {
    throw "LogicLens repository was not found: $RepoRoot"
}
if (-not (Test-Path (Join-Path $RepoRoot '.git'))) {
    throw "The directory is not a Git checkout: $RepoRoot"
}

$scriptsRoot = Join-Path $RepoRoot 'EpistemicCompilerLab\scripts'

Push-Location $RepoRoot
try {
    switch ($Action) {
        'sync-doctor' {
            & git pull --ff-only
            if ($LASTEXITCODE -ne 0) {
                throw "git pull failed with code $LASTEXITCODE."
            }
            & (Join-Path $scriptsRoot 'doctor.ps1')
        }
        'doctor' {
            & (Join-Path $scriptsRoot 'doctor.ps1')
        }
        'tests' {
            & (Join-Path $scriptsRoot 'run-tests.ps1')
        }
        'cases' {
            & (Join-Path $scriptsRoot 'validate-cases.ps1')
        }
        'oracle' {
            & (Join-Path $scriptsRoot 'verify-oracle.ps1')
        }
        'runner-check' {
            & (Join-Path $scriptsRoot 'validate-runner.ps1')
        }
        'ollama-smoke' {
            if (-not $Arguments -or $Arguments.Count -ne 1) {
                throw 'Usage: ollama-smoke <base-model>'
            }
            $profileModel = & (Join-Path $scriptsRoot 'ensure-ollama-cpu-profile.ps1') `
                -BaseModel $Arguments[0] |
                Select-Object -Last 1
            & (Join-Path $scriptsRoot 'test-ollama-model.ps1') -Model $profileModel
        }
        'representation-run' {
            if (-not $Arguments -or $Arguments.Count -lt 2 -or $Arguments.Count -gt 3) {
                throw 'Usage: representation-run <mode> <execution-model> [absolute-output-path]'
            }
            $runParameters = @{
                Mode = $Arguments[0]
                Model = $Arguments[1]
            }
            if ($Arguments.Count -eq 3) {
                $runParameters.OutputPath = $Arguments[2]
            }
            & (Join-Path $scriptsRoot 'run-representation.ps1') @runParameters
        }
        'representation-score' {
            if (-not $Arguments -or $Arguments.Count -lt 1 -or $Arguments.Count -gt 2) {
                throw 'Usage: representation-score <run-jsonl-path> [summary-json-path]'
            }
            $scoreParameters = @{ RunPath = $Arguments[0] }
            if ($Arguments.Count -eq 2) {
                $scoreParameters.SummaryPath = $Arguments[1]
            }
            & (Join-Path $scriptsRoot 'score-representation.ps1') @scoreParameters
        }
        'representation-baseline' {
            if (-not $Arguments -or $Arguments.Count -ne 2) {
                throw 'Usage: representation-baseline <mode> <base-model>'
            }
            & (Join-Path $scriptsRoot 'run-representation-baseline.ps1') `
                -Mode $Arguments[0] `
                -Model $Arguments[1]
        }
        'query' {
            if (-not $Arguments -or $Arguments.Count -eq 0) {
                throw 'Query arguments are required, for example: query current-material b 20260810'
            }
            & (Join-Path $scriptsRoot 'query.ps1') @Arguments
        }
    }
}
finally {
    Pop-Location
}
