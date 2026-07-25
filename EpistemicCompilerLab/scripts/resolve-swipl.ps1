[CmdletBinding()]
param(
    [switch] $Required
)

$ErrorActionPreference = 'Stop'

$command = Get-Command swipl -CommandType Application -ErrorAction SilentlyContinue |
    Select-Object -First 1

if ($command) {
    (Resolve-Path $command.Source).Path
    exit 0
}

$candidates = [System.Collections.Generic.List[string]]::new()
$registryPaths = @(
    'HKLM:\SOFTWARE\SWI\Prolog64',
    'HKLM:\SOFTWARE\SWI\Prolog',
    'HKCU:\SOFTWARE\SWI\Prolog64',
    'HKCU:\SOFTWARE\SWI\Prolog'
)

foreach ($registryPath in $registryPaths) {
    if (-not (Test-Path $registryPath)) {
        continue
    }

    $properties = Get-ItemProperty $registryPath
    foreach ($propertyName in @('home', 'Home')) {
        # PowerShell variable names are case-insensitive. Do not use $home:
        # it conflicts with the read-only automatic variable $HOME.
        $installRoot = $properties.$propertyName
        if ([string]::IsNullOrWhiteSpace($installRoot)) {
            continue
        }

        $candidates.Add((Join-Path $installRoot 'bin\swipl.exe'))
        $candidates.Add((Join-Path $installRoot 'swipl.exe'))
    }
}

foreach ($root in @(
    $env:ProgramFiles,
    ${env:ProgramFiles(x86)},
    (Join-Path $env:LOCALAPPDATA 'Programs')
)) {
    if ([string]::IsNullOrWhiteSpace($root)) {
        continue
    }

    $candidates.Add((Join-Path $root 'swipl\bin\swipl.exe'))
}

$resolved = $candidates |
    Select-Object -Unique |
    Where-Object { Test-Path $_ -PathType Leaf } |
    Select-Object -First 1

if ($resolved) {
    (Resolve-Path $resolved).Path
    exit 0
}

if ($Required) {
    throw @'
SWI-Prolog was not found in PATH, the Windows registry, or standard install folders.
Install the Windows 64-bit stable build from:
  https://www.swi-prolog.org/download/stable
Then open a new PowerShell window and run:
  swipl --version
'@
}

exit 1
