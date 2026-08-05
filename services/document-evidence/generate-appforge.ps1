[CmdletBinding()]
param(
    [string]$AppForgeRoot = "D:\projects\ChatPilotGroup\AppForge",
    [string]$PreviousPackageRoot = "",
    [switch]$AllowDirtyAppForge
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-LastExitCode([string]$Operation) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Operation failed with exit code $LASTEXITCODE."
    }
}

function Get-StableTreeHash([string]$Root) {
    $records = Get-ChildItem -Path $Root -Recurse -File |
        Where-Object { $_.Name -ne "logiclens-generation-receipt.json" } |
        Sort-Object FullName |
        ForEach-Object {
            $relative = [IO.Path]::GetRelativePath($Root, $_.FullName).Replace("\", "/")
            $hash = (Get-FileHash -Algorithm SHA256 -Path $_.FullName).Hash.ToLowerInvariant()
            "$relative`t$hash"
        }

    $bytes = [Text.Encoding]::UTF8.GetBytes(($records -join "`n") + "`n")
    $stream = [IO.MemoryStream]::new($bytes)
    try {
        return (Get-FileHash -Algorithm SHA256 -InputStream $stream).Hash.ToLowerInvariant()
    }
    finally {
        $stream.Dispose()
    }
}

function Assert-File([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label is missing: $Path"
    }
}

$AppForgeRoot = (Resolve-Path $AppForgeRoot).Path
$spec = (Resolve-Path (Join-Path $PSScriptRoot "spec\document-evidence.md")).Path
$output = Join-Path $PSScriptRoot "Generated"
$runner = Join-Path $AppForgeRoot "scripts\quality\run-md-ef-core-production-package.ps1"
$contractVerifier = Join-Path $PSScriptRoot "verify-appforge-lifecycle-contract.ps1"
$existingManifest = Join-Path $output "manifest\package-manifest.json"

Assert-File $runner "AppForge production package runner"
Assert-File $contractVerifier "LogicLens lifecycle contract verifier"

$dirty = & git -C $AppForgeRoot status --porcelain
Assert-LastExitCode "Reading AppForge status"
if ($dirty -and -not $AllowDirtyAppForge) {
    throw "AppForge checkout is dirty. Commit/stash changes or pass -AllowDirtyAppForge."
}

$appForgeCommit = (& git -C $AppForgeRoot rev-parse HEAD).Trim()
Assert-LastExitCode "Reading AppForge commit"

if ((Test-Path -LiteralPath $output -PathType Container) -and
    -not (Test-Path -LiteralPath $existingManifest -PathType Leaf)) {
    Write-Host "Removing incomplete generated package: $output"
    Remove-Item -LiteralPath $output -Recurse -Force
}

$arguments = @{
    SpecPath = $spec
    OutputRoot = $output
    Clean = $true
}
if ($PreviousPackageRoot) {
    $arguments.PreviousPackageRoot = (Resolve-Path $PreviousPackageRoot).Path
}

& $runner @arguments
Assert-LastExitCode "AppForge production package generation"

$manifestPath = Join-Path $output "manifest\package-manifest.json"
Assert-File $manifestPath "Production package manifest"
$manifest = Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json

if ($manifest.kind -ne "appforge-generated-admin-production-package") {
    throw "Unexpected package kind: $($manifest.kind)"
}
if ($manifest.runtimeProfile -ne "production") {
    throw "Unexpected runtime profile: $($manifest.runtimeProfile)"
}

$identity = $manifest.generatedIdentity
$projectPath = Join-Path $output "backend\$($identity.projectFileName)"
$requiredFiles = @(
    $projectPath,
    (Join-Path $output "backend-contract\meta\domains.json"),
    (Join-Path $output "frontend\runtime\httpClient.ts"),
    (Join-Path $output "frontend-app\dist\index.html"),
    (Join-Path $output "deploy\production\docker-compose.production.yml")
)
foreach ($path in $requiredFiles) {
    Assert-File $path "Generated production artifact"
}

$lifecycleProofJson = (& $contractVerifier -OutputRoot $output | Out-String).Trim()
$lifecycleProof = $lifecycleProofJson | ConvertFrom-Json

$receipt = [ordered]@{
    kind = "logiclens-appforge-generation-receipt"
    version = 2
    appForgeCommit = $appForgeCommit
    modelId = $identity.modelId
    projectFileName = $identity.projectFileName
    sourceSpecSha256 = (Get-FileHash -Algorithm SHA256 -Path $spec).Hash.ToLowerInvariant()
    packageManifestSha256 = (Get-FileHash -Algorithm SHA256 -Path $manifestPath).Hash.ToLowerInvariant()
    generatedTreeSha256BeforeReceipt = Get-StableTreeHash $output
    lifecycleFields = @($lifecycleProof.fields)
    migrationSqlSha256 = $lifecycleProof.migrationSqlSha256
}
$receiptPath = Join-Path $output "manifest\logiclens-generation-receipt.json"
$receiptJson = ($receipt | ConvertTo-Json -Depth 5) + "`n"
[IO.File]::WriteAllText($receiptPath, $receiptJson, [Text.UTF8Encoding]::new($false))

Write-Host "Document Evidence AppForge production package passed."
Write-Host "AppForge commit: $appForgeCommit"
Write-Host "Model: $($identity.modelId)"
Write-Host "Backend project: $($identity.projectFileName)"
Write-Host "Lifecycle fields: $($receipt.lifecycleFields -join ', ')"
Write-Host "Output: $output"
Write-Host "Generated tree hash: $($receipt.generatedTreeSha256BeforeReceipt)"
