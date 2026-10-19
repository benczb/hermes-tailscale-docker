# SID Hermes training bootstrap (native runtime)

A bounded, consent-driven MVP for the Singapore Institute of Directors two-hour workshop.
This is an independent training template, not an official SID or Nous Research distribution.

**Architecture: native runtime + Docker terminal sandbox.** The Hermes runtime is installed
**natively on the host** with the official one-liner. **Docker Desktop is retained, but only
as the Hermes terminal sandbox backend** (`terminal.backend: docker`) — the agent's shell
commands and file tools run inside a disposable sandbox container. The runtime, the web
dashboard and the Desktop GUI run on the host, **not** in a container. This means:

- **Future updates need no terminal** — `hermes update` (CLI) or the one-click update inside
  Hermes Desktop (the app checks for updates in the background and offers it).
- There is **no duplicated bundled + source install**: one native runtime, one Desktop GUI.
- The installer seeds a **fresh, synthetic-data-only** Hermes data home (a `HERMES_HOME`),
  never the trainer's live profile.

**Not an unattended one-click installer.** Host prerequisites, provider sign-in, OS
installation and Desktop connection require human interaction. No packages, services or host
configuration are changed merely by downloading this repository or running the tests.

## Before the workshop

Have your IT team approve and install these on the **host**:

- Python 3.9+ with its standard library. On Windows use the Python launcher (`py -3`) or
  `python`, not only the Microsoft Store alias.
