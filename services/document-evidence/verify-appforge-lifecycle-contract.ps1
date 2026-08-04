[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-Corpus([string]$Root, [string[]]$Extensions) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        throw "Generated contract root is missing: $Root"
    }

    $files = Get-ChildItem -LiteralPath $Root -Recurse -File |
        Where-Object {
            $Extensions -contains $_.Extension -and
            $_.FullName -notmatch "[\\/](bin|obj|node_modules|dist)[\\/]"
        }
    if (-not $files) {
        throw "No generated contract files found under: $Root"
    }
    return ($files | ForEach-Object {
        Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
    }) -join "`n"
}

function Assert-Fields(
    [string]$Corpus,
    [string[]]$Fields,
    [string]$Surface
) {
    foreach ($field in $Fields) {
        if ($Corpus -notmatch "(?i)$([regex]::Escape($field))") {
            throw "Generated $Surface does not contain lifecycle field '$field'."
        }
    }
}

$OutputRoot = (Resolve-Path $OutputRoot).Path
$requiredFields = @(
    "ManifestJson",
    "MaxAttempts",
    "AvailableAt",
    "LeaseToken",
    "LastError"
)
$backendRoot = Join-Path $OutputRoot "backend"
$contractRoot = Join-Path $OutputRoot "backend-contract"
$migrationsRoot = Join-Path $backendRoot "Migrations"
$migrationSql = Join-Path $migrationsRoot "AppForgeGeneratedMigrations.idempotent.sql"

if (-not (Test-Path -LiteralPath $migrationSql -PathType Leaf)) {
    throw "Generated idempotent migration SQL is missing: $migrationSql"
}

$contractCorpus = Get-Corpus $contractRoot @(".json")
$backendCorpus = Get-Corpus $backendRoot @(".cs")
$migrationCorpus = Get-Corpus $migrationsRoot @(".cs", ".sql")

Assert-Fields $contractCorpus $requiredFields "canonical backend contract"
Assert-Fields $backendCorpus $requiredFields "C# backend"
Assert-Fields $migrationCorpus $requiredFields "EF migration chain"

$result = [ordered]@{
    kind = "logiclens-appforge-lifecycle-contract-proof"
    fields = $requiredFields
    migrationSql = [IO.Path]::GetRelativePath($OutputRoot, $migrationSql).Replace("\", "/")
    migrationSqlSha256 = (Get-FileHash -Algorithm SHA256 -Path $migrationSql).Hash.ToLowerInvariant()
}
$result | ConvertTo-Json -Depth 4
