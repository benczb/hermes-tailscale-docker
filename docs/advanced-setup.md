# Detailed setup and recovery guide

A simple, guided setup that brings together **Hermes Desktop, optional Docker
terminal tools and Tailscale** on your own computer. Start with a command, ask
your agent to help, or use a downloadable package. The graphical wizard lets you
choose your profile name, dashboard login, terminal backend and private access
port **(Default: 9119)** before component installation.

The bundled **Starter Agent** template includes a preconfigured
[`SOUL.md` with safeguards](../profiles/starter-agent/SOUL.md). It asks your agent to
protect secrets, use only the access needed for a task, treat external content as
untrusted, request approval before consequential actions, and verify results
before reporting success. Personalize `[YOUR NAME]` in the file. These are
behavioral instructions for the agent, not a technical security boundary or a
guarantee that every action is safe. Existing customized profiles are preserved.

**Hermes Desktop and its agent stay native; only terminal commands optionally run
in Docker.** Tailscale runs on the host for private remote access. No separate
Linux computer or backend IP is required. You still complete sign-ins, OS approvals
and any required restart. This is a community companion and remains a preview;
platform limitations and prerequisites are described below.

In Docker mode on Windows Home/Pro/Enterprise/Education, Docker Desktop uses WSL2
internally; setup commands run in native PowerShell. Local-terminal mode skips
Docker and its Windows WSL2 prerequisites. On macOS, Docker Desktop manages its
own internal Linux VM when selected.

## Graphical companion: original Desktop installer first

The graphical companion defaults to the **original Nous Research Hermes Desktop installer** on supported platforms. It opens the official `Hermes-Setup.exe` (Windows) or `Hermes-Setup.dmg` (Apple Silicon) download, lets the user finish that installer and open Desktop, then checks its managed completion marker, built app and native CLI before applying the profile, terminal and Tailscale settings. It does not run a separate Hermes installation or Desktop build in this mode.

The official DMG bootstrap installer is Apple Silicon-only. Intel Mac and Linux users must explicitly choose the **Source build · advanced alternative** if they want the companion's source path. Intel source builds remain best effort. The original bootstrap installer itself can prepare/build dependencies; choosing it does not guarantee every dependency failure disappears.

This preview integrates the original bootstrap installer's standard native layout. A detected bundled/Store edition is stopped for explicit integration rather than converted into another runtime. Configure that installed app directly until its payload mapping is supported.

Recommended form defaults are preselected and labeled: original Desktop installer on supported platforms, Docker sandbox for **terminal commands only**, password hidden, preserve an existing login, and **Tailscale TCP port 9119 (Default: 9119)**. Profile name, dashboard username and password are personal entries; no admin credentials are preset.

The GUI is a preview; see [build and support details](../installer-ui/README.md). The ZIPs below are separate advanced script installers and retain the legacy source path by default. Use the GUI for the original-installer handoff, or explicitly enable reuse-only mode after completing the original installer.

## Start with a command instead of a manual download

The optional command launchers fetch the files and open the same graphical wizard.
This is a **source-launch preview**: it requires **Node.js 24+**, npm and potentially
Python/C++ build tools. It does not yet fetch a prebuilt, signed release. See the
[command setup guide](command-setup.md) for prerequisites and limitations.

macOS/Linux — paste into Terminal as your normal desktop user:

```bash
f=$(mktemp) && curl -fsSL https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/start-setup.sh -o "$f" && bash "$f"
```

Windows — paste into 64-bit Administrator Windows PowerShell:

```powershell
$f = Join-Path $env:TEMP ('hermes-start-' + [guid]::NewGuid().ToString('N') + '.ps1'); Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/start-setup.ps1 -OutFile $f -ErrorAction Stop; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $f
```

The launchers verify a fixed source archive, prepare GUI dependencies, then show
the form before component installation. Original Desktop installer platform
limits still apply; Intel Mac needs the explicit best-effort source alternative.
You still approve sign-ins, administrator prompts and any required reboots.

Or give your agent this instruction:

> Install Hermes Desktop using https://github.com/benczb/hermes-tailscale-docker.
> Read AGENTS.md, README.md and docs/command-setup.md. Check my computer's
> prerequisites and launch the graphical setup wizard. Keep Hermes and its agent
> native; use Docker only for terminal commands if I select it. Let me enter
> credentials and approve sign-ins. Preserve existing profiles and logins, and
> report the setup checks and anything still pending.

See the [agent installation guide](agent-install.md). The agent needs command
access to your computer; an unconnected cloud agent cannot install locally.

## Direct downloads

Choose your operating system. These links download a ZIP directly from this public repository; no GitHub sign-in or navigation is required.

| Platform | Download | After extracting, open the included folder and start |
| --- | --- | --- |
| macOS | [Download macOS ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-macos.zip) | Double-click `Install-Hermes.command` |
| Linux desktop | [Download Linux ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-linux.zip) | Open a terminal in the extracted folder; run `bash Install-Hermes.sh` |
| Native Windows | [Download Windows ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-windows.zip) | Double-click `Install-Hermes.cmd`; approve Administrator PowerShell under your normal account |

Extract each ZIP once. Keep its launcher and `scripts/` folder together. Downloading does not execute the installer. macOS may require Finder's Open action or `bash scripts/setup-macos-linux.sh` if download protections prevent double-click launch. [SHA-256 checksums](../downloads/SHA256SUMS) are provided. [Full repository source ZIP](https://github.com/benczb/hermes-tailscale-docker/archive/refs/heads/main.zip) is also available.

This is guided setup: Tailscale/provider sign-in, OS approvals, Docker first-run acceptance and possible reboots require user input. Desktop is built from source; compiler/system dependencies can be required. Automated checks are not clean-machine installation evidence.

## Choose the terminal backend

The graphical installer offers **Docker sandbox** (default) or **Local terminal** before installation. Docker mode installs/checks Docker and runs a test container. Local mode configures `terminal.backend: local` and skips Docker installation, startup and checks; on Windows it also skips WSL updates and virtualization-feature setup. Existing Docker/WSL installations are left in place. Local terminal commands run directly on your computer with your account's file access.

For the script installer, choose local mode explicitly:

```sh
HERMES_TERMINAL_BACKEND=local bash scripts/setup-macos-linux.sh
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -TerminalBackend local
```

Use `docker` instead of `local` for sandbox mode. Both modes install/check native Hermes Desktop, keep Tailscale on the host and configure private TCP 9119 access. The selected terminal backend is restored after the final optional profile wizard.

## Requirements

- macOS: Apple Silicon is the upstream primary target; Intel source builds are best effort. The installer can install missing Homebrew and Tailscale, plus Docker Desktop when selected; finish Xcode Command Line Tools/OS dialogs if requested.
- Linux: 64-bit glibc desktop, systemd user services; Docker access for your user is required in Docker mode. apt-based distributions get basic dependencies; others need their prerequisites installed separately.
- Windows: supported Windows 10/11 desktop releases (build 19045 or newer), including Home, Pro, Enterprise and Education; x64 or ARM64, native 64-bit PowerShell, winget. Docker mode additionally needs firmware virtualization and uses Docker Desktop’s internal WSL2 backend. In that mode the installer enables WSL/Virtual Machine Platform prerequisites, asks you to reboot if needed, and installs missing Docker Desktop. Both modes install missing Tailscale. It does not enable the full Hyper-V role or require a user Linux distribution. Older Windows and Windows Server are outside this installer path; dependency support still applies.

## What the installer does

1. Check/install prerequisites, verify Docker and run its `hello-world` test only in Docker mode.
2. Install Tailscale if needed, request sign-in and obtain the machine's tailnet IPv4 address.
3. Install native Hermes and build Desktop, or reuse an existing Hermes command and build Desktop.
4. Ask for your profile name and install missing profile files from the bundled template, including your preconfigured SOUL.md. Preserve existing profiles. Configure the selected terminal backend before starting services; the interactive profile/model wizard runs last.
5. Ask for your dashboard username, password and confirmation. No default username. Passwords need at least 12 characters; hidden entry is the default and visible entry is optional. The session-signing secret is generated randomly.
6. Create a user-login backend: launchd (macOS), systemd user service (Linux), or a limited-privilege Scheduled Task (Windows). It uses loopback and requires authentication through its declared Tailscale URL.
7. After backend/auth-gate readiness, configure Tailscale raw TCP 9119 to the local backend. Save and print `installation-ready.txt` with separate Docker, Tailscale, Desktop, backend and forwarding results.
8. Run interactive profile/model setup **last** if pending. Windows opens it in a separate PowerShell window; macOS/Linux run it after the readiness summary. Verify the actual Desktop login, model and remote access afterward.

