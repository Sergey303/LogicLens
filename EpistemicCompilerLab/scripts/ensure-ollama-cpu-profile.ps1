[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $BaseModel,

    [string] $ProfileModel,

    [int] $NumCtx = 2048,

    [int] $NumBatch = 64
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ProfileModel)) {
    $safeBase = $BaseModel -replace '[^A-Za-z0-9_.-]', '-'
    $ProfileModel = "epistemic-$safeBase`:cpu-v1"
}

$tagsJson = & ollama list --json 2>$null
if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($tagsJson)) {
    $installed = @($tagsJson | ConvertFrom-Json | ForEach-Object { [string] $_.name })
}
else {
    $installed = @(
        & ollama list |
            Select-Object -Skip 1 |
            ForEach-Object { ($_ -split '\s+')[0] } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
}

if ($BaseModel -notin $installed) {
    throw "Base Ollama model '$BaseModel' is not installed. Available: $($installed -join ', ')"
}

if ($ProfileModel -notin $installed) {
    $modelfile = Join-Path ([IO.Path]::GetTempPath()) (
        'epistemic-ollama-' + [Guid]::NewGuid().ToString('N') + '.Modelfile'
    )

    try {
        @"
FROM $BaseModel
PARAMETER num_gpu 0
PARAMETER num_ctx $NumCtx
PARAMETER num_batch $NumBatch
"@ | Set-Content -LiteralPath $modelfile -Encoding utf8

        & ollama create $ProfileModel -f $modelfile
        if ($LASTEXITCODE -ne 0) {
            throw "ollama create failed with code $LASTEXITCODE."
        }
    }
    finally {
        Remove-Item -LiteralPath $modelfile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Ollama CPU-safe profile: $ProfileModel"
Write-Host "Base model: $BaseModel; num_gpu=0; num_ctx=$NumCtx; num_batch=$NumBatch"
$ProfileModel
