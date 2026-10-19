param([string]$Home = (Join-Path $HOME 'hermes-tailscale-docker'), [switch]$Desktop)
$ErrorActionPreference = 'Stop'
# Native Windows flow: bootstrap.py drives the official native installer + native runtime.
# It does NOT use WSL. Docker Desktop (host) is the terminal sandbox backend.
$python = Get-Command python -ErrorAction SilentlyContinue
$py = Get-Command py -ErrorAction SilentlyContinue
$scriptArgs = @((Join-Path $PSScriptRoot 'bootstrap.py'), '--home', $Home)
if ($Desktop) { $scriptArgs += '--desktop' }
if ($py) { & py -3 @scriptArgs }
elseif ($python) { & python @scriptArgs }
else { throw 'Python 3.9+ is required. Install using your approved host process; no packages were installed.' }
if ($LASTEXITCODE -ne 0) { throw "Bootstrap stopped (exit $LASTEXITCODE). See README recovery." }