An existing service using local 9119 is left running. The installer selects a free local port from 9120–9139 and persists it. Remote Tailscale port 9119 stays the same. On macOS/Linux, override with `HERMES_BACKEND_PORT=9120` if desired. Windows saves its selected port in `%LOCALAPPDATA%\HermesWorkshopInstaller\<your-profile-name>\backend-port`.

An inherited `HERMES_HOME` is cleared only for the installer and backend processes. Saved settings and custom directories are not modified or migrated. Native profile data lives under `~/.hermes/profiles/<your-profile-name>` (macOS/Linux) or `%LOCALAPPDATA%\hermes\profiles\<your-profile-name>` (Windows). Existing profiles and installer state directories keep their original names.

In Docker mode, Docker isolates terminal commands, not every native tool, plugin or browser capability. Tailscale Serve is tailnet access, not all-interface/public-internet exposure. Tailnet policy must allow TCP 9119. Existing TCP 9119 Serve mapping is pointed to the selected profile backend; unrelated Serve endpoints are not reset. Autostart is at user login; Docker must also be running when that backend is selected.

## Attendees: prepare first or start with the installer?

You can start directly with the platform installer. It checks prerequisites and installs missing Docker/Tailscale where supported; you still complete OS approvals and sign-ins. For a smoother workshop, optionally install/open Docker Desktop (Linux: Docker Engine also works), confirm Docker is running and sign into Tailscale beforehand. macOS may need Homebrew and Xcode Command Line Tools. Windows Docker mode may need firmware virtualization, WSL2 updates and a restart; local-terminal mode skips those steps. Neither platform needs a separate Linux computer.

## Windows local Desktop

Double-click `Install-Hermes.cmd`; approve Administrator PowerShell using your normal account. If asked to restart after WSL2 prerequisites are enabled, restart and run the installer again. Compatible WSL 2.1.5 or newer is reused without an update. If a required WSL update fails with MSI 1603/service errors, close Docker Desktop, save WSL work, restart Windows and rerun as Administrator; check `wsl --version` and the local Temp `wsl-install-logs.txt` if it persists. In Docker Desktop, finish first-run setup and enable Settings > General > Use the WSL 2 based engine. The installer validates a local Docker Desktop WSL2 engine and runs hello-world; a remote Docker engine is rejected. It then installs native Hermes, the Starter Agent template, your dashboard login and a local backend service, and configures Tailscale TCP access.

There is no Linux URL prompt. Old saved remote URLs are ignored. The installer and generated `%LOCALAPPDATA%\HermesWorkshopInstaller\<your-profile-name>\Open-Hermes-Desktop.ps1` launcher clear inherited `HERMES_DESKTOP_REMOTE_URL` only in their own processes so an old remote setting does not redirect Desktop. Use that launcher to reopen Desktop. Saved environment settings and custom directories remain unchanged. Select your chosen profile. The backend, and Docker engine when selected, run on this PC.

## Choose your own profile name

After prerequisite checks and before creating the profile/dashboard login, the installer asks **Hermes profile name [starter-agent]**. Enter a name such as `Hamburger`, `personal` or `Ben_01`. Press Enter to accept the shown default; reruns remember your last selection. Your chosen name is used for native profile data, private installer state, backend services, Desktop and the final wizard. Every new profile receives the same bundled preconfigured SOUL.md.

Names use 1–64 letters/digits, `_` or `-`, starting with a letter/digit. `default`, paths, spaces and reserved Windows device names are rejected. Choosing an existing name preserves its SOUL.md, model settings and normal-rerun login. Choosing a different name creates/selects another profile; it does not rename or delete the old one. Each machine still has one Tailscale TCP 9119 mapping, pointing to the selected profile’s backend.

For scripted installs, `HERMES_PROFILE_NAME=personal bash scripts/setup-macos-linux.sh` or `-ProfileName personal` on Windows bypasses the name prompt. Bootstrap downloads and the saved name are stored separately under the private installer `_bootstrap` directory; per-profile state remains under its chosen name. Recovery commands also ask which profile to use unless an explicit name is supplied.

