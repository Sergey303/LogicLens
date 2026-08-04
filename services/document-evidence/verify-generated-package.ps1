[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $PSScriptRoot "Generated")
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-LastExitCode([string]$Operation) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Operation failed with exit code $LASTEXITCODE."
    }
}

function Assert-File([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label is missing: $Path"
    }
}

$OutputRoot = (Resolve-Path $OutputRoot).Path
$manifestPath = Join-Path $OutputRoot "manifest\package-manifest.json"
$receiptPath = Join-Path $OutputRoot "manifest\logiclens-generation-receipt.json"
$migrationSql = Join-Path $OutputRoot "backend\Migrations\AppForgeGeneratedMigrations.idempotent.sql"
$contractVerifier = Join-Path $PSScriptRoot "verify-appforge-lifecycle-contract.ps1"

Assert-File $manifestPath "Package manifest"
Assert-File $receiptPath "LogicLens receipt"
Assert-File $migrationSql "Idempotent migration SQL"
Assert-File $contractVerifier "Lifecycle contract verifier"

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$receipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json

& $contractVerifier -OutputRoot $OutputRoot
Assert-LastExitCode "Lifecycle contract verification"

$projects = @(
    Get-ChildItem -LiteralPath (Join-Path $OutputRoot "backend") -Filter "*.csproj" -File
)
if ($projects.Count -ne 1) {
    throw "Expected exactly one generated backend project, found $($projects.Count)."
}

dotnet build $projects[0].FullName --nologo --no-restore -warnaserror
Assert-LastExitCode "Generated backend warnings-as-errors build"

$result = [ordered]@{
    kind = "logiclens-generated-package-proof"
    modelId = $manifest.generatedIdentity.modelId
    projectFileName = $manifest.generatedIdentity.projectFileName
    appForgeCommit = $receipt.appForgeCommit
    sourceSpecSha256 = $receipt.sourceSpecSha256
    lifecycleFields = @($receipt.lifecycleFields)
    migrationSqlSha256 = (Get-FileHash -Algorithm SHA256 -Path $migrationSql).Hash.ToLowerInvariant()
    packageManifestSha256 = (Get-FileHash -Algorithm SHA256 -Path $manifestPath).Hash.ToLowerInvariant()
    generatedTreeSha256BeforeReceipt = $receipt.generatedTreeSha256BeforeReceipt
    buildWarningsAsErrors = "passed"
}
$result | ConvertTo-Json -Depth 5
