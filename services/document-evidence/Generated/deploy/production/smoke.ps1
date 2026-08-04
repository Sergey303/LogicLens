param(
  [string]$ComposePath = "deploy/production/docker-compose.production.yml",
  [string]$EnvPath = "deploy/production/.env.production",
  [string]$PublicBaseUrl = "http://127.0.0.1:8080",
  [switch]$SkipComposeConfig
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "../..")
$composeFullPath = if ([System.IO.Path]::IsPathRooted($ComposePath)) { $ComposePath } else { Join-Path $RepoRoot.Path $ComposePath }
$envFullPath = if ([System.IO.Path]::IsPathRooted($EnvPath)) { $EnvPath } else { Join-Path $RepoRoot.Path $EnvPath }

if (-not (Test-Path -LiteralPath $composeFullPath)) { throw "Production compose file was not found: $composeFullPath" }
if (-not (Test-Path -LiteralPath $envFullPath)) { throw "Production env file was not found: $envFullPath" }

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) { throw "Docker was not found. Production deploy smoke requires Docker Compose." }

& $docker.Source info *> $null
if ($LASTEXITCODE -ne 0) {
  throw "Docker daemon is not reachable. Start Docker Desktop and wait until the Linux engine is running before production deploy smoke."
}

function Invoke-DockerCompose {
  param([string[]]$Arguments)

  & $docker.Source compose --env-file $envFullPath -f $composeFullPath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "docker compose $($Arguments -join ' ') failed. Exit code: $LASTEXITCODE."
  }
}

function Invoke-HttpStatus {
  param(
    [string]$Uri,
    [int[]]$ExpectedStatusCodes
  )

  $response = Invoke-WebRequest -UseBasicParsing -SkipHttpErrorCheck -Uri $Uri
  if ($ExpectedStatusCodes -notcontains [int]$response.StatusCode) {
    throw "Unexpected HTTP status for ${Uri}: $($response.StatusCode). Expected: $($ExpectedStatusCodes -join ', ')."
  }
  Write-Host "OK $Uri -> $($response.StatusCode)"
}

if (-not $SkipComposeConfig) {
  Invoke-DockerCompose @("config", "--quiet")
}

Invoke-DockerCompose @("exec", "-T", "db", "sh", "-c", 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"')
Invoke-DockerCompose @("exec", "-T", "api", "curl", "-fsS", "http://127.0.0.1:8080/health/live")
Invoke-DockerCompose @("exec", "-T", "api", "curl", "-fsS", "http://127.0.0.1:8080/health/ready")
Invoke-DockerCompose @("exec", "-T", "api", "curl", "-fsS", "http://127.0.0.1:8080/metrics")

$base = $PublicBaseUrl.TrimEnd("/")
Invoke-HttpStatus -Uri "$base/" -ExpectedStatusCodes @(200)
Invoke-HttpStatus -Uri "$base/health/live" -ExpectedStatusCodes @(404)
Invoke-HttpStatus -Uri "$base/health/ready" -ExpectedStatusCodes @(404)
Invoke-HttpStatus -Uri "$base/metrics" -ExpectedStatusCodes @(404)

Write-Host "ALL OK: production deploy kit smoke checks passed."
