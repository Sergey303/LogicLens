[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('raw', 'teacher-frame')]
    [string] $InputMode,

    [Parameter(Mandatory)]
    [string] $Model,

    [Parameter(Mandatory)]
    [string] $OutputPath,

    [string] $OllamaUri = 'http://127.0.0.1:11434'
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v1.jsonl'
$promptName = if ($InputMode -eq 'raw') { 'planner-v1-raw.md' } else { 'planner-v1-frame.md' }
$promptPath = Join-Path $labRoot "runner/prompts/$promptName"
$ollamaBase = $OllamaUri.TrimEnd('/')

if (-not [IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath = Join-Path $repoRoot $OutputPath
}
if (Test-Path -LiteralPath $OutputPath) {
    throw "Output already exists: $OutputPath"
}
New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force | Out-Null

try { $tags = Invoke-RestMethod -Method Get -Uri "$ollamaBase/api/tags" }
catch { throw "Ollama is not reachable at $ollamaBase. $($_.Exception.Message)" }
$available = @($tags.models | ForEach-Object { [string] $_.name })
if ($Model -notin $available) {
    throw "Ollama model '$Model' is not installed. Available: $($available -join ', ')"
}

$systemPrompt = Get-Content -LiteralPath $promptPath -Raw -Encoding utf8
$promptHash = (Get-FileHash -LiteralPath $promptPath -Algorithm SHA256).Hash.ToLowerInvariant()
$commit = (& git -C $repoRoot rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Cannot resolve Git commit: $commit" }
$started = [DateTimeOffset]::UtcNow
$runId = '{0}-planner-v1-{1}' -f $started.ToString('yyyyMMddTHHmmssZ'), $InputMode
$count = 0
$errorCount = 0

foreach ($line in Get-Content -LiteralPath $caseFile -Encoding utf8) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $case = $line | ConvertFrom-Json -Depth 40
    $count++
    $errorMessage = $null
    $parsed = $null
    $raw = $null
    $watch = [Diagnostics.Stopwatch]::StartNew()

    try {
        $userPrompt = if ($InputMode -eq 'raw') {
            "User question:`n$($case.questionRu)"
        }
        else {
            $frameJson = $case.teacherFrame | ConvertTo-Json -Depth 20 -Compress
            "User question:`n$($case.questionRu)`n`nteacherFrame:`n$frameJson"
        }
        $payload = [ordered]@{
            model = $Model
            stream = $false
            format = 'json'
            keep_alive = '10m'
            messages = @(
                @{ role = 'system'; content = $systemPrompt },
                @{ role = 'user'; content = $userPrompt }
            )
            options = @{ temperature = 0; seed = 42; num_predict = 256 }
        }
        $response = Invoke-RestMethod `
            -Method Post `
            -Uri "$ollamaBase/api/chat" `
            -ContentType 'application/json' `
            -Body ($payload | ConvertTo-Json -Depth 30 -Compress)
        $raw = [string] $response.message.content
        $parsed = $raw | ConvertFrom-Json -Depth 40
    }
    catch {
        $errorCount++
        $errorMessage = $_.Exception.Message
    }
    finally { $watch.Stop() }

    $record = [ordered]@{
        schemaVersion = 1
        runId = $runId
        caseId = [string] $case.id
        taskType = [string] $case.taskType
        inputMode = $InputMode
        model = $Model
        commit = $commit
        promptHash = $promptHash
        questionRu = [string] $case.questionRu
        plan = $parsed
        raw = $raw
        elapsedMs = $watch.ElapsedMilliseconds
        promptEvalCount = if ($null -ne $response) { $response.prompt_eval_count } else { $null }
        evalCount = if ($null -ne $response) { $response.eval_count } else { $null }
        runnerError = $errorMessage
    }
    Add-Content -LiteralPath $OutputPath -Encoding utf8 `
        -Value ($record | ConvertTo-Json -Depth 50 -Compress)
    $status = if ($null -eq $errorMessage) { [string] $parsed.action } else { 'error' }
    Write-Host "[$count] $($case.id): $status"
    $response = $null
}

Write-Host "Planner v1 run written: $OutputPath"
Write-Host "Cases: $count; runner errors: $errorCount"
if ($errorCount -gt 0) {
    throw "Planner v1 run completed with $errorCount error(s); results were preserved."
}
