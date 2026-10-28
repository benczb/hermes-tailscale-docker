# Starter Agent installer operating guide

Updated 24 October 2026. The copyable setup slides and packaged scripts use the same implementation.

## Architecture and support

Native Hermes and Desktop run locally on macOS, Linux and Windows; only terminal tool commands use Docker Linux containers. Tailscale provides private access to that local backend. No separate Linux machine is required. Docker Desktop on macOS manages an internal Linux VM; Docker Desktop on Windows uses WSL2 internally, including on Windows Home. Workshop commands run in native Terminal/PowerShell, not in a manually configured Linux distribution. Windows does not enable the full Hyper-V optional feature; WSL2 still requires firmware virtualization and Virtual Machine Platform.

macOS needs a desktop session, Homebrew/Xcode tools and Docker Desktop; missing Homebrew, Docker and Tailscale can be installed. Apple Silicon is the primary upstream target; Intel source builds are best effort. Linux needs 64-bit glibc, a graphical session, systemd user services and Docker access. apt distributions get basic dependencies; other distributions need prerequisites installed separately. Windows accepts supported Windows 10/11 desktop releases (build 19045 or newer), including Home/Pro/Enterprise/Education, on x64 or ARM64, using native 64-bit PowerShell and winget. Docker Desktop and its dependencies must support the machine. Windows Server and older Windows are outside this installer path. The source-built Desktop and its dependencies must support the machine; edition detection alone does not prove a clean-machine installation.

These are guided bootstrap packages, not offline or silent installers. Approve OS prompts, Tailscale sign-in, provider setup and Docker first-run dialogs where applicable. Upstream bootstrap scripts are pinned to `afe3cbd817b7f5655e4172b442acf6fa7c9bb55d`; the upstream stable channel still selects runtime dependencies.

## Download and launch

The public benczb/hermes-tailscale-docker repository provides direct macOS/Linux/Windows ZIPs under downloads/. GitHub sign-in is unnecessary. Extract once; keep launchers and scripts together. macOS: open Install-Hermes.command (Finder Open may be needed). Linux: bash Install-Hermes.sh. Windows: Install-Hermes.cmd, approving Administrator PowerShell for your normal account. The slide copy blocks save the complete scripts before executing them so prompts read the terminal.

An inherited HERMES_HOME is cleared only in installer/generated launcher processes. Saved shell or Windows environment settings and custom directories are unchanged. Existing usable Hermes commands are reused; otherwise the upstream installer creates the native layout. An existing folder alone is not evidence of a working command, and upstream installation may require repair. Old whole-agent Docker data is not migrated automatically.

## Local backend on each platform

Setup verifies Docker Linux containers with hello-world, installs/signs into Tailscale, installs Hermes if absent and builds Desktop. It installs missing named profile files early, preserving an existing profile and model keys. The interactive wizard runs only after Desktop/backend/forwarding readiness. It explicitly sets terminal.backend to docker and configures dashboard.public_url using the server Tailscale IPv4 and port 9119.

On first configuration, choose a username (no preset admin), hidden or visible password entry (hidden default), a password of at least 12 characters, and confirmation. Only the session-signing secret is randomly generated. Credentials are stored in the profile .env and protected installer dashboard-login.txt, not encrypted vaults or GitHub. Normal reruns preserve the login.

A per-profile isolated backend listens on loopback. Setup uses local 9119 if available; an existing listener is left running and a free port in 9120–9139 is selected and saved under ~/.hermes-workshop-installer/<profile>/backend-port. On Bash, HERMES_BACKEND_PORT can request an explicit port; an occupied requested port fails. Windows stores the port under %LOCALAPPDATA%\HermesWorkshopInstaller\<profile>\backend-port. Existing installer-managed Windows backends retain their previous port. Reruns reuse the saved port. Services use launchd (macOS), systemd user services (Linux) or a limited-privilege interactive Scheduled Task (Windows), starting at user login. Docker must also be running. Linux unattended operation can require administrator-configured user lingering.

Before forwarding, /api/status must report auth_required: true using the declared tailnet Host header. This checks the auth gate, not password login/model inference. Tailscale Serve external TCP 9119 forwards to the selected local port. One TCP 9119 mapping exists per machine; updating it points that endpoint to the workshop, preserving unrelated endpoints. Existing listener bind addresses/data are unchanged.

## Windows local setup (WSL2 internal Docker engine)

The installer accepts Home and other supported Windows 10/11 desktop editions; it no longer asks for a Linux backend URL. It enables only Microsoft-Windows-Subsystem-Linux and VirtualMachinePlatform if needed, then stops with reboot/rerun instructions. It reuses WSL 2.1.5 or newer, updates only missing/older WSL and selects version 2; no user Linux distribution or workshop commands inside WSL are required. Firmware virtualization must be available. It does not enable Microsoft-Hyper-V-All or the Windows Containers feature.

