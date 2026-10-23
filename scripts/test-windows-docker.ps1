# Test the production edition/engine/port checks without installing apps or features.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'setup-windows.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Installer parse failure' }
foreach ($node in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) { . ([scriptblock]::Create($node.Extent.Text)) }
function Assert-Throws { param([scriptblock]$Action) $failed=$false; try { & $Action } catch { $failed=$true }; if (-not $failed) { throw 'Expected failure was accepted' } }
foreach ($caption in @('Windows 11 Home','Windows 11 Pro','Windows 10 Enterprise','Windows 11 Education')) { Assert-WorkshopWindowsHost $caption '10.0.26200' 1 'AMD64' }
Assert-WorkshopWindowsHost 'Windows 11 ARM' '10.0.26200' 1 'ARM64'
Assert-Throws { Assert-WorkshopWindowsHost 'Windows 7' '6.1.7601' 1 'AMD64' }
Assert-Throws { Assert-WorkshopWindowsHost 'Old Windows 10' '10.0.18363' 1 'AMD64' }
Assert-Throws { Assert-WorkshopWindowsHost 'Server' '10.0.26200' 3 'AMD64' }
Assert-Throws { Assert-WorkshopWindowsHost 'Windows 11' '10.0.26200' 1 'x86' }
Assert-WorkshopDockerEngine 'linux' 'Docker Desktop' '6.6.87.2-microsoft-standard-WSL2' 'npipe:////./pipe/dockerDesktopLinuxEngine'
Assert-Throws { Assert-WorkshopDockerEngine 'windows' 'Docker Desktop' '10.0.26200' 'npipe:////./pipe/docker_engine' }
Assert-Throws { Assert-WorkshopDockerEngine 'linux' 'Docker Desktop' '6.6-linuxkit' 'npipe:////./pipe/docker_engine' }
Assert-Throws { Assert-WorkshopDockerEngine 'linux' 'Ubuntu' '6.6-WSL2' 'ssh://remote' }
# Exercise the real WSL version parser against localized output, then verify update decisions.
$fakeWslOutput = "WSL version: 2.6.1.0`nKernel version: 6.6.87.2"
function wsl.exe { $global:LASTEXITCODE=0; return $fakeWslOutput }
if ((Get-WorkshopWslVersion) -ne [version]'2.6.1.0') { throw 'WSL parser chose the kernel version' }
$fakeWslOutput = "WSL-Version: 3.0.3.0`nKernel-Version: 6.6.87.2"
if ((Get-WorkshopWslVersion) -ne [version]'3.0.3.0') { throw 'Localized WSL version parsing failed' }
$versionAnswers = New-Object 'System.Collections.Generic.Queue[object]'
function Get-WorkshopWslVersion { return $versionAnswers.Dequeue() }
$updateCalls = New-Object 'System.Collections.Generic.List[object]'
$failUpdate = $false
function Invoke-Checked { param($File,[string[]]$Arguments) if ($failUpdate) { throw 'MSI 1603: WSL service could not be stopped' }; $updateCalls.Add(@($File,$Arguments)) }
foreach ($existing in @('2.1.5','2.6.1','3.0.3')) { $versionAnswers.Enqueue([version]$existing); Ensure-WorkshopWsl }
if ($updateCalls.Count) { throw 'Compatible WSL triggered an unnecessary update' }
$versionAnswers.Enqueue([version]'2.0.0'); $versionAnswers.Enqueue([version]'3.0.3')
Ensure-WorkshopWsl
if ($updateCalls.Count -ne 1 -or $updateCalls[0][0] -ne 'wsl.exe' -or $updateCalls[0][1][0] -ne '--update') { throw 'Old WSL was not updated exactly once' }
$failUpdate = $true; $versionAnswers.Enqueue([version]'2.0.0')
$failureText=''; try { Ensure-WorkshopWsl } catch { $failureText=$_.Exception.Message }
if ($failureText -notlike '*Close Docker Desktop*restart Windows*Administrator PowerShell*') { throw 'WSL MSI failure lacked actionable recovery guidance' }
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('hermes port ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixture | Out-Null
$busyPorts = @(9119)
function Get-NetTCPConnection { param($State,$LocalPort,$ErrorAction) if ($LocalPort -in $busyPorts) { return @{LocalAddress='0.0.0.0'} } }
try {
    if ((Get-WorkshopBackendPort $fixture) -ne 9120) { throw 'Occupied 9119 did not select a free port' }
    $busyPorts = @(9119,9120)
    if ((Get-WorkshopBackendPort $fixture) -ne 9120) { throw 'Rerun did not reuse saved port' }
    Save-Utf8 (Join-Path $fixture 'backend-port') 'invalid'
    Assert-Throws { Get-WorkshopBackendPort $fixture }
    Remove-Item (Join-Path $fixture 'backend-port')
    $busyPorts = @(9119..9139)
    Assert-Throws { Get-WorkshopBackendPort $fixture }
    $source=[IO.File]::ReadAllText((Join-Path $PSScriptRoot 'setup-windows.ps1'))
    if ($source -match 'Microsoft-Hyper-V-All|--backend=hyper-v|Linux Hermes URL|RemoteInstallerPath') { throw 'Old Hyper-V/remote architecture remains' }
    Write-Host 'Windows Home, local WSL2 Docker engine and backend port regression checks passed.'
} finally { Remove-Item -LiteralPath $fixture -Recurse -Force }
