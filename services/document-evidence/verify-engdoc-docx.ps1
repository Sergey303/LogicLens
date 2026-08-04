[CmdletBinding()]
param(
    [string]$EngDocRoot = 'D:\projects\ChatPilotGroup\EngDocSentinel',
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedSha256 = 'bbd051dce7fd1e351175677c2c4c5bb8f14e2ba96c5a0f63298dd3a2f318023c'
$relativeSource = 'datasets\synthetic\demo-v0\generated\confirmed-power-conflict\01-technical-specification.docx'
$sourcePath = Join-Path $EngDocRoot $relativeSource
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$projectPath = Join-Path $repositoryRoot 'services\document-evidence\tests\DocumentEvidence.Ooxml.ContractTests\DocumentEvidence.Ooxml.ContractTests.csproj'

if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Committed EngDoc DOCX fixture was not found: $sourcePath"
}

$actualSha256 = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualSha256 -ne $expectedSha256) {
    throw "EngDoc DOCX SHA-256 mismatch. Expected $expectedSha256; actual $actualSha256."
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $repositoryRoot '.artifacts\document-evidence\engdoc-docx-local-proof-v0.json'
}
$outputDirectory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$lines = @(
    & dotnet run `
        --project $projectPath `
        --configuration Release `
        -- `
        --engdoc-docx $sourcePath 2>&1
)
$exitCode = $LASTEXITCODE
$lines | ForEach-Object { Write-Host $_ }
if ($exitCode -ne 0) {
    throw "EngDoc DOCX gate failed with exit code $exitCode."
}

$proof = $null
foreach ($line in $lines) {
    $text = [string]$line
    if ($text.TrimStart().StartsWith('{', [StringComparison]::Ordinal)) {
        try {
            $proof = $text | ConvertFrom-Json -Depth 32
        }
        catch {
            continue
        }
    }
}
if ($null -eq $proof -or $proof.status -ne 'passed') {
    throw 'EngDoc DOCX gate did not emit a valid proof record.'
}

$record = [ordered]@{
    schemaVersion = '0.1'
    linearIssue = 'ENG-145'
    sourceRepository = 'Sergey303/EngDocSentinel'
    sourceCommit = '916b19bf9a3047c1cb0e2bed9a1dab7bb084608a'
    sourceRelativePath = $relativeSource.Replace('\', '/')
    expectedArtifactSha256 = $expectedSha256
    verifiedAtUtc = [DateTimeOffset]::UtcNow.ToString('O')
    adapterProof = $proof
}
$record | ConvertTo-Json -Depth 32 | Set-Content -LiteralPath $OutputPath -Encoding utf8NoBOM
Write-Host "EngDoc DOCX proof written to: $OutputPath"
