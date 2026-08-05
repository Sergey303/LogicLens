[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $repo

$projects = @(
    "services/document-evidence/tests/DocumentEvidence.Security.ContractTests/DocumentEvidence.Security.ContractTests.csproj",
    "services/document-evidence/src/DocumentEvidence.Api.Application/DocumentEvidence.Api.Application.csproj",
    "services/document-evidence/tests/DocumentEvidence.Client.ContractTests/DocumentEvidence.Client.ContractTests.csproj",
    "services/document-evidence/tests/DocumentEvidence.Api.ContractTests/DocumentEvidence.Api.ContractTests.csproj"
)

$runProjects = @(
    "services/document-evidence/tests/DocumentEvidence.Security.ContractTests/DocumentEvidence.Security.ContractTests.csproj",
    "services/document-evidence/tests/DocumentEvidence.Client.ContractTests/DocumentEvidence.Client.ContractTests.csproj",
    "services/document-evidence/tests/DocumentEvidence.Api.ContractTests/DocumentEvidence.Api.ContractTests.csproj"
)

$base = (git rev-parse HEAD^).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Unable to resolve the comparison base."
}

python tools/quality/repository_guard.py --base $base
if ($LASTEXITCODE -ne 0) {
    throw "Repository guard failed."
}

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

$result = [ordered]@{
    status = "success"
    branch = (git branch --show-current).Trim()
    commit = (git rev-parse HEAD).Trim()
    openApi = "services/document-evidence/openapi/document-evidence-v1.json"
    projectsBuilt = $projects.Count
    contractExecutablesRun = $runProjects.Count
}

$result | ConvertTo-Json -Depth 3