Missing Docker Desktop is installed with --backend=wsl-2; missing Tailscale is installed through winget. Complete Docker first-run dialogs, and use Settings > General > Use the WSL 2 based engine. Existing Docker settings are checked, not overwritten live. The engine must report Linux containers, Docker Desktop, a WSL2 kernel and a local named-pipe context. Docker hello-world verifies basic execution before Hermes is configured. A real agent terminal call is still needed to verify the entire sandbox integration.

The installer signs into Tailscale, installs native Hermes if absent, installs missing local named profile files, sets terminal.backend to docker, configures dashboard public URL/login and builds Desktop. Existing profile/SOUL/model settings and normal-rerun login are preserved. User/SYSTEM ACLs protect installer state. Inherited HERMES_HOME and HERMES_DESKTOP_REMOTE_URL are cleared for workshop processes only; saved user settings remain. Old remote-url.txt state is ignored.

A limited-privilege Scheduled Task launches an isolated local loopback backend at user login. Readiness must report authentication required before Tailscale forwarding is enabled. Open-Hermes-Desktop.ps1 in the installer state selects the chosen local profile and clears inherited remote URL/home selectors. It is launched after backend/forwarding readiness and can be reused later. The pending profile/model wizard opens last in a separate PowerShell window. No SSH server or separate Linux host is involved.

## Workshop preparation

Attendees can start directly with the installer: it checks and installs missing Docker/Tailscale where supported. To save workshop time, optionally install/open Docker Desktop (Linux may use Docker Engine), verify Docker works and sign into Tailscale beforehand. macOS may need Homebrew/Xcode tools; Windows may need WSL2 updates, firmware virtualization and a restart. OS approvals and provider/Tailscale sign-ins are interactive. This is guided installation, not an unattended one-click guarantee.

## Password reset

macOS/Linux, from the extracted installer directory:

```bash
HERMES_RESET_DASHBOARD_AUTH=1 bash scripts/setup-macos-linux.sh
```

