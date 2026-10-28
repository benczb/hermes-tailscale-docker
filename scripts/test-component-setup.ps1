# Exercise GUI wait/retry and the generated limited-user gateway/backend launcher.
# No package installation, WSL command, daemon or real network call is performed.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Windows setup does not parse' }
foreach ($node in $ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst]}, $true)) { . ([scriptblock]::Create($node.Extent.Text)) }
$script:checks = 0; $script:responses = 0; $script:actions = 0
function Read-Host { param($Prompt) $script:responses++; return '' }
Wait-WorkshopComponent -Component docker -Gui -Message 'Start Docker' -Check { $script:checks++; return $script:checks -ge 3 }
if ($script:checks -ne 3 -or $script:responses -ne 2) { throw 'Wait did not preserve/recheck the current session' }
Invoke-WorkshopComponentStep -Component tailscale -Gui -Message 'Retry install' -Action { $script:actions++; if ($script:actions -lt 2) { throw 'Synthetic installer failure' } }
if ($script:actions -ne 2 -or $script:responses -ne 3) { throw 'Failed installation was not retried only after a GUI response' }
$failed = $false
try { Wait-WorkshopComponent -Component docker -Message 'Docker not ready' -Check { return $false } } catch { $failed = $true }
if (-not $failed -or $script:responses -ne 3) { throw 'CLI mode unexpectedly requested graphical input' }
function tailscale {
    param([Parameter(ValueFromRemainingArguments=$true)]$Arguments)
    $global:LASTEXITCODE = 0
    if ($Arguments[0] -eq 'status') { return ('{"BackendState":"' + $script:tailState + '"}') }
    return '100.80.90.10'
}
$script:tailState = 'Stopped'
if (Get-WorkshopTailnetIp) { throw 'A stopped Tailscale was accepted because it retained an IP' }
$script:tailState = 'Running'
if ((Get-WorkshopTailnetIp) -ne '100.80.90.10') { throw 'Connected host Tailscale was not recognized' }
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('hermes GUI fixture ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
try {
    $fakeHermes = Join-Path $fixture 'mock-hermes.ps1'
    $mock = @'
if ($args[2] -eq 'gateway') {
    if ($env:HERMES_TEST_GATEWAY -eq 'absent') { Write-Output '{"state":"absent","endpoint":null}'; exit 5 }
    if ($env:HERMES_TEST_GATEWAY -eq 'starting') { Write-Output '{"state":"starting","endpoint":{"pid":1234}}'; exit 0 }
    Write-Output '{"state":"ready","endpoint":{"pid":1234}}'; exit 0
}
[IO.File]::WriteAllText($env:HERMES_TEST_SERVED, 'served')
exit 0
'@
    Save-Utf8 $fakeHermes $mock
    $escapedHermes = $fakeHermes.Replace("'", "''")
    $ProfileName = 'starter-agent'; $backendPort = 9120
    $receipt = Join-Path $fixture 'gateway-ready.json'; $escapedReceipt = $receipt.Replace("'", "''")
    $assignment = @($ast.FindAll({param($n) $n -is [System.Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq '$backendCode'}, $true))
    if ($assignment.Count -ne 1) { throw 'Expected the production backend generator' }
    . ([scriptblock]::Create($assignment[0].Extent.Text))
    $backend = Join-Path $fixture 'backend.ps1'; Save-Utf8 $backend $backendCode
    $env:HERMES_TEST_SERVED = Join-Path $fixture 'served'
    $hostExe = (Get-Process -Id $PID).Path
    foreach ($case in @('absent','starting','ready')) {
        Remove-Item -LiteralPath $env:HERMES_TEST_SERVED,$receipt -Force -ErrorAction SilentlyContinue
        $env:HERMES_TEST_GATEWAY = $case
        & $hostExe -NoProfile -File $backend
        if ($case -eq 'ready') {
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path $env:HERMES_TEST_SERVED) -or -not (Test-Path $receipt)) { throw 'Verified gateway did not precede backend startup' }
        } elseif ($LASTEXITCODE -eq 0 -or (Test-Path $env:HERMES_TEST_SERVED) -or (Test-Path $receipt)) {
            throw 'Absent/starting gateway incorrectly allowed backend/completion'
        }
    }
    Write-Host 'Component waits/retries, Tailscale connection state and gateway-before-backend verification passed.'
} finally {
    Remove-Item Env:HERMES_TEST_GATEWAY,Env:HERMES_TEST_SERVED -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
