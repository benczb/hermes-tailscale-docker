param([string]$Directory = (Join-Path $HOME 'hermes-sid-training'), [switch]$Desktop)
$ErrorActionPreference = 'Stop'
$python = Get-Command python -ErrorAction SilentlyContinue
$py = Get-Command py -ErrorAction SilentlyContinue
$scriptArgs = @((Join-Path $PSScriptRoot 'bootstrap.py'), '--directory', $Directory)
if ($Desktop) { $scriptArgs += '--desktop' }
if ($py) { & py -3 @scriptArgs }
elseif ($python) { & python @scriptArgs }
else { throw 'Python 3.9+ is required. Install using your approved host process; no packages were installed.' }
if ($LASTEXITCODE -ne 0) { throw "Bootstrap stopped (exit $LASTEXITCODE). See README recovery." }
