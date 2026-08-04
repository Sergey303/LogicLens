[CmdletBinding()]
param(
    [string]$AppForgeRoot = "D:\projects\ChatPilotGroup\AppForge",
    [switch]$AllowDirtyAppForge,
    [switch]$SkipBuild
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
        Sort-Object FullName |
        ForEach-Object {
            $relative = [IO.Path]::GetRelativePath($Root, $_.FullName).Replace("\", "/")
            $hash = (Get-FileHash -Algorithm SHA256 -Path $_.FullName).Hash.ToLowerInvariant()
            "$relative`t$hash"
        }

    $payload = [Text.Encoding]::UTF8.GetBytes(($records -join "`n") + "`n")
    $stream = [IO.MemoryStream]::new($payload)
    try {
        return (Get-FileHash -Algorithm SHA256 -InputStream $stream).Hash.ToLowerInvariant()
    }
    finally {
        $stream.Dispose()
    }
}

$AppForgeRoot = (Resolve-Path $AppForgeRoot).Path
$spec = (Resolve-Path (Join-Path $PSScriptRoot "spec\document-evidence.md")).Path
$output = Join-Path $PSScriptRoot "Generated"
$cli = Join-Path $AppForgeRoot "src\experimental\md_ef_core\cli.py"

if (-not (Test-Path $cli -PathType Leaf)) {
    throw "AppForge MD EF CLI was not found: $cli"
}

$dirty = & git -C $AppForgeRoot status --porcelain
Assert-LastExitCode "Reading AppForge status"
if ($dirty -and -not $AllowDirtyAppForge) {
    throw "AppForge checkout is dirty. Commit/stash changes or pass -AllowDirtyAppForge."
}

$appForgeCommit = (& git -C $AppForgeRoot rev-parse HEAD).Trim()
Assert-LastExitCode "Reading AppForge commit"

& python $cli `
    --repo-root $AppForgeRoot `
    --spec $spec `
    --output $output `
    --runtime-profile production `
    --database-provider Postgres `
    --clean
Assert-LastExitCode "AppForge generation"

$manifestPath = Join-Path $output "appforge-generation-manifest.json"
if (-not (Test-Path $manifestPath -PathType Leaf)) {
    throw "Generated manifest is missing: $manifestPath"
}

$manifest = Get-Content -Raw -Encoding UTF8 $manifestPath | ConvertFrom-Json
if ($manifest.runtimeProfile -ne "production") {
    throw "Unexpected runtime profile: $($manifest.runtimeProfile)"
}
if ($manifest.databaseProvider -ne "PostgreSQL") {
    throw "Unexpected database provider: $($manifest.databaseProvider)"
}

$receipt = [ordered]@{
    kind = "logiclens-appforge-generation-receipt"
    version = 1
    appForgeCommit = $appForgeCommit
    sourceSpecSha256 = (Get-FileHash -Algorithm SHA256 -Path $spec).Hash.ToLowerInvariant()
    appForgeManifestSha256 = (Get-FileHash -Algorithm SHA256 -Path $manifestPath).Hash.ToLowerInvariant()
    generatedTreeSha256BeforeReceipt = Get-StableTreeHash $output
}
$receiptJson = ($receipt | ConvertTo-Json -Depth 4) + "`n"
$utf8NoBom = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText(
    (Join-Path $output "logiclens-generation-receipt.json"),
    $receiptJson,
    $utf8NoBom
)

if (-not $SkipBuild) {
    & dotnet build (Join-Path $output "GeneratedClinic.slnx") --nologo
    Assert-LastExitCode "Generated solution build"
}

Write-Host "Document Evidence AppForge generation passed."
Write-Host "AppForge commit: $appForgeCommit"
Write-Host "Spec: $spec"
Write-Host "Output: $output"
Write-Host "Generated tree hash: $($receipt.generatedTreeSha256BeforeReceipt)"