## Profile/model setup runs last

Download/extract the current package and use its launcher. The installer now completes the selected terminal/Tailscale checks, the native Hermes/profile files, dashboard credentials, Desktop build, backend readiness and TCP forwarding before opening the interactive profile/model wizard. Creating the profile files early is required for the backend; this is separate from the interactive wizard.

Look for **INSTALLATION CHECKS COMPLETE** and `installation-ready.txt` in the installer state folder. It reports exactly what was checked: the selected terminal backend (Docker hello-world only in Docker mode), Tailscale connection/IP, Desktop build, the local backend auth gate and configured TCP 9119 forwarding. It does not prove a real model conversation or access from another tailnet device.

Windows opens Desktop, prints/saves readiness and then opens the pending profile wizard in a separate PowerShell window. Close/defer that wizard if you prefer to configure a model in Desktop later. Reopen it through `Configure-Hermes-Profile.ps1` in the same state folder. On macOS/Linux, the wizard runs in the terminal after the same infrastructure summary. Successful/failed wizard cleanup restores the selected terminal backend and declared dashboard URL.

To explicitly defer a pending wizard when rerunning Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -SkipProfileSetup
```

macOS/Linux can use `HERMES_SKIP_PROFILE_SETUP=1 bash scripts/setup-macos-linux.sh`. Deferral preserves the installed profile and keys. Configure a model in Desktop or with `hermes -p starter-agent model`; without a provider Hermes cannot chat. On Windows the profile wizard's own “Setup Complete” message is separate from the earlier installer readiness summary.

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

## Starter Agent profile

`profiles/starter-agent/` is the bundled **Starter Agent** template. Attendees
choose their own installed profile name; existing profile folders are not renamed.
The template contains:

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

Commit the regenerated `downloads/*.zip` and `downloads/SHA256SUMS` with installer changes; CI rejects stale packages. The workshop deck retains synchronized copies of these installers for its copy/paste setup slides. This repository is the public installer/download home. Full operating details are in [docs/installer-audit.md](installer-audit.md).

## Existing Python bootstrap

The pre-existing `bootstrap.sh`, `bootstrap.ps1` and `bootstrap.py` remain available with their own separate behavior: a fresh dedicated home, no bundled persona, preinstalled prerequisites and explicit consent gates. They are not the workshop launcher path. See [the retained bootstrap guide](bootstrap-guide.md) and [VERIFICATION.md](../VERIFICATION.md). Existing bootstrap tests and provenance records are retained.

Local terminal mode creates a `workspace` directory inside the selected Hermes profile and sets `terminal.cwd` to that host path. Docker mode uses `/workspace` inside the container. The final optional profile wizard restores both the selected backend and its workspace.

## Custom private access port

The GUI's Tailscale TCP port field is pre-filled with **9119** and labeled **(Default: 9119)**. Choose a port from 1024 to 65535. The selected port is used in the Serve rule, declared dashboard origin, auth checks and printed tailnet URL. A saved local backend port is reused; a fresh backend tries the chosen port, then an available local fallback. Local and tailnet ports are shown separately in the completion report.

Script equivalents: `HERMES_TAILNET_PORT=9234 bash scripts/setup-macos-linux.sh` or `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -TailnetPort 9234`. To configure an installation completed by the original Desktop installer without source installation/build, add `HERMES_USE_EXISTING_DESKTOP=1` for Bash or `-UseExistingDesktop` for PowerShell. Finish the original installer first. Changing ports does not reset unrelated Tailscale Serve rules.

## Community and maintenance

This is a community companion, not an official Nous Research distribution.
Contributions are welcome under the [MIT license](../LICENSE), with existing
copyright and dependency notices preserved.

- [Contribute and run checks](../CONTRIBUTING.md)
- [Code of conduct](../CODE_OF_CONDUCT.md)
- [Report vulnerabilities privately](../SECURITY.md)
- [Get help](../SUPPORT.md)
- [Changelog](../CHANGELOG.md) and [release checklist](releasing.md)

The project is maintained by [@benczb](https://github.com/benczb). There are no
published GitHub releases yet; current CI packages and command-based source
launches are previews. Policies here do not enable GitHub repository settings
such as private vulnerability reporting or branch protection.
