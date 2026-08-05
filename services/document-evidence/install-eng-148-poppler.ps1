[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = "Stop"
if (-not $IsWindows) {
    throw "This bootstrap is only for Windows. Install poppler-utils with the OS package manager."
}
if ((Get-Command pdfinfo -ErrorAction SilentlyContinue) -and
    (Get-Command pdftotext -ErrorAction SilentlyContinue)) {
    Write-Host "Poppler is already available on PATH."
    exit 0
}

$installed = $false
if (Get-Command winget -ErrorAction SilentlyContinue) {
    if ($PSCmdlet.ShouldProcess("oschwartz10612.Poppler", "Install with WinGet")) {
        winget install --id oschwartz10612.Poppler --exact `
            --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw "WinGet Poppler installation failed." }
        $installed = $true
    }
}
elseif (Get-Command choco -ErrorAction SilentlyContinue) {
    if ($PSCmdlet.ShouldProcess("poppler", "Install with Chocolatey")) {
        choco install poppler -y
        if ($LASTEXITCODE -notin @(0, 1641, 3010)) {
            throw "Chocolatey Poppler installation failed."
        }
        $installed = $true
    }
}
elseif (Get-Command scoop -ErrorAction SilentlyContinue) {
    if ($PSCmdlet.ShouldProcess("poppler", "Install with Scoop")) {
        scoop install poppler
        if ($LASTEXITCODE -ne 0) { throw "Scoop Poppler installation failed." }
        $installed = $true
    }
}
else {
    throw @"
No supported Windows package manager was found.
Install WinGet/App Installer, Chocolatey, or Scoop, then rerun this bootstrap.
You may also install Poppler manually and pass its bin directory to
verify-eng-148-demo.ps1 -PopplerBin <path>.
"@
}

if ($installed) {
    Write-Host "Poppler installation completed."
    Write-Host "The verifier will discover WinGet, Chocolatey, and Scoop installations automatically."
}
