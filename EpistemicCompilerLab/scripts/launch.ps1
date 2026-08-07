[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet(
        'sync-doctor',
        'doctor',
        'tests',
        'strict-epistemic-tests',
        'synthetic-kernel-tests',
        'relational-comparator-tests',
        'progressive-core-tests',
        'generate-strict-epistemic-benchmark',
        'cases',
        'cases-v1',
        'oracle',
        'runner-check',
        'ollama-smoke',
        'codex-smoke',
        'planner-v1-codex-pair',
        'teacher-loop',
        'compiled-frame',
        'compiled-frame-replication',
        'generate-replication',
        'representation-run',
        'representation-score',
        'representation-baseline',
        'representation-suite',
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
            if ($LASTEXITCODE -ne 0) { throw "git pull failed with code $LASTEXITCODE." }
            & (Join-Path $scriptsRoot 'doctor.ps1')
        }
        'doctor' { & (Join-Path $scriptsRoot 'doctor.ps1') }
        'tests' { & (Join-Path $scriptsRoot 'run-tests.ps1') }
        'strict-epistemic-tests' { & (Join-Path $scriptsRoot 'run-strict-epistemic-tests.ps1') }
        'synthetic-kernel-tests' { & (Join-Path $scriptsRoot 'run-progressive-core-tests.ps1') }
        'relational-comparator-tests' { & (Join-Path $scriptsRoot 'run-relational-comparator-tests.ps1') }
        'progressive-core-tests' { & (Join-Path $scriptsRoot 'run-progressive-core-tests.ps1') }
        'generate-strict-epistemic-benchmark' {
            & (Join-Path $scriptsRoot 'run-generate-strict-epistemic-benchmark.ps1')
        }
        'cases' { & (Join-Path $scriptsRoot 'validate-cases.ps1') }
        'cases-v1' { & (Join-Path $scriptsRoot 'validate-benchmark-v1.ps1') }
        'oracle' { & (Join-Path $scriptsRoot 'verify-oracle.ps1') }
        'runner-check' { & (Join-Path $scriptsRoot 'validate-runner.ps1') }
        'ollama-smoke' {
            if (-not $Arguments -or $Arguments.Count -ne 1) { throw 'Usage: ollama-smoke <base-model>' }
            $profileModel = & (Join-Path $scriptsRoot 'ensure-ollama-cpu-profile.ps1') `
                -BaseModel $Arguments[0] | Select-Object -Last 1
            & (Join-Path $scriptsRoot 'test-ollama-model.ps1') -Model $profileModel
        }
        'codex-smoke' {
            if ($Arguments -and $Arguments.Count -gt 1) { throw 'Usage: codex-smoke [explicit-model]' }
            $parameters = @{}
            if ($Arguments) { $parameters.Model = $Arguments[0] }
            & (Join-Path $scriptsRoot 'test-codex-cli.ps1') @parameters
        }
        'planner-v1-codex-pair' {
            if ($Arguments -and $Arguments.Count -gt 1) { throw 'Usage: planner-v1-codex-pair [explicit-model]' }
            $parameters = @{}
            if ($Arguments) { $parameters.Model = $Arguments[0] }
            & (Join-Path $scriptsRoot 'run-planner-v1-codex-pair.ps1') @parameters
        }
        'teacher-loop' {
            if ($Arguments -and $Arguments.Count -gt 3) { throw 'Usage: teacher-loop [prompt|prolog|combined] [epochs] [base-model]' }
            $parameters = @{}
            if ($Arguments -and $Arguments.Count -ge 1) { $parameters.Track = $Arguments[0] }
            if ($Arguments -and $Arguments.Count -ge 2) { $parameters.Epochs = [int] $Arguments[1] }
            if ($Arguments -and $Arguments.Count -eq 3) { $parameters.BaseModel = $Arguments[2] }
            & (Join-Path $scriptsRoot 'run-teacher-loop.ps1') @parameters
        }
        'compiled-frame' {
            if ($Arguments -and $Arguments.Count -gt 1) { throw 'Usage: compiled-frame [base-model]' }
            $parameters = @{}
            if ($Arguments) { $parameters.BaseModel = $Arguments[0] }
            & (Join-Path $scriptsRoot 'run-compiled-frame.ps1') @parameters
        }
        'compiled-frame-replication' {
            if ($Arguments -and $Arguments.Count -gt 1) { throw 'Usage: compiled-frame-replication [base-model]' }
            $parameters = @{}
            if ($Arguments) { $parameters.BaseModel = $Arguments[0] }
            & (Join-Path $scriptsRoot 'run-compiled-frame-replication.ps1') @parameters
        }
        'generate-replication' {
            if ($Arguments -and $Arguments.Count -gt 1) { throw 'Usage: generate-replication [explicit-model]' }
            $parameters = @{}
            if ($Arguments) { $parameters.CodexModel = $Arguments[0] }
            & (Join-Path $scriptsRoot 'run-generate-replication.ps1') @parameters
        }
        'representation-run' {
            if (-not $Arguments -or $Arguments.Count -lt 2 -or $Arguments.Count -gt 3) { throw 'Usage: representation-run <mode> <execution-model> [absolute-output-path]' }
            $parameters = @{ Mode = $Arguments[0]; Model = $Arguments[1] }
            if ($Arguments.Count -eq 3) { $parameters.OutputPath = $Arguments[2] }
            & (Join-Path $scriptsRoot 'run-representation.ps1') @parameters
        }
        'representation-score' {
            if (-not $Arguments -or $Arguments.Count -lt 1 -or $Arguments.Count -gt 2) { throw 'Usage: representation-score <run-jsonl-path> [summary-json-path]' }
            $parameters = @{ RunPath = $Arguments[0] }
            if ($Arguments.Count -eq 2) { $parameters.SummaryPath = $Arguments[1] }
            & (Join-Path $scriptsRoot 'score-representation.ps1') @parameters
        }
        'representation-baseline' {
            if (-not $Arguments -or $Arguments.Count -ne 2) { throw 'Usage: representation-baseline <mode> <base-model>' }
            & (Join-Path $scriptsRoot 'run-representation-baseline.ps1') -Mode $Arguments[0] -Model $Arguments[1]
        }
        'representation-suite' {
            if (-not $Arguments -or $Arguments.Count -ne 1) { throw 'Usage: representation-suite <base-model>' }
            & (Join-Path $scriptsRoot 'run-representation-suite.ps1') -Model $Arguments[0]
        }
        'query' {
            if (-not $Arguments -or $Arguments.Count -eq 0) { throw 'Query arguments are required.' }
            & (Join-Path $scriptsRoot 'query.ps1') @Arguments
        }
    }
}
finally {
    Pop-Location
}
