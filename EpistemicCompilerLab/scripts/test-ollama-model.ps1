[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $Model,

    [string] $OllamaUri = 'http://127.0.0.1:11434'
)

$ErrorActionPreference = 'Stop'
$ollamaBase = $OllamaUri.TrimEnd('/')

try {
    $tags = Invoke-RestMethod -Method Get -Uri "$ollamaBase/api/tags"
}
catch {
    throw "Ollama is not reachable at $ollamaBase. $($_.Exception.Message)"
}

$availableModels = @($tags.models | ForEach-Object { [string] $_.name })
if ($Model -notin $availableModels) {
    throw "Ollama model '$Model' is not installed. Available: $($availableModels -join ', ')"
}

$payload = [ordered]@{
    model = $Model
    stream = $false
    format = 'json'
    keep_alive = '10m'
    messages = @(
        @{
            role = 'system'
            content = 'Return only one JSON object with fields status and value.'
        },
        @{
            role = 'user'
            content = 'Set status to ok and value to 42.'
        }
    )
    options = @{
        temperature = 0
        seed = 42
        num_predict = 32
    }
}

try {
    $response = Invoke-RestMethod `
        -Method Post `
        -Uri "$ollamaBase/api/chat" `
        -ContentType 'application/json' `
        -Body ($payload | ConvertTo-Json -Depth 20 -Compress)
}
catch {
    throw "Ollama model '$Model' could not run: $($_.Exception.Message)"
}

$raw = [string] $response.message.content
try {
    $parsed = $raw | ConvertFrom-Json -Depth 20
}
catch {
    throw "Model '$Model' returned invalid JSON: $raw"
}

if ($parsed.status -ne 'ok' -or [int] $parsed.value -ne 42) {
    throw "Model '$Model' returned unexpected JSON: $raw"
}

$running = Invoke-RestMethod -Method Get -Uri "$ollamaBase/api/ps"
$loaded = @($running.models | Where-Object {
    $_.name -eq $Model -or $_.model -eq $Model
}) | Select-Object -First 1

if ($null -eq $loaded) {
    throw "Model '$Model' answered but was not found in /api/ps."
}
if ([int64] $loaded.size_vram -ne 0) {
    throw "Model '$Model' is not CPU-only: size_vram=$($loaded.size_vram)."
}

Write-Host "Ollama model smoke passed: $Model"
Write-Host 'Execution verified: CPU-only (size_vram=0)'
Write-Host "Prompt tokens: $($response.prompt_eval_count); output tokens: $($response.eval_count)"
