# Launch the graphical companion from a verified, fixed source snapshot.
# Run in Administrator Windows PowerShell under your normal user account.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Open Windows PowerShell as Administrator under your normal account, then run the command again.'
}
if (-not [Environment]::Is64BitProcess) { throw 'Use 64-bit Windows PowerShell.' }
if (-not (Get-Command node.exe -ErrorAction SilentlyContinue) -or -not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw 'Install Node.js 24 LTS from https://nodejs.org, reopen Administrator PowerShell, and retry.'
}
& node.exe -e 'if (Number(process.versions.node.split(".")[0]) < 24) process.exit(1)'
if ($LASTEXITCODE -ne 0) { throw 'Node.js 24 or newer is required. Install Node.js 24 LTS, then retry.' }
$revision = '69ff5a45e8181be6c6ceaa4470fb4559ec1344b6'
$expected = 'bb36590787aed474f4e75de4f2b4f6ca097867e6eb58d4b2f02b8cd1d8714b90'
$work = Join-Path ([IO.Path]::GetTempPath()) ('hermes-companion-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work | Out-Null
$archive = Join-Path $work 'source.zip'
Write-Host 'Starting Hermes Setup Companion preview from a fixed source revision.'
Write-Host 'This downloads source and npm dependencies and may compile native GUI helpers.'
Write-Host 'Hermes/component installation starts only after you review settings in the wizard.'
Write-Host "Setup files: $work"
Write-Host 'If dependency preparation fails, install Python 3 and Visual Studio Build Tools with Desktop development with C++, then retry.'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
try {
    Invoke-WebRequest -UseBasicParsing -Uri "https://codeload.github.com/benczb/hermes-tailscale-docker/zip/$revision" -OutFile $archive
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Source checksum mismatch. Nothing from the archive was executed. Download a fresh launcher or report the mismatch.'
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $work
    Push-Location (Join-Path $work "hermes-tailscale-docker-$revision\installer-ui")
    try {
        & npm.cmd ci --include=dev
        if ($LASTEXITCODE -ne 0) { throw "GUI dependency preparation failed. Check build tools. Files are retained at $work." }
        & npm.cmd start
        if ($LASTEXITCODE -ne 0) { throw "Setup window stopped (exit $LASTEXITCODE). Files are retained at $work." }
    }
    finally { Pop-Location }
}
finally { Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue }
