param(
    [Parameter(Mandatory, Position = 0)]
    [string] $Operation,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command swipl -ErrorAction SilentlyContinue)) {
    throw 'SWI-Prolog executable "swipl" was not found in PATH.'
}

$labRoot = Split-Path -Parent $PSScriptRoot
$entryPoint = Join-Path $labRoot 'prolog/entry.pl'

& swipl -q -s $entryPoint -- $Operation @Arguments

if ($LASTEXITCODE -ne 0) {
    throw "SWI-Prolog exited with code $LASTEXITCODE."
}