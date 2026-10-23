# Native Windows Desktop client + Tailscale. No WSL2, Hyper-V or local Docker.
[CmdletBinding()]
param(
    [string]$ProfileName = 'workshop',
    [string]$ProfileSource = '',
    [switch]$ResetDashboardAuth,
    [string]$RemoteUrl = '',
    [string]$SshTarget = '',
    [string]$RemoteInstallerPath = '~/setup-hermes.sh'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Invoke-Checked {
    param([string]$File, [string[]]$Arguments)
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$File failed (exit $LASTEXITCODE). Fix the error and rerun." }
}
function Save-Utf8 {
    param([string]$Path, [string]$Text)
    [IO.File]::WriteAllText($Path, $Text, (New-Object Text.UTF8Encoding($false)))
}
function Assert-WorkshopWindowsHost {
    param([string]$Caption, [string]$Version, [int]$ProductType, [string]$Architecture)
    Write-Host "Detected Windows: $Caption; version $Version; ProductType $ProductType; process architecture $Architecture"
    if ($ProductType -ne 1 -or ([version]$Version).Major -ne 10) {
        throw 'Use a supported Windows 10/11 desktop edition. Older Windows and Windows Server are outside this installer path.'
    }
    if ($Architecture -notin @('AMD64', 'ARM64')) { throw 'Use 64-bit PowerShell on supported x64 or ARM64 Windows.' }
}
function Get-WorkshopRemoteUri {
    param([string]$Value)
    $uri = $null
    if (-not [Uri]::TryCreate($Value, [UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -notin @('http', 'https')) {
        throw 'Use a full Linux Hermes URL such as http://100.x.y.z:9119 or https://host.tailnet.ts.net.'
    }
    $address = $null
    $isAddress = [Net.IPAddress]::TryParse($uri.DnsSafeHost.Trim([char[]]'[]'), [ref]$address)
    $isUnspecified = $isAddress -and ($address.Equals([Net.IPAddress]::Any) -or $address.Equals([Net.IPAddress]::IPv6Any))
    if ($uri.IsLoopback -or $isUnspecified -or $uri.UserInfo -or $uri.Query -or $uri.Fragment) {
        throw 'Use the Linux server address, with no embedded login, query or fragment. Enter credentials only in Desktop.'
    }
    return $uri.AbsoluteUri.TrimEnd('/')
}
function Get-WorkshopRemoteUrl {
    param([string]$RequestedUrl, [string]$StateDirectory)
    $savedUrl = Join-Path $StateDirectory 'remote-url.txt'
    if (-not $RequestedUrl -and (Test-Path $savedUrl)) { $RequestedUrl = (Get-Content $savedUrl -Raw).Trim() }
    if ($RequestedUrl) { return Get-WorkshopRemoteUri $RequestedUrl }
    do {
        $candidate = Read-Host 'Linux Hermes URL (for example http://100.x.y.z:9119)'
        try { return Get-WorkshopRemoteUri $candidate }
        catch { Write-Host $_.Exception.Message }
    } while ($true)
}
function Test-WorkshopRemoteBackend {
    param([string]$BackendUrl)
    try { $status = Invoke-RestMethod -Uri ($BackendUrl + '/api/status') -TimeoutSec 10 }
    catch { throw "Cannot reach $BackendUrl. Start the Linux Hermes backend and Tailscale forwarding, check tailnet access, then rerun. $($_.Exception.Message)" }
    if ($status.auth_required -ne $true) { throw 'The Linux backend did not report authentication enabled. Configure its dashboard login/public URL on Linux first.' }
}
function Reset-WorkshopRemoteLogin {
    param([string]$BackendUrl, [string]$Target, [string]$InstallerPath)
    if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) { throw 'Native OpenSSH Client is required for remote password reset. Install it through Windows Optional Features, or reset directly on Linux.' }
    $hostName = ([Uri]$BackendUrl).Host
    if (-not $Target) { $Target = Read-Host "SSH login for this Linux server (linux-user@$hostName)" }
    if ($Target -notmatch '^[a-zA-Z_][a-zA-Z0-9_-]*@[a-zA-Z0-9][a-zA-Z0-9._-]*$') { throw 'Enter a Linux SSH login in user@hostname form.' }
    if ($Target.Split('@')[1] -ine $hostName) { throw 'The SSH host must match the selected backend URL host to avoid resetting a different server.' }
    if (-not $InstallerPath -or $InstallerPath -match '[\r\n]' -or ($InstallerPath -notmatch '^~/' -and $InstallerPath -notmatch '^/')) {
        throw 'RemoteInstallerPath must be an absolute Linux path or begin with ~/.'
    }
    # Quote a literal shell argument; never turn an installer path into shell instructions.
    $quoteEscape = "'" + [char]34 + "'" + [char]34 + "'"
    if ($InstallerPath.StartsWith('~/')) {
        $remotePath = '"$HOME"/' + "'" + $InstallerPath.Substring(2).Replace("'", $quoteEscape) + "'"
    } else { $remotePath = "'" + $InstallerPath.Replace("'", $quoteEscape) + "'" }
    $command = 'HERMES_RESET_DASHBOARD_AUTH=1 bash ' + $remotePath
    Write-Host "Reset runs on $Target using $InstallerPath. Enter SSH/server credentials privately in the terminal prompts."
    Invoke-Checked ssh @('-t', $Target, $command)
    Test-WorkshopRemoteBackend $BackendUrl
    Write-Host 'Linux reset command completed. Sign in again in Desktop using the new dashboard login.'
}
function Complete-WorkshopRemoteSetup {
    param([string]$HermesCommand, [string]$StateDirectory, [string]$BackendUrl, [string]$SelectedProfile)
    Test-WorkshopRemoteBackend $BackendUrl
    Invoke-Checked $HermesCommand @('desktop', '--build-only')
    Save-Utf8 (Join-Path $StateDirectory 'remote-url.txt') $BackendUrl
    $desktopLauncher = Join-Path $StateDirectory 'Open-Hermes-Desktop.ps1'
    $escapedHermes = $HermesCommand.Replace("'", "''")
    $escapedUrl = $BackendUrl.Replace("'", "''")
    Save-Utf8 $desktopLauncher "Remove-Item Env:HERMES_HOME -ErrorAction SilentlyContinue`r`n`$env:PATH = '$($env:PATH.Replace("'", "''"))'`r`n`$env:HERMES_DESKTOP_REMOTE_URL = '$escapedUrl'`r`n& '$escapedHermes' desktop`r`nexit `$LASTEXITCODE`r`n"
    $notes = "Remote Hermes: $BackendUrl`r`nOpen Desktop using: $desktopLauncher`r`nIn Settings > Gateways, sign in with the Linux backend's dashboard login, save/reconnect and select profile $SelectedProfile.`r`nThe workshop profile, model keys and Docker terminal live on Linux. This Windows client does not configure a local Docker engine, virtualization feature, backend service or Serve rule.`r`n"
    Save-Utf8 (Join-Path $StateDirectory 'remote-connection.txt') $notes
    Write-Host $notes
    Write-Host 'Desktop is installed and its launcher selects the remote URL. Complete sign-in in Desktop; the authenticated Desktop connection is not yet verified.'
    Start-Process powershell.exe -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $desktopLauncher + '"')
}
try {
    if ($env:OS -ne 'Windows_NT') { throw 'Run this in native Windows PowerShell.' }
    if ($ProfileName -notmatch '^[a-zA-Z0-9_-]+$' -or $ProfileName -eq 'default') { throw 'Choose a named profile using letters, digits, _ or -.' }
    if ($ProfileSource) { throw 'Install the profile source on the Linux backend. Windows uses its remote workshop profile, not a local copy.' }
    if ($env:HERMES_HOME) {
        Write-Host 'Using the standard native Hermes layout for this installer; your saved HERMES_HOME setting is unchanged.'
        Remove-Item Env:HERMES_HOME -ErrorAction Stop
    }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Open PowerShell with Run as Administrator, using your normal Windows account, then rerun.'
    }
    $os = Get-CimInstance Win32_OperatingSystem
    Assert-WorkshopWindowsHost -Caption $os.Caption -Version $os.Version -ProductType $os.ProductType -Architecture $env:PROCESSOR_ARCHITECTURE
    Write-Host 'Windows installs a native Desktop client. The Hermes backend and Docker sandbox run on Linux. No WSL2 or Hyper-V is used.'
    $state = Join-Path $env:LOCALAPPDATA "HermesWorkshopInstaller\$ProfileName"
    New-Item -ItemType Directory -Force -Path $state | Out-Null
    $acl = New-Object Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($identity.User, (New-Object Security.Principal.SecurityIdentifier('S-1-5-18')))) {
        $rule = New-Object Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -Path $state -AclObject $acl
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $env:PATH = "$env:LOCALAPPDATA\hermes\bin;$env:ProgramFiles\Tailscale;$env:PATH"
    if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Install Microsoft App Installer (winget), or Tailscale manually, then rerun.' }
        Invoke-Checked winget @('install', '--id', 'Tailscale.Tailscale', '--exact', '--accept-package-agreements', '--accept-source-agreements')
    }
    & tailscale status *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Complete Tailscale sign-in in your browser.'
        Invoke-Checked tailscale @('up')
    }
    $tailIp = (& tailscale ip -4 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $tailIp -notmatch '^100\.\d+\.\d+\.\d+$') { throw 'No Tailscale IPv4 address. Complete sign-in, then rerun.' }
    $RemoteUrl = Get-WorkshopRemoteUrl -RequestedUrl $RemoteUrl -StateDirectory $state
    if ($ResetDashboardAuth) {
        Reset-WorkshopRemoteLogin -BackendUrl $RemoteUrl -Target $SshTarget -InstallerPath $RemoteInstallerPath
        return
    }
    Test-WorkshopRemoteBackend $RemoteUrl
    if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
        $installer = Join-Path $state 'hermes-install.ps1'
        Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/NousResearch/hermes-agent/afe3cbd817b7f5655e4172b442acf6fa7c9bb55d/scripts/install.ps1' -OutFile $installer
        Invoke-Checked powershell.exe @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $installer, '-NonInteractive', '-IncludeDesktop')
    }
    $hermes = (Get-Command hermes -ErrorAction Stop).Source
    Complete-WorkshopRemoteSetup -HermesCommand $hermes -StateDirectory $state -BackendUrl $RemoteUrl -SelectedProfile $ProfileName
} catch {
    Write-Error "Setup stopped: $($_.Exception.Message)" -ErrorAction Continue
    exit 1
}
