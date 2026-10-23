# Setup slides: installer audit and operating guide

Audited 23 October 2026 against the checked-in scripts and current upstream documentation. These scripts replace the old whole-agent Docker installation with **native Hermes + source-built Desktop, with the terminal tool using Docker**. They do not migrate the old `~/hermes/data` container installation.

## Supported setup

| Host | Installer | Requirements and boundaries |
| --- | --- | --- |
| macOS | `scripts/setup-macos-linux.sh` | Desktop session, Homebrew, Xcode Command Line Tools, Docker Desktop, Tailscale. Missing Homebrew/Docker/Tailscale are installed. Apple Silicon is upstream's primary macOS target; Intel source builds are best effort. Approve OS dialogs. |
| Linux | `scripts/setup-macos-linux.sh` | 64-bit glibc desktop with systemd user services. apt-based desktops get basic compiler/GTK/NSS dependencies and Docker if missing. Package availability varies by distro/version; other distros need their Docker/build prerequisites installed first. A graphical session and Electron system libraries are required for Desktop. |
| Native Windows | `scripts/setup-windows.ps1` | x64 Windows 10/11 Pro, Enterprise or Education supported by Docker Desktop; hardware virtualization; Hyper-V; Linux containers. Run 64-bit PowerShell 5.1+ as Administrator using the same account that will run Hermes. An inherited `HERMES_HOME` is cleared only in the installer and generated backend processes; saved User/Machine environment settings and the custom home directory are preserved. winget/App Installer must exist. Hyper-V/Containers changes require a reboot and rerun. Existing WSL2 Docker backends are rejected. |

**Windows Home, Windows Server and Windows ARM are excluded from this no-WSL2 Docker path.** Native Hermes itself supports more Windows configurations; that does not mean Docker Desktop supports Hyper-V Linux containers on them. Supported Windows versions also depend on Docker's current lifecycle requirements.

This is a single entry point with guided setup, not a silent install: Tailscale authentication, VPN/extension approval, provider login/API keys, Docker first-run acceptance and possible reboots require the user. The installers build Desktop from source using upstream's supported workflow. They do not install a signed MSIX/DMG bundle. A source build may need extra compiler/system packages; the script stops on failure rather than claiming completion.

## Existing HERMES_HOME and fresh installs

Both installers and their generated backend launchers now ignore inherited `HERMES_HOME` **only within their own processes**. Saved shell startup files and Windows User/Machine environment settings are not edited, and the custom data directory is not moved, deleted or migrated. The workshop uses `~/.hermes` on macOS/Linux or `%LOCALAPPDATA%\hermes` on Windows. Other shells/apps can continue using a saved custom home. Run workshop CLI commands without that custom selector (for example `env -u HERMES_HOME hermes -p workshop chat` on macOS/Linux).

If there is no native Hermes folder, the installer checks whether `hermes` is available on PATH. If absent, it runs the upstream native installer, which creates the normal code/data/launcher layout and builds Desktop. If a usable Hermes command already exists, it reuses that command rather than deciding solely from folder existence. It then installs the named `workshop` profile if missing and runs its interactive setup. An existing folder without a usable command is not treated as a working installation: the upstream installer handles that existing directory and may require repair.

An existing `workshop` profile keeps its persona, skills and model credentials on rerun, but the installer explicitly sets its terminal backend to Docker and updates its public URL. The first installer-managed run on that profile also sets dashboard credentials; later runs preserve them using the installer state marker. No old container data is imported automatically.

## Run

Download the macOS, Linux or Windows ZIP directly from the public `benczb/hermes-tailscale-docker` repository and extract it once. No GitHub sign-in is required. For the extracted installer bundle, double-click `Install-Hermes.command` on macOS or `Install-Hermes.cmd` on Windows. Windows opens a UAC prompt and a PowerShell window; approve elevation for the same account that will use Hermes. On Linux, run `bash Install-Hermes.sh` in a desktop terminal. OS download protections may require opening the macOS launcher through Finder's Open action. These launchers call the same audited scripts below.

