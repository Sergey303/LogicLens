param(
    [Parameter(Mandatory, Position = 0)]
    [string] $Operation,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)

$ErrorActionPreference = 'Stop'

$swipl = & (Join-Path $PSScriptRoot 'resolve-swipl.ps1') -Required
$labRoot = Split-Path -Parent $PSScriptRoot
$entryPoint = Join-Path $labRoot 'prolog/entry.pl'

& $swipl -q -s $entryPoint -- $Operation @Arguments

if ($LASTEXITCODE -ne 0) {
    throw "SWI-Prolog exited with code $LASTEXITCODE."
}
