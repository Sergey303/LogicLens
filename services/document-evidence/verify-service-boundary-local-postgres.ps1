[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$suffix = [Guid]::NewGuid().ToString("N").Substring(0, 8)
$containerName = "logiclens-document-evidence-proof-$suffix"
$previousConnection = $env:DOCUMENT_EVIDENCE_TEST_POSTGRES
$containerStarted = $false

function Invoke-Docker([string[]] $Arguments) {
    $output = & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed: docker $($Arguments -join ' ')"
    }
    return $output
}

try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker is required for the disposable PostgreSQL proof runner."
    }
    $null = Invoke-Docker @("info", "--format", "{{.ServerVersion}}")
    $null = Invoke-Docker @(
        "run",
        "--detach",
        "--name", $containerName,
        "--env", "POSTGRES_DB=document_evidence",
        "--env", "POSTGRES_USER=postgres",
        "--env", "POSTGRES_PASSWORD=postgres",
        "--publish", "127.0.0.1::5432",
        "postgres:17-alpine"
    )
    $containerStarted = $true

    $ready = $false
    foreach ($attempt in 1..60) {
        & docker exec $containerName pg_isready -U postgres -d document_evidence *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) {
        throw "Disposable PostgreSQL did not become ready."
    }

    $binding = (Invoke-Docker @("port", $containerName, "5432/tcp") | Select-Object -First 1)
    if ($binding -notmatch ':(?<port>\d+)$') {
        throw "Unable to resolve the disposable PostgreSQL host port: $binding"
    }
    $env:DOCUMENT_EVIDENCE_TEST_POSTGRES =
        "Host=127.0.0.1;Port=$($Matches.port);Database=document_evidence;" +
        "Username=postgres;Password=postgres"

    & (Join-Path $PSScriptRoot "verify-service-boundary.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Document Evidence service-boundary proof failed."
    }
    $global:LASTEXITCODE = 0
}
finally {
    $env:DOCUMENT_EVIDENCE_TEST_POSTGRES = $previousConnection
    if ($containerStarted) {
        & docker rm --force $containerName *> $null
    }
}
