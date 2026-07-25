[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$labRoot = Split-Path -Parent $PSScriptRoot
$caseFile = Join-Path $labRoot 'cases/benchmark-v0.jsonl'
$entryPoint = Join-Path $labRoot 'prolog/entry.pl'
$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$executed = 0
$clarifications = 0

function Invoke-PrologJson {
    param(
        [Parameter(Mandatory)]
        [string[]] $CliArguments
    )

    $raw = & $swipl -q -s $entryPoint -- @CliArguments 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "SWI-Prolog failed for '$($CliArguments -join ' ')': $raw"
    }

    try {
        $raw | ConvertFrom-Json -Depth 30
    }
    catch {
        throw "Invalid JSON from '$($CliArguments -join ' ')': $raw"
    }
}

foreach ($line in Get-Content -LiteralPath $caseFile -Encoding utf8) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $case = $line | ConvertFrom-Json -Depth 30
    if ($case.expectedAction -eq 'ask_user') {
        $clarifications++
        continue
    }

    if ($case.query.operation -ne 'current-material') {
        throw "Unsupported oracle operation '$($case.query.operation)' in '$($case.id)'."
    }

    $revision = [string] $case.query.arguments.revision
    $date = [string] $case.query.arguments.date
    $result = Invoke-PrologJson -CliArguments @(
        'current-material',
        $revision,
        $date
    )

    if ($result.status -ne $case.expectedStatus) {
        throw "Case '$($case.id)' expected status '$($case.expectedStatus)' but got '$($result.status)'."
    }

    if ($case.expectedStatus -eq 'success') {
        $solutions = @($result.solutions)
        if ($solutions.Count -ne 1) {
            throw "Case '$($case.id)' expected one solution but got $($solutions.Count)."
        }

        if ($solutions[0].material -ne $case.expectedMaterial) {
            throw "Case '$($case.id)' expected '$($case.expectedMaterial)' but got '$($solutions[0].material)'."
        }

        if ($null -ne $case.requiresTail) {
            $tailEntity = [string] $case.tailEntity
            $kinds = @($solutions[0].available_expansions | ForEach-Object { $_.kind })

            if ($tailEntity -eq $case.expectedMaterial -and
                $case.requiresTail -notin $kinds) {
                throw "Case '$($case.id)' requires unavailable tail '$($case.requiresTail)' on '$tailEntity'."
            }

            $tail = Invoke-PrologJson -CliArguments @(
                'expand',
                $tailEntity,
                $case.requiresTail
            )
            if ($tail.status -ne 'success') {
                throw "Case '$($case.id)' could not open tail '$($case.requiresTail)' on '$tailEntity'."
            }
        }
    }

    if ($case.expectedStatus -eq 'unknown' -and @($result.solutions).Count -gt 0) {
        throw "Case '$($case.id)' returned solutions with unknown status."
    }

    $executed++
}

Write-Host "Benchmark oracle passed: $executed query cases; $clarifications clarification cases"
