# No installation commands: exercise the production PowerShell prompt shapes.
$ErrorActionPreference = 'Stop'
$username = Read-Host 'Dashboard username'
$visibility = Read-Host 'Show password while typing? [y/N]'
$securePassword = Read-Host 'Dashboard password (at least 12 characters; hidden)' -AsSecureString
try { $password = [Net.NetworkCredential]::new('', $securePassword).Password }
finally { $securePassword.Dispose() }
$secureConfirm = Read-Host 'Confirm dashboard password (hidden)' -AsSecureString
try { $confirmation = [Net.NetworkCredential]::new('', $secureConfirm).Password }
finally { $secureConfirm.Dispose() }
if ($username -cne 'smoke-user' -or $visibility -cne 'n' -or $password -cne 'private-smoke-password' -or $confirmation -cne $password) { exit 1 }
Write-Host 'PRESETS_OK'
exit 0
