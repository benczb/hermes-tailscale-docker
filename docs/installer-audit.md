# Workshop installer operating guide

Updated 24 October 2026. The copyable setup slides and packaged scripts use the same implementation.

## Architecture and support

macOS/Linux run native Hermes and source-built Desktop; only terminal tool commands use Docker. Windows runs native Desktop and Tailscale, connecting to a Linux Hermes backend. **Windows uses no WSL2, Hyper-V or local Docker engine.** A separate Linux server is required for Windows users; it stores the workshop profile, model keys and dashboard login and runs the Docker terminal sandbox.

macOS needs a desktop session, Homebrew/Xcode tools and Docker Desktop; missing Homebrew, Docker and Tailscale can be installed. Apple Silicon is the primary upstream target; Intel source builds are best effort. Linux needs 64-bit glibc, a graphical session, systemd user services and Docker access. apt distributions get basic dependencies; other distributions need prerequisites installed separately. Windows accepts current supported Windows 10/11 desktop editions including Home/Pro/Enterprise/Education, on x64 or ARM64, using native 64-bit PowerShell. Windows Server and older Windows are outside this installer path. The source-built Desktop and its dependencies must support the machine; edition detection alone does not prove a clean-machine installation.

These are guided bootstrap packages, not offline or silent installers. Approve OS prompts, Tailscale sign-in, provider setup and Docker first-run dialogs where applicable. Upstream bootstrap scripts are pinned to `afe3cbd817b7f5655e4172b442acf6fa7c9bb55d`; the upstream stable channel still selects runtime dependencies.

## Download and launch

The public benczb/hermes-tailscale-docker repository provides direct macOS/Linux/Windows ZIPs under downloads/. GitHub sign-in is unnecessary. Extract once; keep launchers and scripts together. macOS: open Install-Hermes.command (Finder Open may be needed). Linux: bash Install-Hermes.sh. Windows: Install-Hermes.cmd, approving Administrator PowerShell for your normal account. The slide copy blocks save the complete scripts before executing them so prompts read the terminal.

An inherited HERMES_HOME is cleared only in installer/generated launcher processes. Saved shell or Windows environment settings and custom directories are unchanged. Existing usable Hermes commands are reused; otherwise the upstream installer creates the native layout. An existing folder alone is not evidence of a working command, and upstream installation may require repair. Old whole-agent Docker data is not migrated automatically.

## macOS/Linux backend

Setup verifies Docker Linux containers with hello-world, installs/signs into Tailscale, installs Hermes if absent and builds Desktop. It installs a missing named workshop profile and runs interactive setup, preserving an existing profile and model keys. It explicitly sets terminal.backend to docker and configures dashboard.public_url using the server Tailscale IPv4 and port 9119.

On first configuration, choose a username (no preset admin), hidden or visible password entry (hidden default), a password of at least 12 characters, and confirmation. Only the session-signing secret is randomly generated. Credentials are stored in the profile .env and protected installer dashboard-login.txt, not encrypted vaults or GitHub. Normal reruns preserve the login.

A per-profile isolated backend listens on loopback. Setup uses local 9119 if available; an existing listener is left running and a free port in 9120–9139 is selected and saved under ~/.hermes-workshop-installer/<profile>/backend-port. HERMES_BACKEND_PORT can request an explicit port; an occupied requested port fails. Reruns reuse the saved port. Services use launchd (macOS) or systemd user services (Linux), starting at user login. Docker must also be running. Linux unattended operation can require administrator-configured user lingering.

Before forwarding, /api/status must report auth_required: true using the declared tailnet Host header. This checks the auth gate, not password login/model inference. Tailscale Serve external TCP 9119 forwards to the selected local port. One TCP 9119 mapping exists per machine; updating it points that endpoint to the workshop, preserving unrelated endpoints. Existing listener bind addresses/data are unchanged.

## Windows remote Desktop client

Run the Linux installer first, then have its URL and dashboard login ready. Windows setup checks OS/architecture, installs Tailscale via winget if missing, signs in and asks for the Linux URL. It reuses a saved remote-url.txt on rerun. URLs must use http/https and a remote host, without embedded credentials, query or fragment. It checks the Linux /api/status auth gate before installing native Hermes and building Desktop.

The generated %LOCALAPPDATA%\HermesWorkshopInstaller\workshop\Open-Hermes-Desktop.ps1 launcher sets HERMES_DESKTOP_REMOTE_URL and clears inherited HERMES_HOME. Use that launcher to reopen the remote Desktop. In Settings > Gateways, sign in using Linux dashboard credentials, save/reconnect and select workshop. A successful authenticated Desktop connection is not claimed by the installer until the user completes it.