On macOS/Linux, download the repository or copy the full Bash block from the macOS/Linux setup slide, then run:

```bash
bash scripts/setup-macos-linux.sh
```

On native Windows, open Administrator PowerShell as your normal account, download the repository or copy the full block from the Windows setup slide, then run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1
```

The execution-policy override applies only to that process. The slide blocks save the scripts before executing them so interactive Hermes setup reads the terminal correctly. Nothing needs to execute a partially downloaded shell pipe.

The default profile is bundled inside both scripts; no public raw URL or repository token is required.

Both installers:

1. Check the OS and Docker Linux-container engine, then run Docker's `hello-world` smoke test.
2. Install Tailscale if missing and request sign-in when necessary. Existing tailnet identity is kept; no auth keys are shipped.
3. Install native Hermes with Desktop when Hermes is missing. The upstream bootstrap scripts are pinned to commit `afe3cbd817b7f5655e4172b442acf6fa7c9bb55d`; upstream's default **stable** channel selects the runtime. This is not a fully locked dependency bundle. Existing Hermes is preserved, then Desktop is built explicitly.
4. Install a new `workshop` profile and run interactive setup. A rerun keeps an existing profile and its model credentials. Terminal backend is then explicitly set to `docker`.
5. Set `dashboard.public_url` to `http://<tailscale-ip>:9119`. This enables the auth gate even though the backend listens on loopback. On first configuration, prompt for a nonblank username, a password of at least 12 characters and confirmation, with a hidden/visible entry choice (hidden by default). There is no preset username or generated login password. Generate only the session-signing secret randomly. Credentials are saved locally through Hermes' config writer and in the protected `dashboard-login.txt`, never in GitHub. Normal reruns preserve the login.
6. Register a per-profile backend (Bash: `hermes -p workshop serve --isolated --host 127.0.0.1 --port <local-port>`; Windows uses its configured loopback backend on 9119) as a user-login service: launchd on macOS, systemd user service on Linux, or a limited-privilege interactive Scheduled Task on Windows.
7. Check `/api/status` using the tailnet Host header and require `auth_required: true` before enabling raw TCP forwarding. This check is a readiness/auth-gate check; it does not perform a password login or a model inference.
8. Configure Tailscale Serve TCP 9119, then show the usable URL and login-file location.

Desktop is built and ready to launch with `hermes desktop`; select `workshop` in the profile rail. Native Hermes and the backend run on the host; **only terminal tool commands** use Docker. Docker does not isolate other native tools, plugins, browser/computer-use tools, or the entire agent. No Docker socket is mounted into an agent container and Docker-in-Docker is not used.

## Dashboard login prompts and bundled profile

The dashboard login is separate from the OS account, Tailscale sign-in and AI provider credentials. On first configuration the installer prompts for a username (no default), a hidden/visible entry choice (hidden by default), a password (minimum 12 characters), and confirmation using the same entry mode. Blank usernames, short passwords and mismatches reprompt. Passwords are passed literally to the native Hermes config writer, rather than interpolated into Compose. The profile `.env` and installer `dashboard-login.txt` store the login locally; these are protected local files, not encrypted vaults or GitHub content. Only the session-signing secret is generated automatically.

The password-reset slide, immediately after the installers, provides copyable reset commands for both platforms. Run them from the extracted installer folder.

An existing `auth-configured` marker preserves the previous login and skips prompts. To replace an older `admin` login or rotate credentials, explicitly rerun with:

```bash
HERMES_RESET_DASHBOARD_AUTH=1 bash scripts/setup-macos-linux.sh
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -ResetDashboardAuth
```

A reset also rotates the session-signing secret, so previous dashboard sessions need to sign in again. Standard double-click launchers keep existing credentials.

The bundled `workshop` distribution contains only:

