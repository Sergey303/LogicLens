[CmdletBinding()]
param(
    [string] $PopplerBin = $env:POPPLER_BIN
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $repo
$acceptedBase = "c9d8a3e0329cac4244bc1383bdfa200038096450"
$project = "services/document-evidence/tests/DocumentEvidence.EndToEndDemo/DocumentEvidence.EndToEndDemo.csproj"
$artifactRoot = Join-Path $repo ".artifacts/document-evidence/eng-148"
$pythonFiles = @(
    "tests/document_evidence_e2e_gate.py",
    "tests/document_evidence_e2e_gate_runtime.py",
    "tests/document_evidence_e2e_workspace.py",
    "tests/document_evidence_e2e_negative.py"
)

function Test-PopplerDirectory([string] $candidate) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { return $false }
    return (Test-Path (Join-Path $candidate "pdfinfo.exe")) -and
        (Test-Path (Join-Path $candidate "pdftotext.exe"))
}

function Resolve-PopplerDirectory([string] $hint) {
    if (Test-PopplerDirectory $hint) {
        return (Resolve-Path $hint).Path
    }
    if ((Get-Command pdfinfo -ErrorAction SilentlyContinue) -and
        (Get-Command pdftotext -ErrorAction SilentlyContinue)) {
        return $null
    }
    $roots = @(
        (Join-Path $env:LOCALAPPDATA "Microsoft/WinGet/Packages"),
        (Join-Path $env:USERPROFILE "scoop/apps/poppler"),
        (Join-Path ($env:ChocolateyInstall ?? "C:/ProgramData/chocolatey") "lib/poppler"),
        "C:/Program Files/poppler"
    )
    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        $match = Get-ChildItem $root -Filter "pdfinfo.exe" -File -Recurse `
            -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.DirectoryName "pdftotext.exe") } |
            Select-Object -First 1
        if ($null -ne $match) { return $match.DirectoryName }
    }
    throw @"
Poppler commands pdfinfo/pdftotext were not found.
Run .\services\document-evidence\install-eng-148-poppler.ps1 and repeat this verifier,
or pass -PopplerBin <directory containing pdfinfo.exe and pdftotext.exe>.
"@
}

$resolvedPoppler = Resolve-PopplerDirectory $PopplerBin
if ($null -ne $resolvedPoppler) {
    $env:PATH = "$resolvedPoppler;$env:PATH"
    Write-Host "Using Poppler from: $resolvedPoppler"
}
foreach ($command in @("python", "dotnet", "pdfinfo", "pdftotext", "swipl")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required ENG-148 command is not available on PATH: $command"
    }
}

python tools/quality/repository_guard.py --base $acceptedBase
if ($LASTEXITCODE -ne 0) { throw "Repository guard failed." }
python -m ruff check @pythonFiles
if ($LASTEXITCODE -ne 0) { throw "ENG-148 Python lint failed." }
python -m ruff format --diff --check @pythonFiles
if ($LASTEXITCODE -ne 0) { throw "ENG-148 Python format check failed." }

dotnet build $project --nologo --warnaserror
if ($LASTEXITCODE -ne 0) { throw "ENG-148 demo build failed." }
Remove-Item $artifactRoot -Recurse -Force -ErrorAction SilentlyContinue

foreach ($run in 1..2) {
    $runRoot = Join-Path $artifactRoot "run-$run"
    $serviceRoot = Join-Path $runRoot "service"
    $gateRoot = Join-Path $runRoot "gate"
    dotnet run --project $project --no-build -- $serviceRoot
    if ($LASTEXITCODE -ne 0) { throw "ENG-148 service run $run failed." }
    python tests/document_evidence_e2e_gate.py `
        --fragment (Join-Path $serviceRoot "selected-fragment.jsonl") `
        --service-receipt (Join-Path $serviceRoot "service-receipt.json") `
        --output $gateRoot
    if ($LASTEXITCODE -ne 0) { throw "ENG-148 SWI gate run $run failed." }
}

python tests/document_evidence_e2e_negative.py
if ($LASTEXITCODE -ne 0) { throw "ENG-148 fail-closed grounding contracts failed." }

function Get-TreeDigest([string] $root) {
    $lines = Get-ChildItem $root -File -Recurse |
        Sort-Object FullName |
        ForEach-Object {
            $relative = [IO.Path]::GetRelativePath($root, $_.FullName).Replace("\", "/")
            $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            "$relative`t$hash"
        }
    $content = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n") + "`n")
    $hashBytes = [Security.Cryptography.SHA256]::HashData($content)
    return [Convert]::ToHexString($hashBytes).ToLowerInvariant()
}

$first = Get-TreeDigest (Join-Path $artifactRoot "run-1")
$second = Get-TreeDigest (Join-Path $artifactRoot "run-2")
if ($first -ne $second) {
    throw "ENG-148 rerun is not byte-identical: $first != $second"
}
$decisionPath = Join-Path $artifactRoot "run-1/gate/decision-receipt.json"
$decision = Get-Content $decisionPath -Raw | ConvertFrom-Json
if ($decision.gateStatus -ne "passed" -or $decision.decisionFrame.status -ne "verified") {
    throw "ENG-148 decision receipt is not verified."
}

$result = [ordered]@{
    status = "success"
    branch = (git branch --show-current).Trim()
    commit = (git rev-parse HEAD).Trim()
    acceptedBase = $acceptedBase
    deterministicTreeSha256 = "sha256:$first"
    gateStatus = $decision.gateStatus
    decisionStatus = $decision.decisionFrame.status
    selectedFragmentId = $decision.selectedFragmentId
    unknownEvidence = "rejected"
    conflictingEvidence = "rejected"
    consumerReadsDatabase = $decision.consumerReadsDatabase
    consumerReadsBlobPath = $decision.consumerReadsBlobPath
}
$resultPath = Join-Path $artifactRoot "eng-148-proof.json"
$result | ConvertTo-Json -Depth 5 | Set-Content $resultPath -Encoding utf8
$result | ConvertTo-Json -Depth 5
$global:LASTEXITCODE = 0
