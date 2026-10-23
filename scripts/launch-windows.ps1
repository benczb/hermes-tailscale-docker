# Double-click launcher. UAC still requires the user to approve elevation.
$ErrorActionPreference = 'Stop'
try {
    $installer = Join-Path $PSScriptRoot 'setup-windows.ps1'
    $arguments = '-NoExit -NoProfile -ExecutionPolicy Bypass -File "' + $installer + '"'
    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments -Wait
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
