[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$casePath = Join-Path $labRoot 'cases/teacher-loop-pilot-v0.jsonl'
$schemaPath = Join-Path $labRoot 'runner/teacher-candidate.schema.json'
$required = @(
    'research/TEACHER_STUDENT_EXPERIMENT.md',
    'runner/prompts/teacher-optimize.md',
    'scripts/teacher_loop_eval.py',
    'scripts/teacher_loop_teacher.py',
    'scripts/run_teacher_loop.py',
    'scripts/run-teacher-loop.ps1'
)

foreach ($relative in $required) {
    $path = Join-Path $labRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing teacher-loop asset: $relative"
    }
    if ((Get-Item -LiteralPath $path).Length -eq 0) {
        throw "Empty teacher-loop asset: $relative"
    }
}

$cases = @(
    Get-Content -LiteralPath $casePath -Encoding utf8 |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        ForEach-Object { $_ | ConvertFrom-Json -Depth 30 }
)
if ($cases.Count -ne 18) {
    throw "Teacher-loop pilot must contain 18 cases, found $($cases.Count)."
}
if (@($cases.id | Sort-Object -Unique).Count -ne $cases.Count) {
    throw 'Teacher-loop pilot contains duplicate IDs.'
}
if (@($cases.questionRu | Sort-Object -Unique).Count -ne $cases.Count) {
    throw 'Teacher-loop pilot contains duplicate questions.'
}
foreach ($split in @('train', 'dev', 'holdout')) {
    $count = @($cases | Where-Object split -eq $split).Count
    if ($count -ne 6) {
        throw "Teacher-loop split '$split' must contain 6 cases, found $count."
    }
}
foreach ($case in $cases) {
    if ($case.schemaVersion -ne 1) {
        throw "Unsupported teacher-loop schema in '$($case.id)'."
    }
    if ($case.expected.action -notin @('answer', 'ask_user')) {
        throw "Invalid expected action in '$($case.id)'."
    }
    if ($case.expected.status -notin @('success', 'unknown', 'need_user')) {
        throw "Invalid expected status in '$($case.id)'."
    }
    if ($case.expected.action -eq 'ask_user' -and $case.expected.askField -notin @('date', 'revision')) {
        throw "Clarification case '$($case.id)' has invalid askField."
    }
}

$schema = Get-Content -LiteralPath $schemaPath -Raw -Encoding utf8 |
    ConvertFrom-Json -Depth 30
if ($schema.type -ne 'object' -or $schema.additionalProperties -ne $false) {
    throw 'Teacher candidate schema must be a closed object.'
}
$requiredNames = @('decision', 'changeType', 'hypothesis', 'studentPrompt', 'prologKnowledge', 'expectedEffect', 'risk')
foreach ($name in $requiredNames) {
    if ($name -notin @($schema.required)) {
        throw "Teacher candidate schema does not require '$name'."
    }
}

$pythonFiles = @(
    'scripts/teacher_loop_eval.py',
    'scripts/teacher_loop_teacher.py',
    'scripts/run_teacher_loop.py'
)
foreach ($relative in $pythonFiles) {
    $path = Join-Path $labRoot $relative
    python -m py_compile $path
    if ($LASTEXITCODE -ne 0) {
        throw "Python compilation failed for $relative with code $LASTEXITCODE."
    }
}

$tokens = $null
$errors = $null
[void] [System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $labRoot 'scripts/run-teacher-loop.ps1'),
    [ref] $tokens,
    [ref] $errors
)
if (@($errors).Count -gt 0) {
    throw "PowerShell parse errors in run-teacher-loop.ps1: $(@($errors.Message) -join '; ')"
}

$holdoutHash = (Get-FileHash -LiteralPath $casePath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "Teacher loop assets valid: 18 cases (6/6/6), closed schema, Python and PowerShell parse."
Write-Host "Frozen pilot cases SHA256: $holdoutHash"
