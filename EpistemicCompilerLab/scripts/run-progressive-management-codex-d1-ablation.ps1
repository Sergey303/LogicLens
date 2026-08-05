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
$d1Root = Join-Path `
    $logicLens `
    "EpistemicCompilerLab\progressive-dsl\opinion-d1"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$tempRoot = Join-Path `
    $env:TEMP `
    "progressive-management-codex-d1-$runId"
$offline = Join-Path $tempRoot "offline-contract"
$output = Join-Path $tempRoot "experiment"

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

Invoke-Native "Check Codex CLI" {
    & $Codex --version
}

Invoke-Native "Check SWI-Prolog" {
    & $Swipl --version
}

Invoke-Native "Verify frozen DSL-D1 contracts" {
    py -3 (Join-Path $d1Root "verify_contract.py")
}

Invoke-Native "Verify offline DSL-D1 runner and corrected scorer" {
    py -3 `
        (Join-Path $d1Root "run_codex_ablation.py") `
        --root $d1Root `
        --output-root $offline `
        --fake-provider `
        --skip-prolog `
        --repetitions 1
}

$arguments = @(
    (Join-Path $d1Root "run_codex_ablation.py"),
    "--root", $d1Root,
    "--output-root", $output,
    "--codex", $Codex,
    "--swipl", $Swipl,
    "--timeout-seconds", "$TimeoutSeconds",
    "--repetitions", "$Repetitions",
    "--conditions", "scalar", "rounded", "exact", "verified"
)

if ($Model) {
    $arguments += @("--model", $Model)
}

Invoke-Native "Run Scalar, Rounded, Exact and Verified DSL-D1 ablation" {
    py -3 @arguments
}

foreach ($name in @(
    "opinions-v0.jsonl",
    "cases-v0.jsonl",
    "README.md",
    "opinion-v0.schema.json",
    "case-v0.schema.json",
    "codex-response-v0.schema.json",
    "prompt-v0.md"
)) {
    Copy-Item `
        -Path (Join-Path $d1Root $name) `
        -Destination (Join-Path $output $name) `
        -Force
}

$summary = Get-Content `
    (Join-Path $output "summary.json") `
    -Raw |
    ConvertFrom-Json

Write-Host ""
Write-Host "Experiment summary"
Write-Host "  Linear issue: ENG-186"
Write-Host "  Cases:       $($summary.caseCount)"
Write-Host "  Calls:       $($summary.callCount)"
Write-Host "  Model:       $($summary.modelSelection)"

foreach ($metric in $summary.metrics) {
    Write-Host ""
    Write-Host "  $($metric.condition)"
    Write-Host "    task conclusion accuracy:        $($metric.taskConclusionAccuracy)"
    Write-Host "    condition conclusion accuracy:   $($metric.conditionConclusionAccuracy)"
    Write-Host "    exact boundary preservation:     $($metric.exactBoundaryPreservationRate)"
    Write-Host "    numeric equality:                $($metric.suppliedNumberNumericEqualityRate)"
    Write-Host "    canonical lexical exact:         $($metric.canonicalLexicalExactRate)"
    Write-Host "    exact fraction transport:        $($metric.exactFractionTransportExactRate)"
    Write-Host "    projection arithmetic:           $($metric.projectionArithmeticCorrectRate)"
    Write-Host "    invariant interpretation:        $($metric.invariantInterpretationCorrectRate)"
    Write-Host "    semantic obligations:            $($metric.semanticObligationsRate)"
    Write-Host "    probability semantics safety:    $($metric.probabilitySemanticsSafetyRate)"
    Write-Host "    latency mean ms:                 $($metric.latencyMeanMs)"
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
Write-Host "[CGR_ARTIFACT_TITLE] DSL-D1 exact-rational boundary ablation"
Write-Host "[CGR_ARTIFACT] $archive"

exit 0
