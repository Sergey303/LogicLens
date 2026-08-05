[CmdletBinding()]
param(
    [string] $LogicLensRoot = "D:\projects\ChatPilotGroup\LogicLens",
    [string] $Codex = "codex",
    [string] $Swipl = "swipl",
    [ValidateRange(1, 20)]
    [int] $Repetitions = 1,
    [ValidateRange(1, 3600)]
    [int] $TimeoutSeconds = 300,
    [string] $Model
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Invoke-Native {
    param(
        [Parameter(Mandatory)]
        [string] $Name,

        [Parameter(Mandatory)]
        [scriptblock] $Command
    )

    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Name
    Write-Host "============================================================"

    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

$logicLens = (Resolve-Path $LogicLensRoot).Path
$d0Root = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\opinion-d0"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$tempRoot = Join-Path `
    $env:TEMP `
    "progressive-management-codex-d0-$runId"
$offline = Join-Path $tempRoot "offline-contract"
$output = Join-Path $tempRoot "experiment"

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

Invoke-Native "Check Codex CLI" {
    & $Codex --version
}

Invoke-Native "Check SWI-Prolog" {
    & $Swipl --version
}

Invoke-Native "Verify frozen DSL-D0 contracts" {
    py -3 (Join-Path $d0Root "verify_contract.py")
}

Invoke-Native "Verify offline DSL-D0 runner and scorer" {
    py -3 `
        (Join-Path $d0Root "run_codex_ablation.py") `
        --root $d0Root `
        --output-root $offline `
        --fake-provider `
        --skip-prolog `
        --repetitions 1
}

$arguments = @(
    (Join-Path $d0Root "run_codex_ablation.py"),
    "--root", $d0Root,
    "--output-root", $output,
    "--codex", $Codex,
    "--swipl", $Swipl,
    "--timeout-seconds", "$TimeoutSeconds",
    "--repetitions", "$Repetitions",
    "--conditions", "direct", "scalar", "raw", "verified"
)

if ($Model) {
    $arguments += @("--model", $Model)
}

Invoke-Native "Run Direct, Scalar, Raw and Verified DSL-D0 ablation" {
    py -3 @arguments
}

Copy-Item `
    -Path (Join-Path $d0Root "opinions-v0.jsonl") `
    -Destination (Join-Path $output "opinions-v0.jsonl") `
    -Force

Copy-Item `
    -Path (Join-Path $d0Root "cases-v0.jsonl") `
    -Destination (Join-Path $output "cases-v0.jsonl") `
    -Force

Copy-Item `
    -Path (Join-Path $d0Root "README.md") `
    -Destination (Join-Path $output "README.md") `
    -Force

$summary = Get-Content `
    (Join-Path $output "summary.json") `
    -Raw |
    ConvertFrom-Json

Write-Host ""
Write-Host "Experiment summary"
Write-Host "  Linear issue: ENG-185"
Write-Host "  Cases:       $($summary.caseCount)"
Write-Host "  Calls:       $($summary.callCount)"
Write-Host "  Model:       $($summary.modelSelection)"

foreach ($metric in $summary.metrics) {
    Write-Host ""
    Write-Host "  $($metric.condition)"
    Write-Host "    task conclusion accuracy:      $($metric.taskConclusionAccuracy)"
    Write-Host "    condition conclusion accuracy: $($metric.conditionConclusionAccuracy)"
    Write-Host "    number transport exact:        $($metric.numberTransportExactRate)"
    Write-Host "    semantic obligations:          $($metric.semanticObligationsRate)"
    Write-Host "    probability semantics safety:  $($metric.probabilitySemanticsSafetyRate)"
    Write-Host "    scalar overclaim rate:         $($metric.scalarOverclaimRate)"
    Write-Host "    latency mean ms:               $($metric.latencyMeanMs)"
}

$archive = "$output.zip"
if (Test-Path $archive) {
    Remove-Item $archive -Force
}

Compress-Archive `
    -Path "$output\*" `
    -DestinationPath $archive `
    -CompressionLevel Optimal `
    -Force

Write-Host ""
Write-Host "[CGR_ARTIFACT_TITLE] Progressive management DSL-D0 opinion ablation"
Write-Host "[CGR_ARTIFACT] $archive"

exit 0
