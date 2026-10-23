# Exercise real native-client functions with mocked network/process/SSH effects.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Installer parse failure' }
foreach ($node in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
    . ([scriptblock]::Create($node.Extent.Text))
}
function Assert-Throws { param([scriptblock]$Action) $failed = $false; try { & $Action } catch { $failed = $true }; if (-not $failed) { throw 'Expected failure was accepted' } }
# Edition is not a reason to reject a remote native client; no localized caption matching.
foreach ($caption in @('Microsoft Windows 11 Home', 'Microsoft Windows 11 Pro', 'Microsoft Windows 10 Enterprise', 'Windows 11 家庭中文版')) {
    Assert-WorkshopWindowsHost $caption '10.0.26200' 1 'AMD64'
}
Assert-WorkshopWindowsHost 'Windows 11 Home ARM' '10.0.26200' 1 'ARM64'
Assert-Throws { Assert-WorkshopWindowsHost 'Windows 7' '6.1.7601' 1 'AMD64' }
Assert-Throws { Assert-WorkshopWindowsHost 'Windows Server' '10.0.26200' 3 'AMD64' }
Assert-Throws { Assert-WorkshopWindowsHost 'Windows 11 Home' '10.0.26200' 1 'x86' }
foreach ($bad in @('100.80.90.10:9119', 'file:///tmp/backend', 'http://127.0.0.1:9119', 'http://localhost:9119', 'http://0.0.0.0:9119', 'http://[::]:9119', 'http://user:secret@100.80.90.10:9119', 'http://100.80.90.10:9119/?secret=value')) {
    Assert-Throws { Get-WorkshopRemoteUri $bad }
}
$url = Get-WorkshopRemoteUri 'http://100.80.90.10:9119/'
if ($url -ne 'http://100.80.90.10:9119') { throw 'Remote URL normalization failed' }
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('hermes remote ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
$networkCalls = New-Object 'System.Collections.Generic.List[string]'
$nativeCalls = New-Object 'System.Collections.Generic.List[object]'
$authRequired = $true
function Invoke-RestMethod { param($Uri, $TimeoutSec) $networkCalls.Add($Uri); return @{ auth_required = $authRequired } }
function Invoke-Checked { param($File, [string[]]$Arguments) $nativeCalls.Add(@($File, $Arguments)) }
function Get-Command { param($Name, $ErrorAction) if ($Name -eq 'ssh') { return @{ Source = 'mock-ssh' } }; throw 'Unexpected executable lookup' }
try {
    Test-WorkshopRemoteBackend $url
    if ($networkCalls[0] -ne ($url + '/api/status')) { throw 'Wrong backend probe URL' }
    $authRequired = $false
    Assert-Throws { Test-WorkshopRemoteBackend $url }
    $authRequired = $true
    Save-Utf8 (Join-Path $fixture 'remote-url.txt') $url
    if ((Get-WorkshopRemoteUrl '' $fixture) -ne $url) { throw 'Saved URL was not reused' }
    Assert-Throws { Reset-WorkshopRemoteLogin $url 'ben@different-server' '~/setup-hermes.sh' }
    Assert-Throws { Reset-WorkshopRemoteLogin $url 'ben@100.80.90.10' "~/bad`npath" }
    if ($nativeCalls.Count) { throw 'Rejected reset performed a native action' }
    Reset-WorkshopRemoteLogin $url 'ben@100.80.90.10' '~/setup-hermes.sh'
    if ($nativeCalls.Count -ne 1 -or $nativeCalls[0][0] -ne 'ssh') { throw 'Reset did not use native SSH exactly once' }
    $arguments = $nativeCalls[0][1]
    if ($arguments[0] -ne '-t' -or $arguments[1] -ne 'ben@100.80.90.10' -or $arguments[2] -notlike 'HERMES_RESET_DASHBOARD_AUTH=1 bash *') { throw 'Wrong remote reset command' }
    # Enforce the no-virtualization/no-local-Docker contract on executable commands.
    $commands = $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)
    foreach ($command in $commands) {
        if ($command.GetCommandName() -in @('wsl', 'wsl.exe', 'docker', 'docker.exe', 'Get-VM', 'Enable-WindowsOptionalFeature', 'Get-WindowsOptionalFeature', 'Register-ScheduledTask')) {
            throw 'Native Windows client attempted a forbidden local virtualization/backend operation'
        }
    }
    Write-Host 'Windows remote checks passed: Home/Pro/ARM, URL validation, auth gate, saved URL and SSH reset.'
} finally { Remove-Item -LiteralPath $fixture -Recurse -Force }
