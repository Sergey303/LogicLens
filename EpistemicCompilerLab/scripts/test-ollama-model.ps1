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
    }
}

$response = Invoke-RestMethod `
    -Method Post `
    -Uri "$ollamaBase/api/chat" `
    -ContentType 'application/json' `
    -Body ($payload | ConvertTo-Json -Depth 20 -Compress)

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

Write-Host "Ollama model smoke passed: $Model"
Write-Host "Prompt tokens: $($response.prompt_eval_count); output tokens: $($response.eval_count)"
