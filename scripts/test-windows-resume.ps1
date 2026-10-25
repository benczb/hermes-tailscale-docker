# Exercise production resume behavior; no real apps, credentials or network are used.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'Installer parse failure' }
$function=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Complete-WorkshopProfileSetup'},$true)
if (-not $function) { throw 'Missing production resume helper' }
foreach ($definition in $ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst]},$true)) { . ([scriptblock]::Create($definition.Extent.Text)) }
$invokeDefinition=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Invoke-Checked'},$true)
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('hermes resume ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
$pending=Join-Path $fixture 'setup-pending'
$calls=New-Object 'System.Collections.Generic.List[object]'
$failWizard=$false
function Invoke-Checked { param($File,[string[]]$Arguments) $calls.Add(@($File,$Arguments)); if ($failWizard -and $Arguments[-1] -eq 'setup') { throw 'Fixture interrupted wizard' } }
try {
    Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture
    if ($calls.Count) { throw 'Completed profile unexpectedly reran the wizard' }
    New-Item -ItemType File -Path $pending | Out-Null
    $failWizard=$true; $failed=$false
    try { Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture } catch { $failed=$true }
    if (-not $failed -or -not (Test-Path $pending)) { throw 'Interrupted wizard did not preserve resumable state' }
    if ($calls.Count -ne 2 -or $calls[0][0] -ne 'fixture-hermes' -or ($calls[0][1] -join '|') -ne '-p|workshop|setup') { throw 'Wrong profile wizard was invoked' }
    # Explicit deferral resumes after the same pending wizard, even if calling it would fail again.
    $before=$calls.Count
    Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture -Skip
    if ($calls.Count -ne $before -or (Test-Path $pending)) { throw 'Explicit deferral did not bypass the pending wizard' }
    $failWizard=$false
    New-Item -ItemType File -Path $pending | Out-Null
    Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture
    if ($calls.Count -ne ($before+2) -or (Test-Path $pending)) { throw 'Successful wizard did not clear pending state' }
    if (($calls[-1][1] -join '|') -ne '-p|workshop|config|set|terminal.backend|docker') { throw 'Wizard did not restore Docker terminal settings' }
    New-Item -ItemType File -Path $pending | Out-Null
    Complete-WorkshopProfileSetup 'fixture-hermes' 'workshop' $fixture -TerminalBackend local
    if (($calls[-1][1] -join '|') -ne '-p|workshop|config|set|terminal.backend|local') { throw 'Local terminal choice was not restored' }
    # The final wizard launches in its own process; execute the generated launcher against a fake CLI.
    . ([scriptblock]::Create($invokeDefinition.Extent.Text))
    New-Item -ItemType File -Path $pending | Out-Null
    $fakeHermes=Join-Path $fixture 'fake-hermes.ps1'
    $log=Join-Path $fixture 'wizard-calls.txt'
    $fakeCode="Add-Content -LiteralPath '$($log.Replace("'", "''"))' -Value (`$args -join '|')`nexit 0"
    [IO.File]::WriteAllText($fakeHermes,$fakeCode)
    $launches=New-Object 'System.Collections.Generic.List[object]'
    function Start-Process { param($FilePath,$ArgumentList) $launches.Add(@($FilePath,$ArgumentList)) }
    Start-WorkshopProfileSetup $fakeHermes 'workshop' $fixture 'http://100.80.90.10:9119' -TerminalBackend local -WorkingDirectory (Join-Path $fixture 'local workspace')
    if ($launches.Count -ne 1 -or -not (Test-Path $pending) -or (Test-Path $log)) { throw 'Wizard ran in the parent or pending state was cleared before launch' }
    $engine=(Get-Process -Id $PID).Path
    & $engine -NoProfile -File (Join-Path $fixture 'Configure-Hermes-Profile.ps1')
    if ($LASTEXITCODE -ne 0 -or (Test-Path $pending)) { throw 'Final wizard launcher failed to complete' }
    $observed=Get-Content $log
    if ($observed.Count -ne 4 -or $observed[0] -ne '-p|workshop|setup' -or $observed[1] -ne '-p|workshop|config|set|terminal.backend|local' -or $observed[2] -ne ('-p|workshop|config|set|terminal.cwd|' + (Join-Path $fixture 'local workspace')) -or $observed[3] -ne '-p|workshop|config|set|dashboard.public_url|http://100.80.90.10:9119') { throw 'Final wizard did not restore sandbox/public URL settings' }
    $source=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'setup-windows.ps1'))
    if ($source.LastIndexOf('    Start-WorkshopProfileSetup -HermesCommand') -lt $source.IndexOf('Save-Utf8 (Join-Path $state ''installation-ready.txt'')')) {
        throw 'Profile wizard started before installation readiness was saved'
    }
    Write-Host 'Windows resume checks passed: wizard last, separate process, sandbox restoration and explicit deferral.'

} finally { Remove-Item -LiteralPath $fixture -Recurse -Force }
