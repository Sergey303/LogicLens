[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('raw', 'teacher-frame')][string] $InputMode,
    [Parameter(Mandatory)][string] $OutputRoot,
    [string] $Model,
    [int] $TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v1.jsonl'
$schemaPath = Join-Path $labRoot 'runner/planner-v1-output.schema.json'
$adapter = Join-Path $PSScriptRoot 'invoke_codex_json.py'
$promptName = if ($InputMode -eq 'raw') { 'planner-v1-raw.md' } else { 'planner-v1-frame.md' }
$promptPath = Join-Path $labRoot "runner/prompts/$promptName"

if (-not [IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot = Join-Path $repoRoot $OutputRoot }
if (Test-Path -LiteralPath $OutputRoot) { throw "Output already exists: $OutputRoot" }
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$runPath = Join-Path $OutputRoot 'run.jsonl'
Copy-Item -LiteralPath $schemaPath -Destination (Join-Path $OutputRoot 'output-schema.json')
Copy-Item -LiteralPath $promptPath -Destination (Join-Path $OutputRoot 'prompt.md')

$systemPrompt = Get-Content -LiteralPath $promptPath -Raw -Encoding utf8
$schemaNote = @'
The response schema requires every plan step to contain revision, date, entity and kind.
For current-material set entity and kind to null. For expand set revision and date to null.
'@
$promptHash = (Get-FileHash -LiteralPath $promptPath -Algorithm SHA256).Hash.ToLowerInvariant()
$commit = (& git -C $repoRoot rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Cannot resolve Git commit: $commit" }
$cliVersion = (& codex --version 2>&1 | Select-Object -First 1).ToString().Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Codex CLI version.' }
$selection = if ([string]::IsNullOrWhiteSpace($Model)) { 'account-default' } else { $Model }
$started = [DateTimeOffset]::UtcNow
$runId = '{0}-planner-v1-codex-{1}-{2}' -f $started.ToString('yyyyMMddTHHmmssZ'), $InputMode, $selection
$count = 0
$errorCount = 0
$nativePreference = $PSNativeCommandUseErrorActionPreference
$PSNativeCommandUseErrorActionPreference = $false

try {
    foreach ($line in Get-Content -LiteralPath $caseFile -Encoding utf8) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $case = $line | ConvertFrom-Json -Depth 40
        $count++
        $caseRoot = Join-Path $OutputRoot "cases/$($case.id)"
        New-Item -ItemType Directory -Path $caseRoot -Force | Out-Null
        $responsePath = Join-Path $caseRoot 'response.json'
        $eventsPath = Join-Path $caseRoot 'events.jsonl'
        $userInput = if ($InputMode -eq 'raw') {
            "User question:`n$($case.questionRu)"
        } else {
            $frame = $case.teacherFrame | ConvertTo-Json -Depth 20 -Compress
            "User question:`n$($case.questionRu)`n`nteacherFrame:`n$frame"
        }
        $providerPrompt = "$systemPrompt`n`n$schemaNote`n`n$userInput"
        $arguments = @(
            $adapter, '--working-directory', $labRoot, '--schema', $schemaPath,
            '--output', $responsePath, '--events', $eventsPath,
            '--timeout-seconds', $TimeoutSeconds
        )
        if (-not [string]::IsNullOrWhiteSpace($Model)) { $arguments += @('--model', $Model) }
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $adapterLog = $providerPrompt | python @arguments 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
        $watch.Stop()
        $parsed = $null
        $raw = $null
        $errorMessage = $null
        if ($exitCode -eq 0 -and (Test-Path -LiteralPath $responsePath)) {
            $raw = Get-Content -LiteralPath $responsePath -Raw -Encoding utf8
            try { $parsed = $raw | ConvertFrom-Json -Depth 40 }
            catch { $errorMessage = "Invalid response JSON: $($_.Exception.Message)" }
        } else {
            $errorMessage = $adapterLog.Trim()
        }
        if ($null -ne $errorMessage) { $errorCount++ }
        $record = [ordered]@{
            schemaVersion = 1; runId = $runId; provider = 'codex-cli'
            caseId = [string] $case.id; taskType = [string] $case.taskType
            inputMode = $InputMode; model = $selection; cliVersion = $cliVersion
            commit = $commit; promptHash = $promptHash; questionRu = [string] $case.questionRu
            plan = $parsed; raw = $raw; elapsedMs = $watch.ElapsedMilliseconds
            eventsPath = "cases/$($case.id)/events.jsonl"; runnerError = $errorMessage
        }
        Add-Content -LiteralPath $runPath -Encoding utf8 -Value ($record | ConvertTo-Json -Depth 50 -Compress)
        $status = if ($null -eq $errorMessage) { [string] $parsed.action } else { 'error' }
        Write-Host "[$count] $($case.id): $status"
    }
}
finally {
    $PSNativeCommandUseErrorActionPreference = $nativePreference
}

Write-Host "Codex planner v1 run: $runPath"
Write-Host "Model selection: $selection; cases: $count; runner errors: $errorCount"
if ($errorCount -gt 0) { throw "Codex planner run completed with $errorCount error(s); artifacts were preserved." }
