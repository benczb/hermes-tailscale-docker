# Run the real dashboard-auth block against private fixtures and mocked CLI/prompts.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'), [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Installer parse failure' }
$block = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.IfStatementAst] -and
    $node.Extent.Text.StartsWith('if ($ResetDashboardAuth -or ')
}, $true)
if (-not $block) { throw 'Missing dashboard auth block' }
$state = Join-Path ([IO.Path]::GetTempPath()) ('hermes login ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $state | Out-Null
$ProfileName = 'workshop'
$hermes = 'mock-hermes'
$ResetDashboardAuth = $false
$answers = New-Object 'System.Collections.Generic.Queue[string]'
$calls = New-Object 'System.Collections.Generic.List[object]'
$readModes = New-Object 'System.Collections.Generic.List[bool]'
$password = 'Fixture $ # CaseSensitive Password!'
function Read-Host {
    param([string]$Prompt, [switch]$AsSecureString)
    if ($answers.Count -eq 0) { throw 'Unexpected login prompt' }
    if ($Prompt -match '^(Dashboard password|Confirm dashboard password)') { $readModes.Add([bool]$AsSecureString) }
    $value = $answers.Dequeue()
    if ($AsSecureString) { return ConvertTo-SecureString $value -AsPlainText -Force }
    return $value
}
function Invoke-Checked { param($File, [string[]]$Arguments) $calls.Add($Arguments) }
function New-HexSecret { param($Length) return ('a' * ($Length * 2)) }
function Save-Utf8 { param($Path, $Text) [IO.File]::WriteAllText($Path, $Text) }
try {
    foreach ($value in @('', 'ben-workshop', '', 'short', $password, 'wrong confirmation', $password, $password)) { $answers.Enqueue($value) }
    $code = [scriptblock]::Create($block.Extent.Text)
    . $code
    if ($answers.Count) { throw 'Login prompts did not consume expected retries' }
    if ($calls.Count -ne 3) { throw 'Credentials were written before validation completed' }
    if ($calls[0][-1] -cne 'ben-workshop' -or $calls[1][-1] -cne $password) { throw 'Custom username/password were not passed exactly' }
    if (-not (Test-Path (Join-Path $state 'auth-configured'))) { throw 'Login marker missing' }
    if ($readModes.Contains($false)) { throw 'Default password entry was visible' }
    $hiddenReadCount = $readModes.Count
    $original = [IO.File]::ReadAllText((Join-Path $state 'dashboard-login.txt'))
    . $code
    if ($calls.Count -ne 3) { throw 'Rerun changed existing credentials' }
    $ResetDashboardAuth = $true
    foreach ($value in @('new-user', 'y', $password, $password)) { $answers.Enqueue($value) }
    . $code
    if ($readModes.Count -ne ($hiddenReadCount + 2) -or $readModes[$hiddenReadCount] -or $readModes[$hiddenReadCount + 1]) { throw 'Visible entry mode was not used for both prompts' }
    if ($calls.Count -ne 6 -or $calls[3][-1] -cne 'new-user') { throw 'Explicit login reset failed' }
    if ([IO.File]::ReadAllText((Join-Path $state 'dashboard-login.txt')) -ceq $original) { throw 'Reset kept the previous login' }
    Write-Host 'Dashboard login regression passed: custom credentials, retries, preservation and explicit reset.'
} finally {
    Remove-Item -LiteralPath $state -Recurse -Force
}
