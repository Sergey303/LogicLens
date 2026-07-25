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
        $home = $properties.$propertyName
        if ([string]::IsNullOrWhiteSpace($home)) {
            continue
        }

        $candidates.Add((Join-Path $home 'bin\swipl.exe'))
        $candidates.Add((Join-Path $home 'swipl.exe'))
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
Install it with:
  pwsh EpistemicCompilerLab/scripts/setup.ps1
'@
}

exit 1
