[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$casePath = Join-Path $labRoot 'cases/teacher-loop-pilot-v0.jsonl'
$teacherSchemaPath = Join-Path $labRoot 'runner/teacher-candidate.schema.json'
$studentSchemaPath = Join-Path $labRoot 'runner/student-answer.schema.json'
$required = @(
    'research/TEACHER_STUDENT_EXPERIMENT.md',
    'runner/prompts/teacher-optimize.md',
    'runner/teacher-candidate.schema.json',
    'runner/student-answer.schema.json',
    'scripts/invoke_codex_json.py',
    'scripts/teacher_loop_eval.py',
    'scripts/teacher_loop_teacher.py',
    'scripts/teacher_loop_feedback.py',
    'scripts/teacher_loop_runtime.py',
    'scripts/teacher_loop_epoch.py',
    'scripts/teacher_loop_report.py',
    'scripts/run_teacher_loop.py',
    'scripts/test_teacher_loop_offline.py',
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
if ($cases.Count -ne 18) { throw "Teacher-loop pilot must contain 18 cases." }
if (@($cases.id | Sort-Object -Unique).Count -ne 18) {
    throw 'Teacher-loop pilot contains duplicate IDs.'
}
if (@($cases.questionRu | Sort-Object -Unique).Count -ne 18) {
    throw 'Teacher-loop pilot contains duplicate questions.'
}
foreach ($split in @('train', 'dev', 'holdout')) {
    if (@($cases | Where-Object split -eq $split).Count -ne 6) {
        throw "Teacher-loop split '$split' must contain 6 cases."
    }
}
foreach ($case in $cases) {
    if ($case.schemaVersion -ne 1) { throw "Bad schema in '$($case.id)'." }
    if ($case.expected.action -notin @('answer', 'ask_user')) {
        throw "Bad action in '$($case.id)'."
    }
    if ($case.expected.status -notin @('success', 'unknown', 'need_user')) {
        throw "Bad status in '$($case.id)'."
    }
    if ($case.expected.action -eq 'ask_user' -and
        $case.expected.askField -notin @('date', 'revision')) {
        throw "Bad askField in '$($case.id)'."
    }
}

$teacherRaw = Get-Content $teacherSchemaPath -Raw -Encoding utf8
if ($teacherRaw -match '"(minLength|maxLength|pattern|minimum|maximum)"') {
    throw 'Teacher schema uses a non-conservative keyword.'
}
$teacherSchema = $teacherRaw | ConvertFrom-Json -Depth 30
if ($teacherSchema.type -ne 'object' -or
    $teacherSchema.additionalProperties -ne $false) {
    throw 'Teacher candidate schema must be a closed object.'
}
$teacherRequired = @(
    'decision', 'changeType', 'hypothesis', 'studentPrompt',
    'prologKnowledge', 'expectedEffect', 'risk'
)
foreach ($name in $teacherRequired) {
    if ($name -notin @($teacherSchema.required)) {
        throw "Teacher schema does not require '$name'."
    }
}

$studentSchema = Get-Content $studentSchemaPath -Raw -Encoding utf8 |
    ConvertFrom-Json -Depth 30
if ($studentSchema.type -ne 'object' -or
    $studentSchema.additionalProperties -ne $false) {
    throw 'Student answer schema must be a closed object.'
}
foreach ($name in @('action', 'status', 'material', 'askField', 'answerRu')) {
    if ($name -notin @($studentSchema.required)) {
        throw "Student answer schema does not require '$name'."
    }
}
if ((@($studentSchema.properties.action.enum) -join ',') -ne 'answer,ask_user') {
    throw 'Student action enum changed.'
}
if ((@($studentSchema.properties.status.enum) -join ',') -ne
    'success,unknown,need_user') {
    throw 'Student status enum changed.'
}

$teacherTransport = Get-Content (Join-Path $labRoot 'scripts/teacher_loop_teacher.py') -Raw
if ($teacherTransport -notmatch 'encoding="utf-8"' -or
    $teacherTransport -notmatch 'errors="strict"') {
    throw 'Teacher subprocess must use strict UTF-8.'
}
$codexTransport = Get-Content (Join-Path $labRoot 'scripts/invoke_codex_json.py') -Raw
if ($codexTransport -notmatch 'sys\.stdin\.buffer\.read\(\)\.decode\("utf-8"' -or
    $codexTransport -notmatch 'encoding="utf-8"' -or
    $codexTransport -notmatch 'errors="strict"') {
    throw 'Codex adapter must use strict UTF-8.'
}

$pythonFiles = @($required | Where-Object { $_ -like 'scripts/*.py' })
$pythonCheck = @'
import ast, pathlib, sys
ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
'@
foreach ($relative in $pythonFiles) {
    $pythonCheck | python - (Join-Path $labRoot $relative)
    if ($LASTEXITCODE -ne 0) { throw "Python parse failed: $relative" }
}

$tokens = $null; $errors = $null
[void] [System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $labRoot 'scripts/run-teacher-loop.ps1'),
    [ref] $tokens,
    [ref] $errors
)
if (@($errors).Count -gt 0) { throw "PowerShell parse errors: $($errors.Message)" }

$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
python (Join-Path $labRoot 'scripts/test_teacher_loop_offline.py') `
    --lab-root $labRoot --swipl $swipl
if ($LASTEXITCODE -ne 0) { throw 'Teacher-loop offline regressions failed.' }

$hash = (Get-FileHash $casePath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host 'Teacher loop assets valid: 18 cases, case-level feedback, fixed schemas, strict UTF-8, offline regressions passed.'
Write-Host "Frozen pilot cases SHA256: $hash"
