[CmdletBinding()]
param(
    [string] $LogicLensRoot = "D:\projects\ChatPilotGroup\LogicLens",
    [string] $CtoRoot = "D:\projects\ChatPilotGroup\CTO-Practical-Simulation",
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
$cto = (Resolve-Path $CtoRoot).Path
$worldRoot = Join-Path $cto "worlds\management"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$tempRoot = Join-Path $env:TEMP "progressive-management-codex-c0-$runId"
$dslCWorld = Join-Path $tempRoot "dsl-c-world"
$dslCPackage = Join-Path $tempRoot "dsl-c-package"
$output = Join-Path $tempRoot "experiment"
$preflightOutput = Join-Path $tempRoot "frame-preflight.json"

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

$contracts = Join-Path $logicLens "contracts"
$capsuleTool = Join-Path $logicLens "tools\capsule.py"
$overlayBuilder = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\build_dsl_c_overlay.py"
$observations = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\dsl-c-observations-v0.jsonl"
$cases = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\cases-dsl-c-v0.jsonl"
$frameVerifier = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\verify_progressive_management_dsl_c_frames.py"
$runner = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\run_codex_dsl_c_ablation.py"

Invoke-Native "Check Codex CLI" {
    & $Codex --version
}

Invoke-Native "Check SWI-Prolog" {
    & $Swipl --version
}

Invoke-Native "Verify numeric Codex structured-output schema" {
    py -3 `
        (Join-Path $logicLens "tests\numeric_codex_structured_output_schema_contract_test.py")
}

Invoke-Native "Verify typed observation DSL-C runtime" {
    py -3 `
        (Join-Path $logicLens "tests\capsule_query_dsl_c_contract_test.py")
}

Invoke-Native "Verify frozen management DSL-C tranche" {
    py -3 `
        (Join-Path $logicLens "tests\progressive_management_dsl_c_contract_test.py")
}

Invoke-Native "Verify offline management DSL-C Codex runner" {
    py -3 `
        (Join-Path $logicLens "tests\progressive_management_dsl_c_ablation_contract_test.py")
}

Invoke-Native "Validate source management world" {
    py -3 $capsuleTool `
        --contracts-root $contracts `
        validate `
        --world-root $worldRoot
}

Invoke-Native "Build temporary DSL-C overlay" {
    py -3 $overlayBuilder `
        --source-world $worldRoot `
        --output-world $dslCWorld `
        --observations $observations `
        --contracts-root $contracts
}

Invoke-Native "Ensure source management world is unchanged" {
    git -C $cto diff `
        --exit-code `
        -- worlds/management
}

Invoke-Native "Compile DSL-C capsule" {
    py -3 $capsuleTool `
        --contracts-root $contracts `
        compile `
        --world-root $dslCWorld `
        --capsule management.role-boundaries `
        --output $dslCPackage
}

Invoke-Native "Verify DSL-C capsule" {
    py -3 $capsuleTool `
        --contracts-root $contracts `
        verify `
        --package $dslCPackage
}

Invoke-Native "Verify frozen expectations against real DSL-C frames" {
    py -3 $frameVerifier `
        --logiclens-root $logicLens `
        --cases $cases `
        --dsl-c-package $dslCPackage `
        --swipl $Swipl `
        --output $preflightOutput
}

$arguments = @(
    $runner,
    "--logiclens-root", $logicLens,
    "--cases", $cases,
    "--dsl-c-package", $dslCPackage,
    "--output-root", $output,
    "--codex", $Codex,
    "--swipl", $Swipl,
    "--timeout-seconds", "$TimeoutSeconds",
    "--repetitions", "$Repetitions",
    "--conditions", "direct", "raw", "gold-c"
)

if ($Model) {
    $arguments += @("--model", $Model)
}

Invoke-Native "Run Direct, Raw and verified DSL-C Codex ablation" {
    py -3 @arguments
}

Copy-Item `
    -Path $preflightOutput `
    -Destination (Join-Path $output "frame-preflight.json") `
    -Force

Copy-Item `
    -Path (Join-Path $dslCWorld "dsl-c-overlay.json") `
    -Destination (Join-Path $output "dsl-c-overlay.json") `
    -Force

Copy-Item `
    -Path (Join-Path $dslCPackage "capsule-package.json") `
    -Destination (Join-Path $output "capsule-package.json") `
    -Force

Copy-Item `
    -Path (Join-Path $dslCPackage "capsule.lock.json") `
    -Destination (Join-Path $output "capsule.lock.json") `
    -Force

$archive = "$output.zip"
if (Test-Path $archive) {
    Remove-Item $archive -Force
}

Compress-Archive `
    -Path "$output\*" `
    -DestinationPath $archive `
    -CompressionLevel Optimal `
    -Force

$summary = Get-Content `
    (Join-Path $output "summary.json") `
    -Raw |
    ConvertFrom-Json

Write-Host ""
Write-Host "Experiment summary"
Write-Host "  Cases:         $($summary.caseCount)"
Write-Host "  Calls:         $($summary.callCount)"
Write-Host "  Model:         $($summary.modelSelection)"
Write-Host "  DSL-C package: $($summary.hashes.dslCPackage)"

foreach ($metric in $summary.metrics) {
    Write-Host ""
    Write-Host "  $($metric.condition)"
    Write-Host "    task status accuracy:          $($metric.taskStatusAccuracy)"
    Write-Host "    condition status accuracy:     $($metric.conditionStatusAccuracy)"
    Write-Host "    condition abstention accuracy: $($metric.conditionAbstentionAccuracy)"
    Write-Host "    observation structure exact:   $($metric.observationStructureExactRate)"
    Write-Host "    normalized values exact:       $($metric.normalizedValuesExactRate)"
    Write-Host "    interpretation flags exact:    $($metric.interpretationFlagsExactRate)"
    Write-Host "    warnings exact:                $($metric.warningsExactRate)"
    Write-Host "    probability-policy safety:     $($metric.probabilityPolicySafetyRate)"
    Write-Host "    latency mean ms:               $($metric.latencyMeanMs)"
}

Write-Host ""
Write-Host "[CGR_ARTIFACT_TITLE] Progressive management numeric DSL-C ablation"
Write-Host "[CGR_ARTIFACT] $archive"

exit 0