- `distribution.yaml`: name `workshop`, version `1.0.1`, author `Ben`, description, and ownership of `SOUL.md`/`config.yaml`.
- `config.yaml`: `terminal.backend: docker` and `terminal.cwd: /workspace`, inside the container.
- `SOUL.md`: the exact **Safe Agent Starter** text from the Safe Agent Starter slide, including core operating rules, approval gates, secrets handling, verification and recovery. The `[YOUR NAME]` placeholder is preserved for each recipient to personalize. `python3 scripts/sync-profile-template.py` embeds the authored profile files into both installers; checks prevent drift. The workshop deck carries matching Safe Agent Starter text. These are behavioral instructions, not an enforced sandbox.
- `.gitignore`: an authoring allowlist to keep local secrets/runtime data out of a profile repository; it is included in the bundle, not needed for the runtime template installation.

No personal data, API keys, model/provider choice, custom skills, MCP connections, messaging bot tokens, cron jobs or desktop themes are shipped by this profile. Base Hermes can include its own standard tools/skills independently. The installer subsequently applies machine-specific dashboard URL and authentication settings. Your own trusted Git distribution can replace the starter profile.

## Tailscale correction and manual commands

The supplied command is valid:

```text
tailscale serve --bg --tcp=9119 tcp://127.0.0.1:9119
```

It forwards TCP **on this machine's Tailscale address**, subject to tailnet access policy. It does not bind every LAN interface, publish to the internet, or turn `0.0.0.0` into a usable destination. Use:

```text
http://100.x.y.z:9119
```

Replace `100.x.y.z` with the **server's** output from `tailscale ip -4`. Both the server and connecting device must be online in an authorized tailnet. Enter the `http://` scheme explicitly because raw TCP forwarding does not add HTTPS; Tailscale encrypts the network tunnel. Keep any existing bookmarked HTTPS Serve endpoint if still configured; this adds a separate TCP listener and does not reset Serve.

macOS/Linux (with Tailscale CLI installed and the authenticated backend running):

```bash
tailscale status
tailscale serve status
tailscale ip -4
sudo tailscale serve --bg --tcp=9119 tcp://127.0.0.1:9119
tailscale serve status
```

macOS GUI installations may require `/Applications/Tailscale.app/Contents/MacOS/Tailscale` instead of `tailscale`; the installer detects that path. Linux may require `sudo tailscale up` for initial sign-in. Tailscale Serve may show a one-time tailnet enablement/approval link; complete it and rerun the Serve command if requested.

Windows, Administrator PowerShell:

```powershell
$ts = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
& $ts status
& $ts serve status
& $ts ip -4
& $ts serve --bg --tcp=9119 tcp://127.0.0.1:9119
& $ts serve status
```

If not logged in, run `& $ts up` and finish browser sign-in first. Check `$LASTEXITCODE` after any failed command; the installer does this automatically. No broad LAN firewall rule or `0.0.0.0` backend binding is needed.

From **another** tailnet device, open `http://<server-tailscale-ip>:9119`, sign in, and select the profile. If unavailable, check the server backend first, then `tailscale serve status`, Tailscale connectivity and tailnet grants/ACLs for TCP 9119. Do not assume the local installer proves remote access.

## Publish and install your own profile

Edit `profiles/workshop/SOUL.md`, `config.yaml` and `distribution.yaml` here to set workshop defaults. Run `python3 scripts/sync-profile-template.py` after editing. It embeds these authored files into both installers and updates the slides. Recipients need no access token for this private slide repository and do not clone its media. A custom private Git profile still needs their own Git access.

For an independently versioned GitHub profile:

1. Copy the contents of `profiles/workshop/`, including `.gitignore`, into a **new, dedicated repository root**.
2. Customize the manifest, SOUL, settings and reviewed skills. Keep the terminal backend `docker`. Do not put a personal `.env`, OAuth credentials, sessions, memory or API keys in the repository. The template `.gitignore` allowlists authored files; extend the allowlist intentionally for additional assets.
3. Commit/push the authored files to your GitHub repository. A distribution's `distribution.yaml` must be at the repository root; a GitHub `/tree/main/profiles/workshop` URL is not a distribution source.
4. Supply that repository to the installer:

macOS/Linux:

