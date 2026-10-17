# SID Hermes training bootstrap

A bounded, consent-driven MVP for the Singapore Institute of Directors two-hour workshop. This is an independent training template, not an official SID or Nous Research distribution. It creates a fresh, synthetic-data-only Hermes data home in Docker and guides installation of the official host Desktop. It never copies the trainer's live profile.

**Not an unattended one-click installer.** Host prerequisites, sign-in, provider selection, OS installation and Desktop connection require human interaction. No packages, services or host configuration are changed merely by downloading this repository or running the tests.

## Before the workshop

Have your IT team approve and install these on the **host**, not in the Hermes container:

- Python 3.9+ with its standard library. On Windows use the Python launcher (`py -3`) or `python`, not only the Microsoft Store alias.
- [Docker Desktop](https://docs.docker.com/desktop/) on macOS/Windows, or [Docker Engine](https://docs.docker.com/engine/install/) on Linux. Compose v2.30+ is required. Start the engine yourself, select a local socket context and ensure `docker info` works. Docker Desktop may require a commercial subscription under your organisation's terms. Windows must use Linux containers. Remote Docker contexts are rejected.
- [Tailscale](https://tailscale.com/download) on the host. Sign in to the intended tailnet and connect. Ensure `tailscale` is on PATH (macOS GUI installations may need their documented CLI integration). ACLs must allow only the intended participants. The script will not log in, start the daemon, elevate privileges or replace any existing Serve configuration.
- Your own approved model provider account. API use can cost money and transmit prompts to that provider. Configure credentials interactively, never in this public repository.

Host package installation is deliberately a manual, approved prerequisite in this MVP. No guessed `winget` identifiers, silent package installs or blanket passwordless sudo rules are used.

## Start

Download this repository ZIP from GitHub and extract it, or:

```bash
git clone https://github.com/benczb/hermes-sid-training.git
cd hermes-sid-training
bash bootstrap.sh
```

Windows, in a normal native PowerShell window from the extracted repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

The execution-policy override applies only to that process. Review scripts first and follow organisational policy. Do not run from WSL, as that would configure the wrong Tailscale host.

The guided runtime flow:

1. Read-only preflight checks Docker, local context, Compose version, signed-in Tailscale, empty Serve configuration, port 9119 and a **non-existent** target directory.
2. Ask for explicit consent, then a new dashboard password twice (16+ characters). Passwords are never put in command arguments or the public template.
3. Exclusively create `~/hermes-sid-training`, seed only the five allowlisted template files and write a loopback-only Compose project. Pull the pinned multi-architecture image and run the real `hermes setup` wizard in the container.
4. Start the new container. Check that anonymous and wrong-password requests are denied; authenticate using `POST /auth/password-login` with cookie storage, then require a JSON response from the protected `/api/status`. **HTTP Basic `curl -u` is not the authentication protocol for this pinned release.**
5. Ask separately before running the requested `tailscale serve --bg --tcp=9119 tcp://127.0.0.1:9119`, then read back and verify the exact TCP forwarding rule. This is Serve, not public Funnel.

Choose a different unused data directory with `bash bootstrap.sh --directory /absolute/path` or `-Directory C:\approved\sid-training` in PowerShell. The Compose project name and host port are fixed, so this MVP supports one training instance per host. Existing project port usage is never replaced.

### Install the official Desktop on the host

```bash
bash bootstrap.sh --desktop
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap.ps1 -Desktop
```

This separate guided stage downloads a pinned package into your existing Downloads directory, verifies SHA-256 against the official release receipt, and asks again before opening it. You finish installation or extraction through the OS. It does not automatically overwrite any existing app or modify Desktop settings. macOS ZIP extraction is manual, then move the app only after checking the destination. Windows opens the signed MSIX bundle through the OS App Installer. Packages are large: approximately 1.6 GB and 4.3 GB respectively.

In official **Hermes Desktop**, use **Settings > Gateways** to add `http://127.0.0.1:9119` and sign in with username `participant` and your dashboard password. A remote participant uses `http://<training-host-tailnet-DNS-name>:9119` after joining the authorised tailnet. Do not use an unrelated community app expecting port 8642. This is a standalone Docker data home, shown as the runtime's default profile, not an exported/imported named profile.

**Platform limits:** the verified stable Desktop receipt provides macOS Apple Silicon and Windows x64/arm64 packages, but no Linux binary. On Linux follow the [official Desktop/source guide](https://hermes-agent.nousresearch.com/docs/user-guide/desktop); building it can require additional prerequisites. Intel macOS is not officially supported. This MVP does not automate Linux source builds or replace the official app with the similarly named community Hermes One app. Docker runtime guidance covers macOS/Linux/Windows, subject to their prerequisites. Desktop 0.22.0 to runtime 0.22.2 connectivity still needs a live rehearsal.

## Public profile and exercises

Only `SOUL.md`, the `sid-board-review` skill and three synthetic exercise files are copied from `profile/`. No working profile, API keys, OAuth tokens, conversations, memories, real board data, personal integrations, cron jobs, MCP servers or plugins are exported. The runtime may initialise its own standard defaults during setup; the allowlist covers the files this installer seeds, not the upstream image's built-ins.

Run `data/training/exercises.md`: review a fictional risk register, draft a monitoring calendar without activating it, and practise citation review against official sources. Web tools need separately configured providers. **Presidio, local redaction models and the proposed three reviewed director plugins are not included.** Do not claim validated redaction or upload real board papers. Profiles are organisational separation, not an enforced security boundary.

## Privacy and security

- The container mounts **only the new data home**, not the host home or Docker socket. Docker still confers significant authority, and this is not an audited sandbox.
- Host publishing binds to `127.0.0.1` only. Inside the container the dashboard binds `0.0.0.0`, so its authentication gate must engage. The health check fails closed before any Serve change.
- Tailscale raw TCP preserves HTTP. Transport between tailnet devices is encrypted by Tailscale, but the URL is not browser HTTPS. Confirm native browser-assisted sign-in behaviour in rehearsal. Tailnet ACLs and dashboard authentication are both required. Do not expose port 9119 publicly.
- `runtime.env` contains the dashboard password and signing secret in plaintext, passed with Compose's raw env-file format to avoid `$` interpolation. POSIX mode is 0600; the new root directory is 0700. **Windows NTFS ACL hardening is manual and not validated here.** Docker administrators can inspect container environment. Provider secrets from setup persist in the private data volume. Never publish or share the installation folder.
- A failed or declined later stage leaves the new data home and any running container intact. It is not silently rolled back or deleted. See recovery.

## Recovery and removal

A repeat install refuses an existing target, including a partially created one. Do not delete it blindly. Inspect it, keep any credentials private, and use these commands from your own training installation directory when appropriate:

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail 100 hermes
# Rerun an interrupted provider wizard:
docker compose run --rm hermes setup
# Start after fixing the local issue:
docker compose up -d hermes
# Stop and remove only this project's containers/network, keeping its data:
docker compose down
```

Before sharing through Serve after manual recovery, rerun the authentication probe interactively:

```bash
python3 -c 'import bootstrap,getpass; bootstrap.health(getpass.getpass("Dashboard password: "))'
```

Run that command from the repository directory, not the installation directory (Windows: `py -3 -c "import bootstrap,getpass; bootstrap.health(getpass.getpass('Dashboard password: '))"`). Do not use `curl -u` as a substitute. Do not share logs without inspecting them for secrets.

Inspect `tailscale serve status`. If this installer created the only TCP 9119 rule, remove **that rule only** with `tailscale serve --tcp=9119 off`, then inspect status again. Do not use `serve reset`, which would remove unrelated rules. This project does not uninstall host applications, sign you out, delete training data or alter services automatically.

## Pins and provenance

`versions.json` is the download authority, deliberately not `latest`:

- Runtime: official Docker Hub `nousresearch/hermes-agent:v0.22.2` multi-architecture manifest digest `sha256:36099926da316742423544e055d4734777105ffe6341873af5459b957d0c2919`, read from the registry. Linux amd64 and arm64 manifests are present.
- Official Desktop: stable receipt version 0.22.0, build `e1734abd5c6128ecbd4d4b995a392750`. `research/desktop-stable-record.json` and `research/desktop-build.json` preserve the public receipt; tests verify its recorded SHA-256. Artifact URLs returned HTTP 200 to HEAD requests. Full multi-gigabyte downloads were not performed during development. SHA receipts establish integrity relative to the upstream HTTPS metadata, not an independent security audit.
- Tailscale and Docker host versions are IT-managed prerequisites, not silently pinned or installed here.

Authoritative references checked during implementation:

- https://hermes-agent.nousresearch.com/docs/getting-started/installation
- https://hermes-agent.nousresearch.com/docs/user-guide/desktop
- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard
- https://hermes-assets.nousresearch.com/releases/channels/stable.json
- https://github.com/NousResearch/hermes-agent/blob/v0.22.2/docker/s6-rc.d/dashboard/run
- https://github.com/NousResearch/hermes-agent/blob/v0.22.2/hermes_cli/dashboard_auth/routes.py
- https://github.com/NousResearch/hermes-agent/blob/v0.22.2/plugins/dashboard_auth/basic/__init__.py
- https://tailscale.com/kb/1242/tailscale-serve

The slides' existing Bash and PowerShell setup scripts were read for context only, not modified or copied wholesale. This project fixes their unsafe re-run behaviour, floating image tag and incorrect Basic-auth health assumption.

## Verification

No third-party test dependencies are needed:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile bootstrap.py tests/test_bootstrap.py
bash -n bootstrap.sh
```

Tests mock all Docker, Tailscale and package-opening effects and exercise consent, allowlisted seeding, overwrite refusal, mocked full orchestration, auth denial/success/failure, download checksums, receipt integrity and Bash syntax. CI additionally parses the PowerShell wrapper on Windows and runs the same tests on Linux/macOS/Windows. CI results are not assumed to have passed until GitHub reports them.

No real macOS/Windows end-to-end tests, container launches, host package installations, Tailscale changes, provider calls or Desktop sign-ins were performed during development. Before class: rehearse on each supported participant OS, verify available disk space for the Docker image and Desktop downloads, review Windows ACLs, complete provider sign-in and a synthetic model turn, verify native Desktop connection and tailnet ACL denial from an unauthorised device. These remain acceptance gaps, not claimed capabilities.
