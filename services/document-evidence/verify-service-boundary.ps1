[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$acceptedBase = "669b54c2ca0758a97f9cc10b32ca637db2e891fb"
Set-Location $repo

$applicationProject =
    "services/document-evidence/tests/DocumentEvidence.Application.ContractTests/DocumentEvidence.Application.ContractTests.csproj"
$postgresProject =
    "services/document-evidence/tests/DocumentEvidence.Postgres.IntegrationTests/DocumentEvidence.Postgres.IntegrationTests.csproj"
$projects = @(
    $applicationProject,
    "services/document-evidence/tests/DocumentEvidence.Security.ContractTests/DocumentEvidence.Security.ContractTests.csproj",
    "services/document-evidence/src/DocumentEvidence.Api.Application/DocumentEvidence.Api.Application.csproj",
    "services/document-evidence/tests/DocumentEvidence.Client.ContractTests/DocumentEvidence.Client.ContractTests.csproj",
    "services/document-evidence/tests/DocumentEvidence.Api.ContractTests/DocumentEvidence.Api.ContractTests.csproj",
    $postgresProject
)

$runProjects = @(
    $applicationProject,
    "services/document-evidence/tests/DocumentEvidence.Security.ContractTests/DocumentEvidence.Security.ContractTests.csproj",
    "services/document-evidence/tests/DocumentEvidence.Client.ContractTests/DocumentEvidence.Client.ContractTests.csproj",
    "services/document-evidence/tests/DocumentEvidence.Api.ContractTests/DocumentEvidence.Api.ContractTests.csproj"
)

git cat-file -e "$acceptedBase^{commit}"
if ($LASTEXITCODE -ne 0) {
    throw "Accepted service-boundary base is unavailable: $acceptedBase"
}

python tools/quality/repository_guard.py --base $acceptedBase
if ($LASTEXITCODE -ne 0) {
    throw "Repository guard failed."
}

$generatorJson = python tools/document_evidence/generate_client.py --check
if ($LASTEXITCODE -ne 0) {
    throw "Generated client verification failed."
}
$generatorReceipt = $generatorJson | ConvertFrom-Json

foreach ($project in $projects) {
    dotnet build $project --nologo --warnaserror
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed: $project"
    }
}

foreach ($project in $runProjects) {
    dotnet run --project $project --no-build
    if ($LASTEXITCODE -ne 0) {
        throw "Contract run failed: $project"
    }
}

$postgresRuntime = "not-run-no-connection"
$executablesRun = $runProjects.Count
if (-not [string]::IsNullOrWhiteSpace($env:DOCUMENT_EVIDENCE_TEST_POSTGRES)) {
    dotnet run --project $postgresProject --no-build
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL integration contracts failed."
    }
    $postgresRuntime = "passed"
    $executablesRun++
}

$result = [ordered]@{
    status = "success"
    branch = (git branch --show-current).Trim()
    commit = (git rev-parse HEAD).Trim()
    acceptedBase = $acceptedBase
    openApi = $generatorReceipt.openApi
    openApiSha256 = $generatorReceipt.openApiSha256
    generatedOutputs = $generatorReceipt.outputs
    projectsBuilt = $projects.Count
    contractExecutablesRun = $executablesRun
    postgresRuntime = $postgresRuntime
}

$result | ConvertTo-Json -Depth 5
$global:LASTEXITCODE = 0