```bash
HERMES_PROFILE_SOURCE=https://github.com/YOUR-NAME/YOUR-PROFILE.git \
HERMES_PROFILE_NAME=my-workshop bash scripts/setup-macos-linux.sh
```

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 `
  -ProfileSource https://github.com/YOUR-NAME/YOUR-PROFILE.git -ProfileName my-workshop
```

Use a new profile name to try a different distribution; reruns deliberately preserve existing profiles. The installer uses `--yes` for the source you select, so review/trust that repository first: skills/plugins can contain code. Private repositories use your existing Git credentials. The upstream Windows installer can stage its own Git; if a private profile clone cannot authenticate, configure Git for that account before retrying.

Recipients can update a Git-installed distribution with `hermes profile update my-workshop`. For the default local template install, publish a separate Git distribution for ongoing updates rather than expecting `profile update` to pull the slide repository. An archive exported from Desktop is another option when you want to share appearance/layout too, but it may contain personal memories; review it before publication.

No credentials are preconfigured for recipients. Each user supplies their own model/provider access through `hermes -p my-workshop setup`. Publishing a profile is separate from granting access to your tailnet.

## Audit findings fixed

| Old behavior | Change |
| --- | --- |
| Slide 13 Bash differed from its source and polled without credentials | Deterministic sync script, saved-file launchers and explicit auth-gate readiness check |
| Claimed native setup but ran the whole agent in Docker | Native installer plus `terminal.backend: docker` and source-built Desktop |
| Windows PowerShell used Linux container implicitly, with no no-WSL2 backend check | Hyper-V edition/architecture/feature checks and running Hyper-V VM verification |
| Missing commands could be followed by a stale `$LASTEXITCODE` | PowerShell stops on command-resolution errors and checks every native exit |
| Passwords interpolated directly into Compose `.env` | Native Hermes config writer plus prompted, confirmed credentials; no Compose interpolation |
| Reruns overwrote `.env`/Compose and regenerated credentials | Named profile is kept, credentials are initialized once per installer profile |
| Neither script installed or configured Tailscale/profile/Desktop | Added installation, sign-in, local template/custom Git profile, Desktop build and login service |
| Workflow could reset an unrelated title slide/date and cover image | Replaced the mutating workflow with read-only three-OS validation |
| TCP Serve described as accessible on all interfaces | Corrected to Tailscale IP + port, authorized tailnet devices only |

## Checks, limits and recovery

Automated checks have also passed on macOS, Ubuntu and Windows GitHub runners, including Windows PowerShell 5.1 parsing.

Offline checks run locally: Bash syntax, deck/source synchronization, both embedded launchers, and mocked Linux/macOS install/rerun/Docker-failure/auth-failure paths. The mocks confirm that forwarding is never enabled after those failures, credentials survive reruns, paths with spaces are quoted, and macOS service XML parses.

CI parses PowerShell on all three runner OSes and separately in Windows PowerShell 5.1; it checks stock macOS Bash syntax. **These are not clean-machine installation tests.** Actual Docker/Tailscale/provider/Desktop installation and remote TCP access still need a manual pass on real target machines. This Linux workspace has no PowerShell and its network proxy is unavailable, so no live dependencies were installed or OS compatibility certified here.

Before workshop rollout, test on Apple Silicon macOS, your supported Linux distro, and x64 Windows Pro with Hyper-V: reboot/login; complete sign-ins; confirm `hermes -p workshop config get terminal.backend` prints `docker`; make a real agent terminal call and inspect `docker ps -a`; open Desktop; verify remote login and a conversation from a second tailnet device; rerun and confirm model settings and login remain intact. Check tailnet policy and test the long bookmarked URL separately if retaining it.

The new Bash installer can coexist with an existing Hermes/container backend on local 9119 by using a separate local port; it does not stop or remove the old service or its data. If intentionally migrating, stop the old service yourself after checking what uses it. A first Bash install chooses a separate local port if 9119 is occupied. Windows still refuses an occupied local 9119. Rerunning is scoped to the installer's existing login service; an unrelated port conflict must be resolved manually. There is one Tailscale TCP 9119 mapping per machine; reconfiguring it points that remote endpoint to the selected workshop backend.

