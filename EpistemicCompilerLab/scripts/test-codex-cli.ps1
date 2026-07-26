[CmdletBinding()]
param(
    [string] $Model,
    [int] $TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
$labRoot = Split-Path -Parent $PSScriptRoot
$adapter = Join-Path $PSScriptRoot 'invoke_codex_json.py'
$temporary = Join-Path ([IO.Path]::GetTempPath()) (
    'epistemic-codex-' + [Guid]::NewGuid().ToString('N')
)
New-Item -ItemType Directory -Path $temporary -Force | Out-Null
$passed = $false

try {
    $codexVersion = (& codex --version 2>&1 | Select-Object -First 1).ToString().Trim()
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not read Codex CLI version.'
    }

    $schemaPath = Join-Path $temporary 'schema.json'
    $outputPath = Join-Path $temporary 'response.json'
    $eventsPath = Join-Path $temporary 'events.jsonl'
    @'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": ["status", "value"],
  "properties": {
    "status": {"const": "ok"},
    "value": {"const": 42}
  }
}
'@ | Set-Content -LiteralPath $schemaPath -Encoding utf8

    $prompt = @'
Return exactly one JSON object with status "ok" and value 42.
Do not inspect files, run commands, call tools or include Markdown.
'@
    $adapterArguments = @(
        $adapter,
        '--working-directory', $labRoot,
        '--schema', $schemaPath,
        '--output', $outputPath,
        '--events', $eventsPath,
        '--timeout-seconds', $TimeoutSeconds
    )
    if (-not [string]::IsNullOrWhiteSpace($Model)) {
        $adapterArguments += @('--model', $Model)
    }
    $prompt | python @adapterArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Codex adapter failed with code $LASTEXITCODE. Diagnostics: $temporary"
    }

    $response = Get-Content -LiteralPath $outputPath -Raw -Encoding utf8 |
        ConvertFrom-Json -Depth 20
    if ($response.status -ne 'ok' -or [int] $response.value -ne 42) {
        throw "Codex returned an unexpected response: $($response | ConvertTo-Json -Compress)"
    }

    $eventCount = @(
        Get-Content -LiteralPath $eventsPath -Encoding utf8 |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    ).Count
    $selection = if ([string]::IsNullOrWhiteSpace($Model)) {
        'account default'
    }
    else {
        $Model
    }
    Write-Host "Codex CLI smoke passed: $selection"
    Write-Host "CLI version: $codexVersion"
    Write-Host 'Execution verified: ephemeral, non-interactive, read-only, no tool events'
    Write-Host "Audit events: $eventCount"
    $passed = $true
}
finally {
    if ($passed) {
        Remove-Item -LiteralPath $temporary -Recurse -Force -ErrorAction SilentlyContinue
    }
    else {
        Write-Warning "Codex smoke diagnostics preserved: $temporary"
    }
}
