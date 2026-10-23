# Hermes + Tailscale + Docker

macOS/Linux install native Hermes and source-built Desktop, with terminal commands running in Docker. Windows installs native Hermes Desktop and Tailscale, connecting to a Linux Hermes backend. Windows uses no WSL2, Hyper-V or local Docker. The Linux backend holds the workshop profile and credentials.

## Direct downloads

Choose your operating system. These links download a ZIP directly from this public repository; no GitHub sign-in or navigation is required.

| Platform | Download | After extracting, open the included folder and start |
| --- | --- | --- |
| macOS | [Download macOS ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-macos.zip) | Double-click `Install-Hermes.command` |
| Linux desktop | [Download Linux ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-linux.zip) | Open a terminal in the extracted folder; run `bash Install-Hermes.sh` |
| Native Windows | [Download Windows ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-windows.zip) | Double-click `Install-Hermes.cmd`; approve Administrator PowerShell under your normal account |

Extract each ZIP once. Keep its launcher and `scripts/` folder together. Downloading does not execute the installer. macOS may require Finder's Open action or `bash scripts/setup-macos-linux.sh` if download protections prevent double-click launch. [SHA-256 checksums](downloads/SHA256SUMS) are provided. [Full repository source ZIP](https://github.com/benczb/hermes-tailscale-docker/archive/refs/heads/main.zip) is also available.

This is guided setup: Tailscale/provider sign-in, OS approvals, Docker first-run acceptance and possible reboots require user input. Desktop is built from source; compiler/system dependencies can be required. Automated checks are not clean-machine installation evidence.

## Requirements

- macOS: Apple Silicon is the upstream primary target; Intel source builds are best effort. The installer can install missing Homebrew, Docker Desktop and Tailscale; finish Xcode Command Line Tools/OS dialogs if requested.
- Linux: 64-bit glibc desktop, systemd user services and Docker access for your user. apt-based distributions get basic dependencies; others need their prerequisites installed separately.
- Windows: supported Windows 10/11 desktop editions including Home, Pro, Enterprise and Education; x64 or ARM64, native 64-bit PowerShell and winget (or manually installed Tailscale). Requires a reachable Linux Hermes backend with dashboard authentication and Docker configured. Windows Server and older Windows are outside this installer path. No Windows virtualization or Docker engine is installed.

## macOS/Linux setup

1. Check/install prerequisites, verify Docker and run its `hello-world` test.
2. Install Tailscale if needed, request sign-in and obtain the machine's tailnet IPv4 address.
3. Install native Hermes and build Desktop, or reuse an existing Hermes command and build Desktop.
4. Install a new named `workshop` profile from the bundled template and run interactive Hermes setup. Existing profiles are preserved. Terminal backend is explicitly set to Docker after setup.
5. Ask for your dashboard username, password and confirmation. No default username. Passwords need at least 12 characters; hidden entry is the default and visible entry is optional. The session-signing secret is generated randomly.
6. Create a user-login backend: launchd (macOS) or systemd user service (Linux). It uses loopback and requires authentication through its declared Tailscale URL.
7. After backend/auth-gate readiness, configure Tailscale raw TCP 9119 to the local backend. Use `http://<server-tailscale-ip>:9119` from an authorized tailnet device.

On macOS/Linux, an existing service using local 9119 is left running. The installer selects a free local port from 9120–9139 and persists it. Remote Tailscale port 9119 stays the same. Override with `HERMES_BACKEND_PORT=9120` if desired. Windows does not open a local backend port.

An inherited `HERMES_HOME` is cleared only for the installer and backend processes. Saved settings and custom directories are not modified or migrated. Normal native workshop data lives under `~/.hermes/profiles/workshop` (macOS/Linux). Windows uses the remote Linux profile.

Docker isolates terminal commands, not every native tool, plugin or browser capability. Tailscale Serve is tailnet access, not all-interface/public-internet exposure. Tailnet policy must allow TCP 9119. Existing TCP 9119 Serve mapping is pointed to the workshop backend; unrelated Serve endpoints are not reset. Autostart is at user login; Docker must also be running.