Backend starts at **user login**, not guaranteed before login. Docker Desktop also needs to be running after login (enable its start-at-sign-in setting). On Linux, an administrator can enable user lingering when unattended operation is required; the user also needs Docker socket access. Service startup failures should be fixed before enabling forwarding. On Windows the task retries failures three times; if Docker/Tailscale first-run setup outlasts this, finish setup and rerun.

Logs/state: macOS/Linux `~/.hermes-workshop-installer/<profile>/`; Linux backend logs in `journalctl --user -u hermes-workshop-workshop`; Windows `%LOCALAPPDATA%\HermesWorkshopInstaller\<profile>\` plus Task Scheduler history. Login file: `dashboard-login.txt` in the installer state directory. POSIX state is private (umask 077); Windows state has user/SYSTEM ACLs. Treat the native profile's `.env` as a secret too.

To remove only this forwarding rule:

```text
tailscale serve --tcp=9119 off
```

Use sudo/Administrator as appropriate. Do not use `tailscale serve reset`, which would remove unrelated endpoints. Disable the login backend with `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.hermes.workshop.workshop.plist` (macOS), `systemctl --user disable --now hermes-workshop-workshop` (Linux), or stop/unregister `HermesWorkshop-workshop` in Task Scheduler (Windows). These actions preserve profile data.

## Sources

- [Native install, Desktop flags and layouts](https://github.com/NousResearch/hermes-agent/blob/afe3cbd817b7f5655e4172b442acf6fa7c9bb55d/website/docs/getting-started/installation.md)
- [Upstream platform support](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/getting-started/platform-support.md)
- [Desktop source builds and remote backends](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/desktop.md)
- [Profile distributions](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/profile-distributions.md)
- [Dashboard authentication and public URL](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/web-dashboard.md)
- [Tailscale Serve TCP reference](https://tailscale.com/docs/reference/tailscale-cli/serve)
- [Docker Desktop Windows requirements and Hyper-V](https://docs.docker.com/desktop/setup/install/windows-install/)

Profile version 1.0.1 adopts the SOUL.md from the Safe Agent Starter slide. Existing installed profiles are still preserved on rerun; this does not overwrite a recipient's customized SOUL.md. To adopt it in an existing profile, deliberately replace that profile's SOUL.md with `profiles/workshop/SOUL.md` (or copy the slide's prompt), keeping a copy of any customization first.

## Existing backend already uses port 9119 (macOS/Linux)

Bash defaults to local 9119. If occupied by an existing service, it selects a free local port from 9120–9139, stores it in `~/.hermes-workshop-installer/<profile>/backend-port`, and creates an isolated workshop backend on loopback. Tailscale remains `--tcp=9119` but forwards to that saved local port, for example `tcp://127.0.0.1:9120`. This preserves the short remote URL and leaves the existing process running. Its original bind address is not changed.

You can explicitly select a free port with `HERMES_BACKEND_PORT=9120 bash scripts/setup-macos-linux.sh`. An explicitly requested occupied port causes an actionable error rather than being changed silently. Reruns use the saved local port. The service/auth readiness check uses that selected port; `/api/status` must report authentication enabled before forwarding is configured.

## Download access

The installer/download home is the public [benczb/hermes-tailscale-docker](https://github.com/benczb/hermes-tailscale-docker) repository. Per-OS ZIPs in `downloads/` have direct public links in the README. No GitHub sign-in is required. Extract once and use the included platform launcher. The private slide repository can stay private. The older GitHub Actions artifact links require sign-in; they are not the attendee download path.

The packages are deterministically generated by `scripts/package-installer.py`, with SHA-256 checksums and preserved POSIX executable bits. Regenerate and commit them when changing installer/profile/docs files. CI checks that packages match their sources. Downloads are bootstrap packages, not offline copies of Hermes, Docker or Tailscale.