Windows Administrator PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -ResetDashboardAuth
```

Windows resets the local workshop login with the same native PowerShell installer. It prompts for a username, hidden/visible password entry and confirmation; no default admin login is preset. No SSH or remote installer path is needed. The command reruns local prerequisite/service checks.

A reset replaces older admin logins and rotates the signing secret. Profile/model data remains; sign in again in Desktop. Standard launchers preserve existing credentials.

## Profile contents

profiles/starter-agent contains distribution.yaml (version 1.0.2), config.yaml (terminal.backend: docker; terminal.cwd: /workspace inside the container), the exact Safe Agent Starter SOUL.md from original slide 67 and an authoring .gitignore. Personalize [YOUR NAME]. No API keys, personal memories, model selection, custom skills, MCP connections, messaging tokens, cron jobs or theme are bundled. Base Hermes can ship its own standard skills. Existing SOUL customizations are preserved. Set HERMES_PROFILE_SOURCE/HERMES_PROFILE_NAME on the backend for a trusted custom distribution. On Windows, use -ProfileSource / -ProfileName to install a trusted custom distribution locally.

/workspace is the container working directory, not an automatic mount of all host files. Docker isolates terminal commands only; native tools, plugins and browser capabilities remain outside that sandbox. SOUL rules are behavioral guidance, not enforced isolation.

## Tailscale and verification

Tailscale Serve exposes the server tailnet address subject to tailnet policy; it does not publish every LAN interface or the internet. 0.0.0.0 is a bind address, not a destination. Open http://<server-tailscale-ip>:9119 from an authorized device. Raw TCP does not add HTTPS; the Tailscale tunnel encrypts transport. The existing long HTTPS endpoint remains usable only if separately configured.

On the macOS/Linux backend (substitute the saved local port if different):

```bash
tailscale status
tailscale serve status
tailscale ip -4
sudo tailscale serve --bg --tcp=9119 tcp://127.0.0.1:9119
tailscale serve status
```

On Windows, the installer configures the same Serve TCP mapping to its selected local backend port. Manual checks in native Administrator PowerShell use tailscale status, tailscale ip -4 and tailscale serve status. No broad LAN firewall rule is required. macOS may use /Applications/Tailscale.app/Contents/MacOS/Tailscale. Linux initial sign-in/Serve may need sudo or tailnet enablement approval.

Verify a real sign-in/conversation in Desktop on each platform, select the chosen local profile, make a terminal call and inspect local docker ps. Confirm reruns preserve profile/login and test login/service recovery. Automated mocked regression tests and syntax/package checks do not replace clean Windows Home/Pro, Linux and macOS installation testing.

State/logs: ~/.hermes-workshop-installer/<profile>/ on the backend; journalctl --user -u hermes-workshop-workshop on Linux; %LOCALAPPDATA%\HermesWorkshopInstaller\<profile>\ on Windows. Backend state uses umask 077; Windows client state uses user/SYSTEM ACLs. Never commit runtime .env/login files.

Remove just this forwarding with tailscale serve --tcp=9119 off on the server. Avoid tailscale serve reset because it removes unrelated endpoints. Disable the macOS launchd or Linux systemd user service to stop its backend, preserving profile data. On Windows, stop/unregister the HermesWorkshop-workshop Scheduled Task to disable its backend while keeping profile data.

Packages are deterministic: regenerate with python3 scripts/package-installer.py; --check rejects stale ZIPs/checksums. Desktop remote URL behavior follows upstream docs: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/desktop.md. Tailscale TCP reference: https://tailscale.com/docs/reference/tailscale-cli/serve.

## Profile wizard last and installation completion

All platform installers create profile files early, then configure dashboard credentials, build Desktop, start the isolated local backend, verify its auth gate and configure Tailscale TCP 9119 before interactive profile setup. They print/save installation-ready.txt with each infrastructure result. Model sign-in, real Desktop authentication and remote-device access remain separate checks.

Windows launches Desktop and opens Configure-Hermes-Profile.ps1 in a separate PowerShell window as its last step. Cancelling that window does not interrupt the completed app/backend installer. Failed/interrupted wizard calls retain setup-pending; successful completion or explicit -SkipProfileSetup deferral clears it. A finally block reapplies the Docker terminal backend and declared dashboard URL after wizard changes. The generated launcher can reopen the wizard later.

macOS/Linux run the wizard in a child shell after printing/saving readiness; its exit cleanup restores the sandbox and public URL. Set HERMES_SKIP_PROFILE_SETUP=1 to explicitly defer it. Existing completed profiles are preserved. Configure a model/provider afterward in Desktop or with hermes -p workshop model if deferred; app/backend readiness does not imply chat readiness. Existing Tailscale sign-ins are reused and Desktop builds automatically rather than asking for a separate install confirmation.

## Profile-name selection

Before profile creation and dashboard credentials, all platform installers prompt for a profile name (workshop initially, the last selected name on rerun). Windows -ProfileName and Bash HERMES_PROFILE_NAME explicitly select a profile without prompting. Names are portable 1–64 ASCII letters/digits, underscores and hyphens, with an alphanumeric first character; default and Windows device names are reserved. Invalid interactive input reprompts. Invalid explicit input stops before installation.

Prerequisite downloads and last-profile are kept in private _bootstrap state, separate from the chosen profile’s state. Selected profile files, credential markers, service/task names and generated launchers use the selected name. Existing SOUL/model/login data is preserved for an existing profile; a different name creates/selects another profile, not a rename. New profiles receive the bundled preconfigured SOUL.md. The final interactive wizard remains last, after Desktop/backend/forwarding readiness. One Tailscale TCP 9119 mapping per machine points to the selected profile backend.

## Terminal backend selection

The GUI collects Docker/local mode before installation and saves the non-secret choice for retries. The platform scripts accept `HERMES_TERMINAL_BACKEND=local` (Bash) or `-TerminalBackend local` (PowerShell), defaulting to Docker for existing launchers. Local mode skips all installer Docker operations and Windows WSL feature/update operations, configures `terminal.backend: local`, and retains that setting after profile setup. Tailscale and authenticated TCP forwarding use the same host-based flow in both modes. Existing Docker/WSL installations are not removed. The readiness report names the selected backend and does not claim a Docker smoke test in local mode.

Local terminal mode creates a `workspace` directory inside the selected Hermes profile and sets `terminal.cwd` to that host path. Docker mode uses `/workspace` inside the container. The final optional profile wizard restores both the selected backend and its workspace.

## Original Desktop handoff and configurable access port

GUI version 0.2 defaults to the original Nous Research bootstrap installer on Windows and Apple Silicon. The companion checks the original installer's standard helper/completion marker, built Desktop and native CLI before running in reuse-only mode. That mode refuses a missing runtime and does not call the upstream native installer or Desktop build command. Intel/Linux require an explicit source-build alternative; a detected bundled/Store app blocks this bootstrap integration instead of creating another runtime.

The access port is validated from 1024 to 65535, pre-filled as 9119, and labeled Default: 9119. It is passed to both platform scripts and used consistently for the Tailscale TCP rule, public origin, auth Host header, final wizard restoration and completion URL. A saved local backend port may differ and is reported separately. Docker remains only the terminal backend; the native agent and Desktop are never deployed as a Docker service.

## Graphical component recovery and gateway startup

Graphical installers initiate missing Docker/Tailscale installation (Windows winget;
macOS Homebrew casks), open their host apps and keep the current session alive
through first-run and connection checks. Automatic five-second checks apply to
readiness only. Failed installs require an explicit retry in the window. Account
sign-in, device/VPN approvals and required Windows restarts remain interactive.

Before starting the authenticated backend, its user-login launcher runs the
selected profile's `gateway ensure --json --timeout 60` and requires `state: ready`.
On Windows this runs in the limited-user task, avoiding an elevated gateway.
A fresh credential-free gateway-ready.json and the auth-gate check are required
before Tailscale forwarding/completion. Login restarts ensure the gateway again;
provider inference and peer-device access are separate checks.
