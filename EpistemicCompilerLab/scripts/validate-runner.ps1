[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$requiredFiles = @(
    'cases/benchmark-v1.jsonl',
    'cases/BENCHMARK_V1.md',
    'representations/knowledge.compact.json',
    'runner/prompts/direct.md',
    'runner/prompts/planner.md',
    'runner/prompts/tail-planner.md',
    'runner/prompts/finalize.md',
    'runner/prompts/planner-v1-raw.md',
    'runner/prompts/planner-v1-frame.md',
    'runner/planner-v1-output.schema.json',
    'scripts/validate-benchmark-v1.ps1',
    'scripts/ensure-ollama-cpu-profile.ps1',
    'scripts/test-ollama-model.ps1',
    'scripts/invoke_codex_json.py',
    'scripts/test-codex-cli.ps1',
    'scripts/run-planner-v1.ps1',
    'scripts/run-planner-v1-codex.ps1',
    'scripts/run-planner-v1-codex-pair.ps1',
    'scripts/score-planner-v1.ps1',
    'scripts/run-representation.ps1',
    'scripts/run-representation-baseline.ps1',
    'scripts/run-representation-suite.ps1',
    'scripts/score-representation.ps1',
    'scripts/show-representation-summary.ps1',
    'scripts/launch.ps1'
)

foreach ($relativePath in $requiredFiles) {
    $path = Join-Path $labRoot $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing representation-runner asset: $relativePath"
    }
    if ((Get-Item -LiteralPath $path).Length -eq 0) {
        throw "Empty representation-runner asset: $relativePath"
    }
}

function Read-Json([string] $RelativePath) {
    $path = Join-Path $labRoot $RelativePath
    try { return Get-Content -LiteralPath $path -Raw -Encoding utf8 | ConvertFrom-Json -Depth 80 }
    catch { throw "Invalid JSON in ${RelativePath}: $($_.Exception.Message)" }
}

$compact = Read-Json 'representations/knowledge.compact.json'
if ($compact.schemaVersion -ne 1) {
    throw "Unsupported compact knowledge schemaVersion '$($compact.schemaVersion)'."
}
if (@($compact.supportedRevisions).Count -eq 0) { throw 'Compact knowledge has no supported revisions.' }
if ($null -eq $compact.transitionDate) { throw 'Compact knowledge has no transition date.' }

$plannerSchema = Read-Json 'runner/planner-v1-output.schema.json'
if ($plannerSchema.type -ne 'object' -or $plannerSchema.additionalProperties -ne $false) {
    throw 'Planner v1 output schema must be a closed object.'
}
foreach ($name in @('action', 'plan', 'askField')) {
    if ($name -notin @($plannerSchema.required)) { throw "Planner schema does not require '$name'." }
}
$arguments = $plannerSchema.properties.plan.items.properties.arguments
foreach ($name in @('revision', 'date', 'entity', 'kind')) {
    if ($name -notin @($arguments.required)) { throw "Planner arguments do not require '$name'." }
    if ($null -eq $arguments.properties.$name.type) { throw "Planner argument '$name' has no explicit type." }
}

$parseTargets = @($requiredFiles | Where-Object { $_ -like 'scripts/*.ps1' })
$parseTargets += 'scripts/validate-runner.ps1'
foreach ($relativePath in $parseTargets) {
    $path = Join-Path $labRoot $relativePath
    $tokens = $null
    $errors = $null
    [void] [System.Management.Automation.Language.Parser]::ParseFile(
        $path, [ref] $tokens, [ref] $errors
    )
    if (@($errors).Count -gt 0) {
        $messages = @($errors | ForEach-Object {
            "line $($_.Extent.StartLineNumber): $($_.Message)"
        }) -join '; '
        throw "PowerShell parse errors in ${relativePath}: $messages"
    }
}

$pythonPath = Join-Path $labRoot 'scripts/invoke_codex_json.py'
$pythonSource = Get-Content -LiteralPath $pythonPath -Raw -Encoding utf8
if ($pythonSource.Contains('--ask-for-approval')) {
    throw 'Codex exec adapter contains the unsupported --ask-for-approval argument.'
}
$pythonCheck = @'
import ast, pathlib, sys
ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
'@
$pythonCheck | python - $pythonPath
if ($LASTEXITCODE -ne 0) {
    throw "Python parse failed for scripts/invoke_codex_json.py with code $LASTEXITCODE."
}

$smokePath = Join-Path $labRoot 'scripts/test-codex-cli.ps1'
$smokeSource = Get-Content -LiteralPath $smokePath -Raw -Encoding utf8
if (-not $smokeSource.Contains('"status": {"type": "string", "const": "ok"}')) {
    throw 'Codex smoke status schema must include an explicit string type.'
}
if (-not $smokeSource.Contains('"value": {"type": "integer", "const": 42}')) {
    throw 'Codex smoke value schema must include an explicit integer type.'
}

Write-Host "Runner assets valid: benchmark v1, Ollama, Codex CLI and planner pair scripts."