Windows does not import a local profile, set a local dashboard password, configure Serve, open a local backend port, register a backend service or install any virtualization/Docker component. Docker, custom profile sources and model configuration belong on Linux. Native Hermes is installed as the Desktop prerequisite; this does not mean a local Docker-backed agent is configured on Windows. Native OpenSSH is needed only for the optional remote reset.

## Password reset

macOS/Linux, from the extracted installer directory:

```bash
HERMES_RESET_DASHBOARD_AUTH=1 bash scripts/setup-macos-linux.sh
```

Windows Administrator PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -ResetDashboardAuth
```

Windows performs the reset on Linux via native ssh -t, asking for linux-user@host and using ~/setup-hermes.sh by default. That file is created by the Bash slide. For a ZIP installation, supply -RemoteInstallerPath with the absolute path to scripts/setup-macos-linux.sh on Linux. Optional -RemoteUrl and -SshTarget avoid prompts. The SSH host must match the backend URL to prevent resetting another machine. If OpenSSH is absent, install Windows OpenSSH Client or run the Bash reset directly on Linux. SSH credentials are entered in terminal prompts; dashboard credentials are chosen on the server. This reruns the backend installer, including its prerequisite/service checks.

A reset replaces older admin logins and rotates the signing secret. Profile/model data remains; sign in again in Desktop. Standard launchers preserve existing credentials.

## Profile contents

profiles/workshop contains distribution.yaml (version 1.0.1), config.yaml (terminal.backend: docker; terminal.cwd: /workspace inside the container), the exact Safe Agent Starter SOUL.md from original slide 67 and an authoring .gitignore. Personalize [YOUR NAME]. No API keys, personal memories, model selection, custom skills, MCP connections, messaging tokens, cron jobs or theme are bundled. Base Hermes can ship its own standard skills. Existing SOUL customizations are preserved. Set HERMES_PROFILE_SOURCE/HERMES_PROFILE_NAME on the backend for a trusted custom distribution. Windows -ProfileSource is rejected with guidance to apply it on Linux.

/workspace is the container working directory, not an automatic mount of all host files. Docker isolates terminal commands only; native tools, plugins and browser capabilities remain outside that sandbox. SOUL rules are behavioral guidance, not enforced isolation.

## Tailscale and verification

Tailscale Serve exposes the server tailnet address subject to tailnet policy; it does not publish every LAN interface or the internet. 0.0.0.0 is a bind address, not a destination. Open http://<server-tailscale-ip>:9119 from an authorized device. Raw TCP does not add HTTPS; the Tailscale tunnel encrypts transport. The existing long HTTPS endpoint remains usable only if separately configured.

On the Linux server (substitute the saved local port if different):

```bash
tailscale status
tailscale serve status
tailscale ip -4
sudo tailscale serve --bg --tcp=9119 tcp://127.0.0.1:9119
tailscale serve status
```

Windows connects to that server; do not configure a Windows Serve rule for this architecture. macOS may use /Applications/Tailscale.app/Contents/MacOS/Tailscale. Linux initial sign-in/Serve may need sudo or tailnet enablement approval.

Verify a real sign-in and conversation from Windows Desktop, select the remote profile, make a terminal call and inspect docker ps on Linux. Confirm reruns preserve profile/login and test login/service recovery. Automated mocked regression tests and syntax/package checks do not replace clean Windows Home/Pro, Linux and macOS installation testing.

State/logs: ~/.hermes-workshop-installer/<profile>/ on the backend; journalctl --user -u hermes-workshop-workshop on Linux; %LOCALAPPDATA%\HermesWorkshopInstaller\<profile>\ on Windows. Backend state uses umask 077; Windows client state uses user/SYSTEM ACLs. Never commit runtime .env/login files.

Remove just this forwarding with tailscale serve --tcp=9119 off on the server. Avoid tailscale serve reset because it removes unrelated endpoints. Disable the macOS launchd or Linux systemd user service to stop its backend, preserving profile data. Windows has no backend service to disable.

Packages are deterministic: regenerate with python3 scripts/package-installer.py; --check rejects stale ZIPs/checksums. Desktop remote URL behavior follows upstream docs: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/desktop.md. Tailscale TCP reference: https://tailscale.com/docs/reference/tailscale-cli/serve.
