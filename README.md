# Hermes + Tailscale + Docker

Native Hermes and source-built Desktop run on your own macOS, Linux or Windows computer. Terminal tool commands use a local Docker Linux-container sandbox, with Tailscale for private remote access. **No separate Linux machine is required.** On Windows Home/Pro/Enterprise/Education, Docker Desktop uses WSL2 internally; all workshop setup commands run in native PowerShell. On macOS, Docker Desktop manages its own internal Linux VM.

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
- Windows: supported Windows 10/11 desktop releases (build 19045 or newer), including Home, Pro, Enterprise and Education; x64 or ARM64, native 64-bit PowerShell, winget and firmware virtualization. Docker Desktop uses its internal WSL2 backend. The installer enables WSL/Virtual Machine Platform prerequisites, asks you to reboot if needed, and installs missing Docker Desktop and Tailscale. It does not enable the full Hyper-V role or require a user Linux distribution. Older Windows and Windows Server are outside this installer path; dependency support still applies.

## What the installer does

1. Check/install prerequisites, verify Docker and run its `hello-world` test.
2. Install Tailscale if needed, request sign-in and obtain the machine's tailnet IPv4 address.
3. Install native Hermes and build Desktop, or reuse an existing Hermes command and build Desktop.
4. Install a new named `workshop` profile from the bundled template and run interactive Hermes setup. Existing profiles are preserved. Terminal backend is explicitly set to Docker after setup.
5. Ask for your dashboard username, password and confirmation. No default username. Passwords need at least 12 characters; hidden entry is the default and visible entry is optional. The session-signing secret is generated randomly.
6. Create a user-login backend: launchd (macOS), systemd user service (Linux), or a limited-privilege Scheduled Task (Windows). It uses loopback and requires authentication through its declared Tailscale URL.
7. After backend/auth-gate readiness, configure Tailscale raw TCP 9119 to the local backend. Use `http://<server-tailscale-ip>:9119` from an authorized tailnet device.

An existing service using local 9119 is left running. The installer selects a free local port from 9120–9139 and persists it. Remote Tailscale port 9119 stays the same. On macOS/Linux, override with `HERMES_BACKEND_PORT=9120` if desired. Windows saves its selected port in `%LOCALAPPDATA%\HermesWorkshopInstaller\workshop\backend-port`.

An inherited `HERMES_HOME` is cleared only for the installer and backend processes. Saved settings and custom directories are not modified or migrated. Normal native workshop data lives under `~/.hermes/profiles/workshop` (macOS/Linux) or `%LOCALAPPDATA%\hermes\profiles\workshop` (Windows).

Docker isolates terminal commands, not every native tool, plugin or browser capability. Tailscale Serve is tailnet access, not all-interface/public-internet exposure. Tailnet policy must allow TCP 9119. Existing TCP 9119 Serve mapping is pointed to the workshop backend; unrelated Serve endpoints are not reset. Autostart is at user login; Docker must also be running.

## Attendees: prepare first or start with the installer?

You can start directly with the platform installer. It checks prerequisites and installs missing Docker/Tailscale where supported; you still complete OS approvals and sign-ins. For a smoother workshop, optionally install/open Docker Desktop (Linux: Docker Engine also works), confirm Docker is running and sign into Tailscale beforehand. macOS may need Homebrew and Xcode Command Line Tools. Windows may need firmware virtualization, WSL2 updates and a restart. Neither platform needs a separate Linux computer.

## Windows local Desktop

Double-click `Install-Hermes.cmd`; approve Administrator PowerShell using your normal account. If asked to restart after WSL2 prerequisites are enabled, restart and run the installer again. Compatible WSL 2.1.5 or newer is reused without an update. If a required WSL update fails with MSI 1603/service errors, close Docker Desktop, save WSL work, restart Windows and rerun as Administrator; check `wsl --version` and the local Temp `wsl-install-logs.txt` if it persists. In Docker Desktop, finish first-run setup and enable Settings > General > Use the WSL 2 based engine. The installer validates a local Docker Desktop WSL2 engine and runs hello-world; a remote Docker engine is rejected. It then installs native Hermes, the workshop profile, your dashboard login and a local backend service, and configures Tailscale TCP access.

There is no Linux URL prompt. Old saved remote URLs are ignored. The installer and generated `%LOCALAPPDATA%\HermesWorkshopInstaller\workshop\Open-Hermes-Desktop.ps1` launcher clear inherited `HERMES_DESKTOP_REMOTE_URL` only in their own processes so an old remote setting does not redirect the workshop Desktop. Use that launcher to reopen Desktop. Saved environment settings and custom directories remain unchanged. Select the workshop profile. The Docker engine and backend must run on this PC.

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

Choose a new username and password locally. Resetting also rotates the session-signing secret; sign in again afterward. Profile data and model keys remain. Credentials are stored locally in the profile `.env` and protected installer `dashboard-login.txt`; these are not encrypted vaults. Never commit runtime data.

## Workshop profile

`profiles/workshop/` contains:

- `SOUL.md`: the exact **Safe Agent Starter** used by the workshop safeguards slide (originally slide 67), including approval gates, secrets handling, verification and recovery. Personalize `[YOUR NAME]`.
- `config.yaml`: `terminal.backend: docker`, `terminal.cwd: /workspace` inside the container. This setting alone does not mount host folders.
- `distribution.yaml`: name/version/author and distribution-owned files.
- `.gitignore`: an authoring allowlist that excludes local credentials/runtime data.

No personal memories, API keys, model selection, custom skills, MCP connections, messaging tokens, cron jobs or Desktop theme are bundled. Existing installed SOUL customizations are not overwritten on rerun. To use your own trusted profile repository, set `HERMES_PROFILE_SOURCE` / `HERMES_PROFILE_NAME` on Bash or `-ProfileSource` / `-ProfileName` on Windows PowerShell.

After changing authored profile files, run:

```bash
python3 scripts/sync-profile-template.py
python3 scripts/test-installers.py
python3 scripts/package-installer.py
```

Commit the regenerated `downloads/*.zip` and `downloads/SHA256SUMS` with installer changes; CI rejects stale packages. The workshop deck retains synchronized copies of these installers for its copy/paste setup slides. This repository is the public installer/download home. Full operating details are in [docs/installer-audit.md](docs/installer-audit.md).

## Existing Python bootstrap

The pre-existing `bootstrap.sh`, `bootstrap.ps1` and `bootstrap.py` remain available with their own separate behavior: a fresh dedicated home, no bundled persona, preinstalled prerequisites and explicit consent gates. They are not the workshop launcher path. See [the retained bootstrap guide](docs/bootstrap-guide.md) and [VERIFICATION.md](VERIFICATION.md). Existing bootstrap tests and provenance records are retained.
