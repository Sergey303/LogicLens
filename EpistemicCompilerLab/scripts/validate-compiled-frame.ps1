[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$schemaPath = Join-Path $labRoot 'runner/replication-cases.schema.json'
$required = @(
    'cases/compiled-frame-replication-v0.jsonl',
    'cases/compiled-frame-replication-v0.manifest.json',
    'runner/prompts/compiled-frame-renderer.md',
    'runner/prompts/generate-replication-cases.md',
    'runner/replication-cases.schema.json',
    'scripts/compiled_frame_core.py',
    'scripts/compiled_frame_eval.py',
    'scripts/run_compiled_frame.py',
    'scripts/run_compiled_frame_replication.py',
    'scripts/validate_compiled_frame.py',
    'scripts/validate_compiled_frame_replication.py',
    'scripts/replication_cases.py',
    'scripts/generate_replication_cases.py',
    'scripts/run-compiled-frame.ps1',
    'scripts/run-compiled-frame-replication.ps1',
    'scripts/run-generate-replication.ps1'
)

foreach ($relative in $required) {
    $path = Join-Path $labRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing compiled-frame asset: $relative"
    }
    if ((Get-Item -LiteralPath $path).Length -eq 0) {
        throw "Empty compiled-frame asset: $relative"
    }
}

$pythonCheck = @'
import ast, pathlib, sys
path = pathlib.Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
ast.parse(source)
if len(source.splitlines()) > 149:
    raise SystemExit(f"human-maintained file exceeds 149 lines: {path}")
'@
foreach ($relative in @($required | Where-Object { $_ -like '*.py' })) {
    $pythonCheck | python - (Join-Path $labRoot $relative)
    if ($LASTEXITCODE -ne 0) {
        throw "Compiled-frame Python validation failed: $relative"
    }
}

$schema = Get-Content $schemaPath -Raw -Encoding utf8 | ConvertFrom-Json -Depth 30
if ($schema.type -ne 'object' -or $schema.additionalProperties -ne $false) {
    throw 'Replication schema must be a closed object.'
}
if ('cases' -notin @($schema.required) -or
    $schema.properties.cases.items.additionalProperties -ne $false) {
    throw 'Replication case schema must require a closed cases array.'
}

$generator = Get-Content (Join-Path $labRoot 'scripts/generate_replication_cases.py') -Raw -Encoding utf8
foreach ($marker in @(
    'candidate.generated.json',
    'rejected_by_trusted_validator',
    'validation-error.json',
    '[CGR_ARTIFACT]'
)) {
    if ($generator -notmatch [regex]::Escape($marker)) {
        throw "Replication generator does not preserve rejected candidates: $marker"
    }
}
$validator = Get-Content (Join-Path $labRoot 'scripts/replication_cases.py') -Raw -Encoding utf8
if ($validator -notmatch 'expectedLiteral' -or $validator -notmatch 'foundDateLiterals') {
    throw 'Replication validator must report literal date mismatch details.'
}

$tokens = $null; $errors = $null
foreach ($relative in @($required | Where-Object { $_ -like '*.ps1' })) {
    [void] [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $labRoot $relative), [ref] $tokens, [ref] $errors
    )
    if (@($errors).Count -gt 0) { throw "PowerShell parse failed: $relative" }
}

$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
python (Join-Path $labRoot 'scripts/validate_compiled_frame.py') `
    --lab-root $labRoot --swipl $swipl
if ($LASTEXITCODE -ne 0) { throw 'Compiled decision frame oracle failed.' }
python (Join-Path $labRoot 'scripts/validate_compiled_frame_replication.py') `
    --lab-root $labRoot --swipl $swipl
if ($LASTEXITCODE -ne 0) { throw 'Frozen compiled-frame replication oracle failed.' }

Write-Host 'Compiled-frame assets valid: pilot 18/18 and frozen replication 24/24.'
