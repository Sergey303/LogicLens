[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('sync-doctor', 'doctor', 'tests', 'cases', 'oracle', 'query')]
    [string] $Action = 'sync-doctor',

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Arguments,

    [string] $RepoRoot = 'D:\projects\ChatPilotGroup\LogicLens'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $RepoRoot -PathType Container)) {
    throw "LogicLens repository was not found: $RepoRoot"
}

$gitDirectory = Join-Path $RepoRoot '.git'
if (-not (Test-Path $gitDirectory)) {
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
