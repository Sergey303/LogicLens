[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$labRoot = Split-Path -Parent $PSScriptRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v0.jsonl'
$requiredFields = @(
    'id',
    'questionRu',
    'expectedAction',
    'expectedStatus',
    'requiresTail',
    'tailEntity'
)
$allowedActions = @('query', 'ask_user')
$allowedStatuses = @('success', 'unknown', 'need_user')
$allowedTails = @('evidence', 'exceptions')
$ids = [System.Collections.Generic.HashSet[string]]::new()
$count = 0
$lineNumber = 0

foreach ($line in Get-Content -LiteralPath $caseFile -Encoding utf8) {
    $lineNumber++
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    try {
        $record = $line | ConvertFrom-Json -Depth 20
    }
    catch {
        throw "Invalid JSON at $caseFile line ${lineNumber}: $($_.Exception.Message)"
    }

    foreach ($field in $requiredFields) {
        if (-not $record.PSObject.Properties[$field]) {
            throw "Missing field '$field' at $caseFile line $lineNumber."
        }
    }

    if ([string]::IsNullOrWhiteSpace($record.id)) {
        throw "Empty case id at $caseFile line $lineNumber."
    }

    if (-not $ids.Add([string] $record.id)) {
        throw "Duplicate case id '$($record.id)'."
    }

    if ($record.expectedAction -notin $allowedActions) {
        throw "Unsupported expectedAction '$($record.expectedAction)' in '$($record.id)'."
    }

    if ($record.expectedStatus -notin $allowedStatuses) {
        throw "Unsupported expectedStatus '$($record.expectedStatus)' in '$($record.id)'."
    }

    if ($null -ne $record.requiresTail -and $record.requiresTail -notin $allowedTails) {
        throw "Unsupported requiresTail '$($record.requiresTail)' in '$($record.id)'."
    }

    if ($null -eq $record.requiresTail -and $null -ne $record.tailEntity) {
        throw "Case '$($record.id)' has tailEntity but requiresTail is null."
    }

    if ($null -ne $record.requiresTail -and
        [string]::IsNullOrWhiteSpace([string] $record.tailEntity)) {
        throw "Case '$($record.id)' requires a tail but has no tailEntity."
    }

    if ($record.expectedAction -eq 'query') {
        if (-not $record.PSObject.Properties['query']) {
            throw "Query case '$($record.id)' has no query object."
        }

        if (-not $record.query.PSObject.Properties['operation']) {
            throw "Query case '$($record.id)' has no operation."
        }

        if (-not $record.query.PSObject.Properties['arguments']) {
            throw "Query case '$($record.id)' has no arguments."
        }
    }

    if ($record.expectedAction -eq 'ask_user' -and
        -not $record.PSObject.Properties['expectedField']) {
        throw "Clarification case '$($record.id)' has no expectedField."
    }

    if ($record.expectedStatus -eq 'success' -and
        -not $record.PSObject.Properties['expectedMaterial']) {
        throw "Successful case '$($record.id)' has no expectedMaterial."
    }

    $count++
}

if ($count -eq 0) {
    throw "No benchmark cases found in $caseFile."
}

Write-Host "Benchmark cases valid: $count"
