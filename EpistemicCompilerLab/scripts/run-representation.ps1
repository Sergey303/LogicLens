[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('markdown', 'compact-json', 'prolog-text', 'cli', 'cli-tails')]
    [string] $Mode,

    [Parameter(Mandatory)]
    [string] $Model,

    [string] $OutputPath,

    [string] $OllamaUri = 'http://127.0.0.1:11434',

    [int] $Seed = 42,

    [double] $Temperature = 0,

    [switch] $Force
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v0.jsonl'
$entryPoint = Join-Path $labRoot 'prolog/entry.pl'
$promptRoot = Join-Path $labRoot 'runner/prompts'
$runRoot = Join-Path $labRoot 'experiments/model-runs'
$ollamaBase = $OllamaUri.TrimEnd('/')
$runStarted = [DateTimeOffset]::UtcNow
$safeModel = $Model -replace '[^A-Za-z0-9_.-]', '_'
$runId = '{0}-{1}-{2}' -f $runStarted.ToString('yyyyMMddTHHmmssZ'), $Mode, $safeModel

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $runRoot ($runId + '.jsonl')
}
elseif (-not [IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath = Join-Path $repoRoot $OutputPath
}

if ((Test-Path -LiteralPath $OutputPath) -and -not $Force) {
    throw "Output already exists: $OutputPath. Use -Force to replace it."
}

$outputDirectory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
if (Test-Path -LiteralPath $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
}

function Get-TextHash {
    param([Parameter(Mandatory)][string] $Path)
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Invoke-OllamaJson {
    param(
        [Parameter(Mandatory)][string] $SystemPrompt,
        [Parameter(Mandatory)][string] $UserPrompt,
        [Parameter(Mandatory)][string] $Stage
    )

    $payload = [ordered]@{
        model = $Model
        stream = $false
        format = 'json'
        messages = @(
            @{ role = 'system'; content = $SystemPrompt },
            @{ role = 'user'; content = $UserPrompt }
        )
        options = @{
            temperature = $Temperature
            seed = $Seed
        }
    }

    $stopwatch = [Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-RestMethod `
            -Method Post `
            -Uri "$ollamaBase/api/chat" `
            -ContentType 'application/json' `
            -Body ($payload | ConvertTo-Json -Depth 30 -Compress)
    }
    catch {
        throw "Ollama stage '$Stage' failed: $($_.Exception.Message)"
    }
    finally {
        $stopwatch.Stop()
    }

    $raw = [string] $response.message.content
    try {
        $parsed = $raw | ConvertFrom-Json -Depth 50
    }
    catch {
        throw "Ollama stage '$Stage' returned invalid JSON: $raw"
    }

    [pscustomobject]@{
        Stage = $Stage
        Parsed = $parsed
        Raw = $raw
        ElapsedMs = $stopwatch.ElapsedMilliseconds
        PromptEvalCount = $response.prompt_eval_count
        EvalCount = $response.eval_count
        TotalDurationNs = $response.total_duration
    }
}

function Invoke-PrologJson {
    param([Parameter(Mandatory)][string[]] $CliArguments)

    $raw = & $script:swipl -q -s $entryPoint -- @CliArguments 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "SWI-Prolog failed for '$($CliArguments -join ' ')': $raw"
    }

    try {
        $parsed = $raw | ConvertFrom-Json -Depth 50
    }
    catch {
        throw "SWI-Prolog returned invalid JSON for '$($CliArguments -join ' ')': $raw"
    }

    [pscustomobject]@{
        Arguments = $CliArguments
        Parsed = $parsed
        Raw = $raw.Trim()
    }
}

function Add-JsonLine {
    param([Parameter(Mandatory)] $Value)
    Add-Content -LiteralPath $OutputPath -Encoding utf8 -Value ($Value | ConvertTo-Json -Depth 50 -Compress)
}

try {
    $tags = Invoke-RestMethod -Method Get -Uri "$ollamaBase/api/tags"
}
catch {
    throw "Ollama is not reachable at $ollamaBase. Start Ollama and verify its local API. $($_.Exception.Message)"
}

$availableModels = @($tags.models | ForEach-Object { [string] $_.name })
if ($Model -notin $availableModels) {
    throw "Ollama model '$Model' is not installed. Available models: $($availableModels -join ', ')"
}

$directPromptPath = Join-Path $promptRoot 'direct.md'
$plannerPromptPath = Join-Path $promptRoot 'planner.md'
$tailPromptPath = Join-Path $promptRoot 'tail-planner.md'
$finalizePromptPath = Join-Path $promptRoot 'finalize.md'
$directPrompt = Get-Content -LiteralPath $directPromptPath -Raw -Encoding utf8
$plannerPrompt = Get-Content -LiteralPath $plannerPromptPath -Raw -Encoding utf8
$tailPrompt = Get-Content -LiteralPath $tailPromptPath -Raw -Encoding utf8
$finalizePrompt = Get-Content -LiteralPath $finalizePromptPath -Raw -Encoding utf8
$promptHashes = [ordered]@{
    direct = Get-TextHash $directPromptPath
    planner = Get-TextHash $plannerPromptPath
    tailPlanner = Get-TextHash $tailPromptPath
    finalize = Get-TextHash $finalizePromptPath
}

$representationPath = switch ($Mode) {
    'markdown' { Join-Path $labRoot 'sources/materials.md' }
    'compact-json' { Join-Path $labRoot 'representations/knowledge.compact.json' }
    'prolog-text' { Join-Path $labRoot 'prolog/knowledge.pl' }
    default { $null }
}

$representationText = $null
$representationHash = $null
if ($null -ne $representationPath) {
    $representationText = Get-Content -LiteralPath $representationPath -Raw -Encoding utf8
    $representationHash = Get-TextHash $representationPath
}

$swipl = $null
if ($Mode -in @('cli', 'cli-tails')) {
    $swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
}

$commit = (& git -C $repoRoot rev-parse HEAD 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Cannot resolve the LogicLens Git commit: $commit"
}

$caseCount = 0
$runnerErrorCount = 0
foreach ($line in Get-Content -LiteralPath $caseFile -Encoding utf8) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $case = $line | ConvertFrom-Json -Depth 50
    $caseCount++
    $caseStarted = [DateTimeOffset]::UtcNow
    $caseStopwatch = [Diagnostics.Stopwatch]::StartNew()
    $planner = $null
    $tailPlan = $null
    $final = $null
    $cliCalls = [Collections.Generic.List[object]]::new()
    $openedTails = [Collections.Generic.List[object]]::new()
    $modelResponses = [Collections.Generic.List[object]]::new()
    $runnerError = $null

    try {
        if ($Mode -in @('markdown', 'compact-json', 'prolog-text')) {
            $userPrompt = @"
Representation mode: $Mode

Approved knowledge representation:
---BEGIN REPRESENTATION---
$representationText
---END REPRESENTATION---

User question:
$($case.questionRu)
"@
            $response = Invoke-OllamaJson -SystemPrompt $directPrompt -UserPrompt $userPrompt -Stage 'direct'
            $modelResponses.Add($response)
            $final = $response.Parsed
        }
        else {
            $plannerUserPrompt = "User question:`n$($case.questionRu)"
            $plannerResponse = Invoke-OllamaJson -SystemPrompt $plannerPrompt -UserPrompt $plannerUserPrompt -Stage 'planner'
            $modelResponses.Add($plannerResponse)
            $planner = $plannerResponse.Parsed

            if ($planner.action -eq 'ask_user') {
                $final = [ordered]@{
                    action = 'ask_user'
                    status = 'need_user'
                    material = $null
                    askField = $planner.askField
                    answerRu = "Нужно уточнить обязательное поле: $($planner.askField)."
                }
            }
            elseif ($planner.action -eq 'query') {
                if ($planner.operation -ne 'current-material') {
                    throw "Planner selected unsupported operation '$($planner.operation)'."
                }
                if ([string]::IsNullOrWhiteSpace([string] $planner.revision) -or $null -eq $planner.date) {
                    throw 'Planner selected query without revision or date.'
                }

                $revision = ([string] $planner.revision).ToLowerInvariant()
                $date = [string] ([int64] $planner.date)
                $baseCall = Invoke-PrologJson -CliArguments @('current-material', $revision, $date)
                $cliCalls.Add([ordered]@{
                    operation = 'current-material'
                    arguments = @($revision, $date)
                    result = $baseCall.Parsed
                })

                $tailResult = $null
                if ($Mode -eq 'cli-tails' -and $baseCall.Parsed.status -eq 'success') {
                    $tailUserPrompt = @"
User question:
$($case.questionRu)

Base CLI result:
$($baseCall.Parsed | ConvertTo-Json -Depth 50 -Compress)
"@
                    $tailResponse = Invoke-OllamaJson -SystemPrompt $tailPrompt -UserPrompt $tailUserPrompt -Stage 'tail-planner'
                    $modelResponses.Add($tailResponse)
                    $tailPlan = $tailResponse.Parsed

                    if ($tailPlan.openTail -eq $true) {
                        if ([string]::IsNullOrWhiteSpace([string] $tailPlan.entity) -or
                            $tailPlan.kind -notin @('evidence', 'exceptions')) {
                            throw 'Tail planner requested an invalid entity or kind.'
                        }

                        $tailCall = Invoke-PrologJson -CliArguments @(
                            'expand',
                            [string] $tailPlan.entity,
                            [string] $tailPlan.kind
                        )
                        $tailResult = $tailCall.Parsed
                        $cliCalls.Add([ordered]@{
                            operation = 'expand'
                            arguments = @([string] $tailPlan.entity, [string] $tailPlan.kind)
                            result = $tailCall.Parsed
                        })
                        $openedTails.Add([ordered]@{
                            entity = [string] $tailPlan.entity
                            kind = [string] $tailPlan.kind
                            status = [string] $tailCall.Parsed.status
                        })
                    }
                }

                $finalizerUserPrompt = @"
User question:
$($case.questionRu)

Base CLI result:
$($baseCall.Parsed | ConvertTo-Json -Depth 50 -Compress)

Optional tail result:
$(if ($null -eq $tailResult) { 'null' } else { $tailResult | ConvertTo-Json -Depth 50 -Compress })
"@
                $finalResponse = Invoke-OllamaJson -SystemPrompt $finalizePrompt -UserPrompt $finalizerUserPrompt -Stage 'finalize'
                $modelResponses.Add($finalResponse)
                $final = [ordered]@{
                    action = 'query'
                    status = $finalResponse.Parsed.status
                    material = $finalResponse.Parsed.material
                    askField = $null
                    answerRu = $finalResponse.Parsed.answerRu
                }
            }
            else {
                throw "Planner returned unsupported action '$($planner.action)'."
            }
        }
    }
    catch {
        $runnerErrorCount++
        $runnerError = $_.Exception.Message
        $final = [ordered]@{
            action = 'error'
            status = 'error'
            material = $null
            askField = $null
            answerRu = $runnerError
        }
    }
    finally {
        $caseStopwatch.Stop()
    }

    $usage = [ordered]@{
        promptEvalCount = (@($modelResponses | ForEach-Object { $_.PromptEvalCount }) | Measure-Object -Sum).Sum
        evalCount = (@($modelResponses | ForEach-Object { $_.EvalCount }) | Measure-Object -Sum).Sum
        modelElapsedMs = (@($modelResponses | ForEach-Object { $_.ElapsedMs }) | Measure-Object -Sum).Sum
    }

    $record = [ordered]@{
        schemaVersion = 1
        runId = $runId
        caseId = [string] $case.id
        questionRu = [string] $case.questionRu
        mode = $Mode
        model = $Model
        seed = $Seed
        temperature = $Temperature
        commit = $commit
        startedAt = $caseStarted.ToString('o')
        elapsedMs = $caseStopwatch.ElapsedMilliseconds
        promptHashes = $promptHashes
        representationHash = $representationHash
        planner = $planner
        tailPlan = $tailPlan
        cliCalls = @($cliCalls)
        openedTails = @($openedTails)
        final = $final
        usage = $usage
        rawModelResponses = @($modelResponses | ForEach-Object {
            [ordered]@{
                stage = $_.Stage
                raw = $_.Raw
                elapsedMs = $_.ElapsedMs
                promptEvalCount = $_.PromptEvalCount
                evalCount = $_.EvalCount
                totalDurationNs = $_.TotalDurationNs
            }
        })
        runnerError = $runnerError
    }

    Add-JsonLine -Value $record
    Write-Host "[$caseCount] $($case.id): $($final.status)"
}

Write-Host "Representation run written: $OutputPath"
Write-Host "Cases: $caseCount; runner errors: $runnerErrorCount"

if ($runnerErrorCount -gt 0) {
    throw "Representation run completed with $runnerErrorCount runner error(s). Results were preserved in $OutputPath."
}
