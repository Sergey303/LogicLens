[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    'runner/prompts/compiled-frame-renderer.md',
    'scripts/compiled_frame_core.py',
    'scripts/compiled_frame_eval.py',
    'scripts/run_compiled_frame.py',
    'scripts/validate_compiled_frame.py',
    'scripts/run-compiled-frame.ps1'
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

$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
python (Join-Path $labRoot 'scripts/validate_compiled_frame.py') `
    --lab-root $labRoot `
    --swipl $swipl
if ($LASTEXITCODE -ne 0) {
    throw 'Compiled decision frame oracle failed.'
}

Write-Host 'Compiled decision frame assets valid: parser and trusted Prolog frame passed 18/18.'