- [Docker Desktop](https://docs.docker.com/desktop/) on macOS/Windows, or
  [Docker Engine](https://docs.docker.com/engine/install/) on Linux. Start the engine
  yourself and select a local socket context; ensure `docker info` works. Remote Docker
  contexts are rejected. Docker Desktop may require a commercial subscription under your
  organisation's terms. On Windows, use Linux containers.
- [Tailscale](https://tailscale.com/download) on the host (optional, for private tailnet
  sharing). Sign in and connect; ensure `tailscale` is on PATH. ACLs must allow only the
  intended participants. The script will not log in, start the daemon, elevate privileges
  or replace any existing Serve configuration.
- Your own approved model provider account. API use can cost money and transmit prompts to
  that provider. Configure credentials interactively, never in this public repository.

Host package installation is deliberately a manual, approved prerequisite in this MVP. No
guessed `winget` identifiers, silent package installs or blanket passwordless sudo rules are used.

## Start

Download this repository ZIP from GitHub and extract it, or:

```bash
git clone https://github.com/benczb/hermes-sid-training.git
cd hermes-sid-training
bash bootstrap.sh
```

Windows, in a normal **native PowerShell** window from the extracted repository (not WSL):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

The execution-policy override applies only to that process. Review scripts first and follow
organisational policy. Do not run from WSL, as that would configure the wrong Tailscale host.

The guided native flow:

1. Read-only preflight checks Docker (local engine, `docker info`, local socket context),
   signed-in Tailscale (when tailnet sharing is wanted), an empty Serve configuration and
   port 9119. It refuses a pre-existing target directory.
2. Ask for explicit consent, then a new dashboard password twice (16+ characters). Passwords
   are never put in command arguments or the public template.
3. Exclusively create a fresh training home and seed only the allowlisted synthetic template
   files, a minimal `config.yaml` (Docker terminal sandbox + scoped training-data volume) and
   a private `.env` (dashboard credentials). Then run the **official native installer**,
   scoped to that home via `HERMES_HOME` so your real `~/.hermes` is untouched.
4. Start the native dashboard on **loopback `127.0.0.1:9119`**. Check that anonymous and
   wrong-password requests are denied; authenticate using `POST /auth/password-login` with
   cookie storage, then require a JSON response from the protected `/api/status`.
   **HTTP Basic `curl -u` is not the authentication protocol for this release.**
5. Only after authenticated health passes, ask separately before running
   `tailscale serve --bg --tcp=9119 tcp://127.0.0.1:9119`, then read back and verify the
   exact TCP forwarding rule. This is Serve, not public Funnel.

Choose a different unused data home with `bash bootstrap.sh --home /absolute/path` (or the
`--directory` alias) / `-Home C:\approved\sid-training` in PowerShell.

### Install the official Desktop on the host (optional GUI)

```bash
bash bootstrap.sh --desktop
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap.ps1 -Desktop
```

This separate guided stage downloads a pinned package into your existing Downloads directory,
verifies SHA-256 against the official release receipt, and asks again before opening it. You
finish installation or extraction through the OS. It does not automatically overwrite any
existing app or modify Desktop settings. macOS ZIP extraction is manual. Windows opens the
signed MSIX bundle through the OS App Installer. Packages are large: ~1.6 GB / ~4.3 GB.

In official **Hermes Desktop**, the app drives the **same native backend** — sign in with
username `participant` and your dashboard password. A remote participant connects to
`http://<training-host-tailnet-DNS-name>:9119` after joining the authorised tailnet. Do not
use an unrelated community app. The Desktop checks for updates in the background and offers
a one-click update, so **no terminal is required for future updates**.

**Platform limits:** the verified stable Desktop receipt provides macOS Apple Silicon and
Windows x64/arm64 packages, but no Linux binary. On Linux follow the official
[Desktop/source guide](https://hermes-agent.nousresearch.com/docs/user-guide/desktop). Intel
macOS is not officially supported. The native runtime (CLI/gateway/dashboard) works on
macOS/Linux/Windows via the official installer, subject to their prerequisites.

## Public profile and exercises

Only `SOUL.md`, the `sid-board-review` skill and three synthetic exercise files are copied
from `profile/` into the fresh training home. No working profile, API keys, OAuth tokens,
conversations, memories, real board data, personal integrations, cron jobs, MCP servers or
plugins are exported. The native runtime may initialise its own standard defaults during
setup; the allowlist covers the files this installer seeds, not the upstream built-ins.

Run `training/exercises.md`: review a fictional risk register, draft a monitoring calendar
without activating it, and practise citation review against official sources. Web tools need
separately configured providers. **Presidio, local redaction models and extra plugins are
not included.** Do not claim validated redaction or upload real board papers. Profiles are
organisational separation, not an enforced security boundary.

## Privacy and security

- The **Docker terminal sandbox** mounts only the scoped training-data volume
  (`/opt/sid-training`, read-only) plus Hermes' standard read-only credential/skill/cache
  mounts. It does **not** mount the host home or the Docker socket merely for convenience.
  The host home and credentials are not exposed to the sandbox. Docker still confers
  significant authority, and this is not an audited sandbox.
- The dashboard binds **loopback `127.0.0.1:9119`** (no `--insecure`, no `0.0.0.0`). The
  authenticated cookie gate engages because the basic auth provider is configured in `.env`.
  The health check fails closed before any Serve change.
- Tailscale raw TCP preserves HTTP. Transport between tailnet devices is encrypted by
  Tailscale, but the URL is not browser HTTPS. Confirm native browser sign-in behaviour in
  rehearsal. Tailnet ACLs and dashboard authentication are both required. Never expose
  port 9119 publicly.
- `.env` holds the dashboard password and signing secret in plaintext; keep it 0600 and the
  home root 0700. **Windows NTFS ACL hardening is manual and not validated here.** Provider
  secrets from setup persist in the private data home. Never publish or share the home folder.
- A failed or declined later stage leaves the new training home intact. It is not silently
  rolled back or deleted. See recovery.

## Recovery and removal

A repeat install refuses an existing target, including a partially created one. Do not delete
it blindly. Inspect it, keep any credentials private, and use these from your own training
installation when appropriate:

```bash
# Inspect the sandbox / dashboard (native install):
hermes doctor            # under the training HERMES_HOME
# Rerun provider setup in the sandbox:
hermes setup
# Stop and remove only the sandbox containers, keeping data:
docker ps --filter label=hermes-agent=1
```

Before sharing through Serve after manual recovery, rerun the authentication probe
interactively from the repository directory:

```bash
python3 -c 'import bootstrap,getpass; bootstrap.health(getpass.getpass("Dashboard password: "))'
```

(Windows: `py -3 -c "import bootstrap,getpass; bootstrap.health(getpass.getpass('Dashboard password: '))"`.)
Do not use `curl -u` as a substitute. Do not share logs without inspecting them for secrets.

Inspect `tailscale serve status`. If this installer created the only TCP 9119 rule, remove
**that rule only** with `tailscale serve --tcp=9119 off`, then inspect status again. Do not
use `serve reset`, which would remove unrelated rules. This project does not uninstall host
applications, sign you out, delete training data or alter services automatically.

## Pins and provenance

`versions.json` is the download authority:

- **Native runtime:** installed from the official one-liner —
  `https://hermes-agent.nousresearch.com/install.sh` (POSIX) and
  `https://hermes-agent.nousresearch.com/install.ps1` (Windows), channel `stable`.
  Both URLs returned HTTP 200 to HEAD requests. The runtime updates with `hermes update` or
  the Desktop one-click update. No separate runtime image is pinned.
- **Terminal sandbox image:** the host's own Hermes image is used by `terminal.backend: docker`
  (Hermes resolves `terminal.docker_image`); this is not re-pinned separately here.
- **Official Desktop:** stable receipt version 0.22.0, build `e1734abd5c6128ecbd4d4b995a392750`.
  `research/desktop-stable-record.json` and `research/desktop-build.json` preserve the public
  receipt; tests verify its recorded SHA-256. Artifact URLs returned HTTP 200 to HEAD requests.
  Full multi-gigabyte downloads were not performed during development.
- Tailscale and Docker host versions are IT-managed prerequisites, not silently pinned here.

Authoritative references checked during implementation:

- https://hermes-agent.nousresearch.com/docs/getting-started/installation
- https://hermes-agent.nousresearch.com/docs/user-guide/desktop
- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard
- https://hermes-assets.nousresearch.com/releases/channels/stable.json
- https://github.com/NousResearch/hermes-agent/blob/v0.22.2/hermes_cli/dashboard_auth/routes.py
- https://github.com/NousResearch/hermes-agent/blob/v0.22.2/plugins/dashboard_auth/basic/__init__.py
- https://github.com/NousResearch/hermes-agent/blob/v0.22.2/tools/environments/docker.py
- https://tailscale.com/kb/1242/tailscale-serve

## Verification

No third-party test dependencies are needed:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile bootstrap.py tests/test_bootstrap.py
bash -n bootstrap.sh
```

Tests mock all Docker, Tailscale, native-install and package-opening effects and exercise
consent, allowlisted seeding, overwrite refusal, the Docker-terminal-sandbox preflight,
WSL refusal, mocked full native orchestration, auth denial/success/failure, the real local
HTTP cookie fixture, download checksums, receipt integrity and Bash syntax. CI additionally
parses the PowerShell wrapper on Windows and runs the same tests on Linux/macOS/Windows.
CI results are not assumed to have passed until GitHub reports them.

No real macOS/Windows end-to-end tests, real native installs, real Desktop downloads or
sign-ins, real Tailscale changes, provider calls or sandbox launches were performed during
development. Before class: rehearse on each supported participant OS, verify available disk
space for the sandbox image and Desktop downloads, review Windows ACLs, complete provider
sign-in and a synthetic model turn, verify native Desktop connection and tailnet ACL denial
from an unauthorised device. These remain acceptance gaps, not claimed capabilities.
