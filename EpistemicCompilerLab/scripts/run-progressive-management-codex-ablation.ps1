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
$tempRoot = Join-Path $env:TEMP "progressive-management-codex-$runId"
$dslA = Join-Path $tempRoot "dsl-a-package"
$dslB = Join-Path $tempRoot "dsl-b-package"
$dslBWorld = Join-Path $tempRoot "dsl-b-world"
$output = Join-Path $tempRoot "experiment"

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

$capsuleTool = Join-Path $logicLens "tools\capsule.py"
$overlayBuilder = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\build_dsl_b_overlay.py"
$rules = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\dsl-b-logical-rules-v0.jsonl"
$cases = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\cases-dsl-b-v0.jsonl"
$runner = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\management-course\run_codex_dsl_ablation.py"
$contracts = Join-Path $logicLens "contracts"

Invoke-Native "Check Codex CLI" {
    & $Codex --version
}

Invoke-Native "Check SWI-Prolog" {
    & $Swipl --version
}

Invoke-Native "Validate source management world" {
    py -3 $capsuleTool `
        --contracts-root $contracts `
        validate `
        --world-root $worldRoot
}

Invoke-Native "Compile DSL-A capsule" {
    py -3 $capsuleTool `
        --contracts-root $contracts `
        compile `
        --world-root $worldRoot `
        --capsule management.role-boundaries `
        --output $dslA
}

Invoke-Native "Build temporary DSL-B overlay" {
    py -3 $overlayBuilder `
        --source-world $worldRoot `
        --output-world $dslBWorld `
        --rules $rules `
        --contracts-root $contracts
}

Invoke-Native "Ensure source management world is unchanged" {
    git -C $cto diff `
        --exit-code `
        -- worlds/management
}

Invoke-Native "Compile DSL-B capsule" {
    py -3 $capsuleTool `
        --contracts-root $contracts `
        compile `
        --world-root $dslBWorld `
        --capsule management.role-boundaries `
        --output $dslB
}

$arguments = @(
    $runner,
    "--logiclens-root", $logicLens,
    "--cases", $cases,
    "--dsl-a-package", $dslA,
    "--dsl-b-package", $dslB,
    "--output-root", $output,
    "--codex", $Codex,
    "--swipl", $Swipl,
    "--timeout-seconds", "$TimeoutSeconds",
    "--repetitions", "$Repetitions",
    "--conditions", "direct", "gold-a", "gold-b"
)

if ($Model) {
    $arguments += @("--model", $Model)
}

Invoke-Native "Run progressive management Codex A/B ablation" {
    py -3 @arguments
}

$summary = Get-Content `
    (Join-Path $output "summary.json") `
    -Raw |
    ConvertFrom-Json

Write-Host ""
Write-Host "Experiment summary"
Write-Host "  Cases:      $($summary.caseCount)"
Write-Host "  Calls:      $($summary.callCount)"
Write-Host "  Model:      $($summary.modelSelection)"
Write-Host "  DSL-A hash: $($summary.hashes.dslAPackage)"
Write-Host "  DSL-B hash: $($summary.hashes.dslBPackage)"

foreach ($metric in $summary.metrics) {
    Write-Host ""
    Write-Host "  $($metric.condition)"
    Write-Host "    task status accuracy:  $($metric.taskStatusAccuracy)"
    Write-Host "    frame status accuracy: $($metric.frameStatusAccuracy)"
    Write-Host "    evidence exact rate:   $($metric.evidenceExactRate)"
    Write-Host "    proof-node recall:     $($metric.meanProofNodeRecall)"
    Write-Host "    latency mean ms:       $($metric.latencyMeanMs)"
}

exit 0