## Windows setup: native Desktop, remote Linux sandbox

First run the Linux installer on your server. Keep its Tailscale URL and dashboard login ready. On Windows, double-click `Install-Hermes.cmd` and approve elevation using your normal account. Setup installs/signs into Tailscale, asks for the Linux URL (for example `http://100.x.y.z:9119`), checks that the remote backend requires authentication, installs native Hermes if missing and builds Desktop.

The generated `%LOCALAPPDATA%\HermesWorkshopInstaller\workshop\Open-Hermes-Desktop.ps1` launcher sets `HERMES_DESKTOP_REMOTE_URL`. Reopen Desktop through this launcher to retain the remote connection. In Desktop Settings > Gateways, sign in with the Linux dashboard credentials, save/reconnect and select `workshop`. Setup checks backend reachability/authentication requirements; successful user login and a real conversation still require verification in Desktop.

Windows does not install a local Docker engine, configure virtualization, create a backend service, set a local password, import a local workshop profile or configure Tailscale Serve. Those belong to the Linux server. Windows needs access to that server whenever using Hermes. The packaged SOUL/config files are for the server, not a second local profile.

## Reset a forgotten dashboard login

Run from the extracted repository folder. Normal reruns preserve the existing login.

macOS/Linux:

```bash
HERMES_RESET_DASHBOARD_AUTH=1 bash scripts/setup-macos-linux.sh
```

Windows Administrator PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -ResetDashboardAuth
```

On Windows, the reset command uses native OpenSSH to run the Linux installer on the selected backend. It asks for `linux-user@server` and defaults to `~/setup-hermes.sh` (the Bash slide's saved file). If you installed from a ZIP, pass `-RemoteInstallerPath '/home/your-user/path/to/scripts/setup-macos-linux.sh'`; optionally pass `-RemoteUrl` and `-SshTarget`. The SSH host must match the backend URL. Install Windows OpenSSH Client first if absent, or run the Bash reset directly on Linux.

Choose a new username and password on the server. Resetting also rotates the session-signing secret; sign in again afterward. Profile data and model keys remain. Credentials are stored locally in the profile `.env` and protected installer `dashboard-login.txt`; these are not encrypted vaults. Never commit runtime data.

## Workshop profile

`profiles/workshop/` contains:

- `SOUL.md`: the exact **Safe Agent Starter** used by the workshop safeguards slide (originally slide 67), including approval gates, secrets handling, verification and recovery. Personalize `[YOUR NAME]`.
- `config.yaml`: `terminal.backend: docker`, `terminal.cwd: /workspace` inside the container. This setting alone does not mount host folders.
- `distribution.yaml`: name/version/author and distribution-owned files.
- `.gitignore`: an authoring allowlist that excludes local credentials/runtime data.

No personal memories, API keys, model selection, custom skills, MCP connections, messaging tokens, cron jobs or Desktop theme are bundled. Existing installed SOUL customizations are not overwritten on rerun. To use your own trusted profile repository, set `HERMES_PROFILE_SOURCE` / `HERMES_PROFILE_NAME` on the Linux/macOS backend. Windows `-ProfileName` selects the expected remote profile; it does not create one. Apply custom profile sources on the backend, not Windows.

After changing authored profile files, run:

```bash
python3 scripts/sync-profile-template.py
python3 scripts/test-installers.py
python3 scripts/package-installer.py
```

Commit the regenerated `downloads/*.zip` and `downloads/SHA256SUMS` with installer changes; CI rejects stale packages. The workshop deck retains synchronized copies of these installers for its copy/paste setup slides. This repository is the public installer/download home. Full operating details are in [docs/installer-audit.md](docs/installer-audit.md).

## Existing Python bootstrap

The pre-existing `bootstrap.sh`, `bootstrap.ps1` and `bootstrap.py` remain available with their own separate behavior: a fresh dedicated home, no bundled persona, preinstalled prerequisites and explicit consent gates. They are not the workshop launcher path. See [the retained bootstrap guide](docs/bootstrap-guide.md) and [VERIFICATION.md](VERIFICATION.md). Existing bootstrap tests and provenance records are retained.
