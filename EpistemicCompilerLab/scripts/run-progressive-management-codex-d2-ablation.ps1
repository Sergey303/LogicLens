[CmdletBinding()]
param(
    [string] $LogicLensRoot = "D:\projects\ChatPilotGroup\LogicLens",
    [string] $Codex = "codex",
    [string] $Swipl = "swipl",
    [ValidateRange(1, 20)] [int] $Repetitions = 1,
    [ValidateRange(1, 3600)] [int] $TimeoutSeconds = 300,
    [string] $Model
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
function Invoke-Native {
    param([Parameter(Mandatory)][string]$Name,[Parameter(Mandatory)][scriptblock]$Command)
    Write-Host ""; Write-Host "============================================================"; Write-Host $Name; Write-Host "============================================================"
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
}
$logicLens=(Resolve-Path $LogicLensRoot).Path
$d2Root=Join-Path $logicLens "EpistemicCompilerLab\progressive-dsl\opinion-d2"
$runId=Get-Date -Format "yyyyMMdd-HHmmss"
$tempRoot=Join-Path $env:TEMP "progressive-management-codex-d2-$runId"
$offline=Join-Path $tempRoot "offline-contract"
$output=Join-Path $tempRoot "experiment"
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
Invoke-Native "Check Codex CLI" { & $Codex --version }
Invoke-Native "Check SWI-Prolog" { & $Swipl --version }
Invoke-Native "Verify frozen DSL-D2 contracts" { py -3 (Join-Path $d2Root "verify_contract.py") }
Invoke-Native "Verify offline DSL-D2 runner and scorer" {
    py -3 (Join-Path $d2Root "run_codex_ablation.py") --root $d2Root --output-root $offline --fake-provider --skip-prolog --repetitions 1
}
$arguments=@((Join-Path $d2Root "run_codex_ablation.py"),"--root",$d2Root,"--output-root",$output,"--codex",$Codex,
 "--swipl",$Swipl,"--timeout-seconds","$TimeoutSeconds","--repetitions","$Repetitions",
 "--conditions","metadata_absent","naive_independent","raw_declared","verified")
if ($Model) { $arguments += @("--model",$Model) }
Invoke-Native "Run DSL-D2 dependency-aware fusion ablation" { py -3 @arguments }
foreach ($name in @("reports-v0.jsonl","cases-v0.jsonl","README.md","report-v0.schema.json","case-v0.schema.json","codex-response-v0.schema.json","prompt-v0.md")) {
    Copy-Item (Join-Path $d2Root $name) (Join-Path $output $name) -Force
}
$summary=Get-Content (Join-Path $output "summary.json") -Raw | ConvertFrom-Json
Write-Host ""; Write-Host "Experiment summary"; Write-Host "  Linear issue: ENG-187"; Write-Host "  Cases: $($summary.caseCount)"; Write-Host "  Calls: $($summary.callCount)"
foreach ($m in $summary.metrics) {
 Write-Host ""; Write-Host "  $($m.condition)"
 Write-Host "    task conclusion accuracy: $($m.taskConclusionAccuracy)"
 Write-Host "    condition accuracy:       $($m.conditionConclusionAccuracy)"
 Write-Host "    operator plan accuracy:   $($m.operatorPlanAccuracy)"
 Write-Host "    dependency safety:        $($m.dependencySafetyRate)"
 Write-Host "    exact value transport:    $($m.exactValueTransportRate)"
 Write-Host "    semantic obligations:     $($m.semanticObligationsRate)"
 Write-Host "    latency mean ms:          $($m.latencyMeanMs)"
}
$archive="$output.zip"
if (Test-Path $archive) { Remove-Item $archive -Force }
Compress-Archive -Path "$output\*" -DestinationPath $archive -CompressionLevel Optimal -Force
Write-Host ""; Write-Host "[CGR_ARTIFACT_TITLE] DSL-D2 dependency-aware fusion ablation"; Write-Host "[CGR_ARTIFACT] $archive"
exit 0
