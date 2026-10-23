# Verify the generated Desktop launcher selects remote mode without touching parent settings.
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'), [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Installer parse failure' }
foreach ($node in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
    . ([scriptblock]::Create($node.Extent.Text))
}
$savedHome = $env:HERMES_HOME
$savedRemote = $env:HERMES_DESKTOP_REMOTE_URL
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('hermes layout ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
try {
    $env:HERMES_HOME = 'fixture-only-custom-home'
    $guard = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.IfStatementAst] -and $node.Extent.Text.StartsWith('if ($env:HERMES_HOME)') }, $true)
    if (-not $guard) { throw 'Missing process-local layout guard' }
    & ([scriptblock]::Create($guard.Extent.Text))
    if ($env:HERMES_HOME) { throw 'Installer retained the inherited profile selector' }
    $env:HERMES_HOME = 'fixture-only-custom-home'
    $env:HERMES_DESKTOP_REMOTE_URL = 'http://old.invalid'
    $result = Join-Path $fixture 'observed.json'
    $fakeHermes = Join-Path $fixture 'fake-hermes.ps1'
    $fakeCode = "@{ home = [string]`$env:HERMES_HOME; remote = [string]`$env:HERMES_DESKTOP_REMOTE_URL; arguments = `$args } | ConvertTo-Json | Set-Content -LiteralPath '$($result.Replace("'", "''"))'`nexit 0"
    [IO.File]::WriteAllText($fakeHermes, $fakeCode)
    $nativeCalls = New-Object 'System.Collections.Generic.List[object]'
    $launches = New-Object 'System.Collections.Generic.List[object]'
    function Invoke-RestMethod { param($Uri, $TimeoutSec) return @{ auth_required = $true } }
    function Invoke-Checked { param($File, [string[]]$Arguments) $nativeCalls.Add($Arguments) }
    function Start-Process { param($FilePath, $ArgumentList) $launches.Add(@($FilePath, $ArgumentList)) }
    Complete-WorkshopRemoteSetup $fakeHermes $fixture 'http://100.80.90.10:9119' 'workshop'
    if ($nativeCalls.Count -ne 1 -or $nativeCalls[0][0] -ne 'desktop' -or $nativeCalls[0][1] -ne '--build-only') { throw 'Remote setup ran something other than the Desktop build' }
    if ($launches.Count -ne 1) { throw 'Desktop was not launched exactly once' }
    $launcher = Join-Path $fixture 'Open-Hermes-Desktop.ps1'
    $engine = (Get-Process -Id $PID).Path
    & $engine -NoProfile -File $launcher
    if ($LASTEXITCODE -ne 0) { throw 'Generated launcher failed' }
    $observed = Get-Content $result -Raw | ConvertFrom-Json
    if ($observed.home -ne '' -or $observed.remote -ne 'http://100.80.90.10:9119' -or $observed.arguments[0] -ne 'desktop') { throw 'Desktop launcher selected the wrong home, remote URL or command' }
    if ($env:HERMES_HOME -ne 'fixture-only-custom-home' -or $env:HERMES_DESKTOP_REMOTE_URL -ne 'http://old.invalid') { throw 'Launcher changed its parent environment' }
    if (Test-Path (Join-Path $fixture 'backend.ps1')) { throw 'Remote setup created a local backend' }
    Write-Host 'Remote Desktop launcher regression passed.'
} finally {
    if ($null -eq $savedHome) { Remove-Item Env:HERMES_HOME -ErrorAction SilentlyContinue } else { $env:HERMES_HOME = $savedHome }
    if ($null -eq $savedRemote) { Remove-Item Env:HERMES_DESKTOP_REMOTE_URL -ErrorAction SilentlyContinue } else { $env:HERMES_DESKTOP_REMOTE_URL = $savedRemote }
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
