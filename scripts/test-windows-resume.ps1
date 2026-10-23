# Exercise production resume behavior; no real apps, credentials or network are used.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Installer parse failure' }
$function=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Complete-WorkshopProfileSetup'},$true)
if (-not $function) { throw 'Missing production resume helper' }
. ([scriptblock]::Create($function.Extent.Text))
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('hermes resume ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
$pending=Join-Path $fixture 'setup-pending'
$calls=New-Object 'System.Collections.Generic.List[object]'
$failWizard=$false
function Invoke-Checked { param($File,[string[]]$Arguments) $calls.Add(@($File,$Arguments)); if ($failWizard) { throw 'Fixture interrupted wizard' } }
try {
    Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture
    if ($calls.Count) { throw 'Completed profile unexpectedly reran the wizard' }
    New-Item -ItemType File -Path $pending | Out-Null
    $failWizard=$true; $failed=$false
    try { Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture } catch { $failed=$true }
    if (-not $failed -or -not (Test-Path $pending)) { throw 'Interrupted wizard did not preserve resumable state' }
    if ($calls.Count -ne 1 -or $calls[0][0] -ne 'fixture-hermes' -or ($calls[0][1] -join '|') -ne '-p|workshop|setup') { throw 'Wrong profile wizard was invoked' }
    # Explicit deferral resumes after the same pending wizard, even if calling it would fail again.
    $before=$calls.Count
    Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture -Skip
    if ($calls.Count -ne $before -or (Test-Path $pending)) { throw 'Explicit deferral did not bypass the pending wizard' }
    $failWizard=$false
    New-Item -ItemType File -Path $pending | Out-Null
    Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture
    if ($calls.Count -ne ($before+1) -or (Test-Path $pending)) { throw 'Successful wizard did not clear pending state' }
    Write-Host 'Windows resume checks passed: no-op rerun, interrupted wizard, explicit deferral and successful setup.'
} finally { Remove-Item -LiteralPath $fixture -Recurse -Force }
