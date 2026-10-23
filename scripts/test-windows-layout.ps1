# Exercise production AST fragments without running the installer or installing apps.
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'), [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Installer parse failure' }
$savedHome = $env:HERMES_HOME
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('hermes layout ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
try {
    $env:HERMES_HOME = 'fixture-only-custom-home'
    $guard = $ast.Find({ param($node)
        $node -is [System.Management.Automation.Language.IfStatementAst] -and
        $node.Extent.Text.StartsWith('if ($env:HERMES_HOME)')
    }, $true)
    if (-not $guard) { throw 'Missing process-local layout guard' }
    & ([scriptblock]::Create($guard.Extent.Text))
    if ($env:HERMES_HOME) { throw 'Installer retained the inherited profile selector' }

    $env:HERMES_HOME = 'fixture-only-custom-home'
    $result = Join-Path $fixture 'observed.txt'
    $fakeHermes = Join-Path $fixture 'fake-hermes.ps1'
    $fakeCode = "[IO.File]::WriteAllText('$($result.Replace("'", "''"))', [string]`$env:HERMES_HOME)`nexit 0"
    [IO.File]::WriteAllText($fakeHermes, $fakeCode)
    $escapedHermes = $fakeHermes.Replace("'", "''")
    $ProfileName = 'workshop'
    $backend = Join-Path $fixture 'backend.ps1'
    function Save-Utf8 { param($Path, $Text) [IO.File]::WriteAllText($Path, $Text) }
    $emitter = $ast.Find({ param($node)
        $node -is [System.Management.Automation.Language.CommandAst] -and
        $node.Extent.Text.StartsWith('Save-Utf8 $backend ')
    }, $true)
    if (-not $emitter) { throw 'Missing backend emitter' }
    & ([scriptblock]::Create($emitter.Extent.Text))
    $engine = (Get-Process -Id $PID).Path
    & $engine -NoProfile -File $backend
    if ($LASTEXITCODE -ne 0) { throw 'Generated backend failed' }
    if (-not (Test-Path $result)) { throw 'Generated backend never invoked Hermes' }
    if ([IO.File]::ReadAllText($result) -ne '') { throw 'Generated backend inherited a custom HERMES_HOME' }
    if ($env:HERMES_HOME -ne 'fixture-only-custom-home') { throw 'Backend changed its parent environment' }
    Write-Host 'Windows layout regression passed: installer and backend isolate inherited HERMES_HOME.'
} finally {
    if ($null -eq $savedHome) { Remove-Item Env:HERMES_HOME -ErrorAction SilentlyContinue }
    else { $env:HERMES_HOME = $savedHome }
    Remove-Item -LiteralPath $fixture -Recurse -Force
}
