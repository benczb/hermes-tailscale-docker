# SID Hermes training bootstrap

Guided native **source runtime + source-built Hermes Desktop**, with **Docker Desktop retained only for agent terminal/file tools**. No whole-runtime Compose and no second bundled Desktop download. Synthetic training data only; not an official SID distribution.

## Prerequisites and start

Have IT approve Python 3.9+, running local Docker Desktop/Engine (Windows: Linux containers), signed-in host Tailscale on PATH, model/provider credentials and the official Hermes source/Desktop build prerequisites. Builds need network, disk space and potentially a compiler. This is not an unattended one-click installer.

Entry points: native macOS, Linux desktop, native Windows PowerShell. WSL is refused because this flow configures host Tailscale. OS-specific source builds must be rehearsed before class.

```bash
git clone https://github.com/benczb/hermes-sid-training.git
cd hermes-sid-training
bash bootstrap.sh
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap.ps1
```

Use `--home /absolute/fresh/location` (or `--directory`) on POSIX, `-Home C:\approved\sid-training` on Windows. An existing target is never overwritten, including after partial failure. `--desktop` / `-Desktop` are compatibility flags; the default install already includes Desktop.

## What happens

1. Read-only preflight checks the fresh target, local Docker context, signed-in Tailscale, empty Serve configuration and free loopback TCP 9119. Remote Docker contexts, existing Serve rules and WSL are refused.
2. Explicit consent precedes the official source installer. **Upstream may install build prerequisites and edit shell PATH files; Windows upstream currently prepends the training bin to User PATH.** These effects are disclosed, not claimed absent. Personal host command wrappers are not silently replaced: training config sets `cli.expose_on_path: false` and project launches use an exact private executable. Use a fresh approved training account/home.
3. Create `TARGET/home` with allowlisted synthetic files, private `.env`, Docker terminal config and `gateway.standalone: true`. Explicitly mount only `TARGET/home/training` read-only at `/opt/sid-training`; tools start there and drafts belong in `/workspace`. Automatic host-cwd mounting is disabled. Hermes may also mount standard sandbox resources; this is not an audited security boundary.
4. Run the official installer with `--include-desktop --non-interactive --channel stable` (Windows: `-IncludeDesktop -NonInteractive -Channel stable`) under the selected `HERMES_HOME`. No interactive setup wizard can switch the Docker terminal backend. One source tree at `TARGET/home/hermes-agent` owns runtime and GUI. Stable is mutable, not an immutable runtime pin.
5. Write persistent training launch scripts **inside TARGET**, not the personal host bin. `SID-Desktop` (Windows: `SID-Desktop.ps1`) sets the training `HERMES_HOME` and launches source Desktop with `--hermes-root TARGET/home/hermes-agent`. Use this instead of an unrelated installed app. `SID-Hermes` / `SID-Hermes.ps1` passes arguments to the exact runtime. Windows requires the official `.exe` launcher; unsafe `.cmd` fallback fails explicitly.
6. Start a detached `dashboard --no-open --host 127.0.0.1 --port 9119` child; record `dashboard.pid` and private `dashboard.log` in TARGET. Upstream dashboard is foreground-only; there is no invented `--background` flag. This is not a reboot-persistent OS service. Health failure terminates the child.
7. Verify anonymous denial, wrong-password denial and cookie-authenticated `/api/status` via `POST /auth/password-login`. HTTP Basic `curl -u` is not equivalent. Only then ask separately before host `tailscale serve --bg --tcp=9119 tcp://127.0.0.1:9119`; read back exact TCPForward. Never Funnel or Serve reset.

## Use and updates

Open the generated SID-Desktop launcher. Configure **only the model/provider** in Desktop; do not run full `hermes setup`, which may change terminal settings. Review Docker backend before the first exercise. Provider authentication, a synthetic model turn and Desktop's one-click source update require live rehearsal. The same source tree is updateable by `SID-Hermes update` and Desktop; no separate bundled application is installed.

Desktop uses its native local gateway, not dashboard password login. The separate browser dashboard is `http://127.0.0.1:9119`, username `participant`, chosen password. Remote browser participants use `http://HOST-TAILNET-DNS:9119` subject to ACLs. Tailscale TCP transport is encrypted, but the URL is not browser HTTPS. Desktop remote connections are not acceptance-tested here.

The public profile is a seeded standalone home, not a live-profile export: SOUL, one board-review skill and three fictional exercises. No personal tokens, sessions, memories, plugins or schedules. The skill reads `/opt/sid-training` inside Docker. Validated Presidio redaction and local redaction models are not included. Never upload real board papers. Models may transmit prompts and incur charges; profiles do not enforce confidentiality.

## Security and recovery

Passwords need 16+ letters, digits or `_.!@%+=:-` only. Restricted characters and single-quoted dotenv serialization avoid interpolation/quoting surprises. Credentials remain plaintext in private `.env`; target/home are 0700 and `.env` is 0600 on POSIX. Windows NTFS ACL review is manual. Never publish TARGET.

Failures preserve the new home. Inspect logs privately; choose a fresh target rather than deleting blindly. Dashboard is not an OS service and does not survive reboot by contract. Use the generated training CLI for `dashboard --status` / `dashboard --stop` before manual recovery. PID files are diagnostic receipts, not permission to kill an unverified recycled PID.

Before enabling Serve after recovery, rerun authentication from the repository:

```bash
python3 -c 'import bootstrap,getpass; bootstrap.health(getpass.getpass("Dashboard password: "))'
```

Inspect `tailscale serve status`. Remove **only** this project's TCP rule with `tailscale serve --tcp=9119 off` if appropriate, then inspect again. Never `serve reset`. No host apps, services, accounts or training data are automatically removed.

## Provenance and verification

Official installers: https://hermes-agent.nousresearch.com/install.sh and https://hermes-agent.nousresearch.com/install.ps1. Official docs: https://hermes-agent.nousresearch.com/docs/user-guide/desktop and https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard.

Reviewed upstream main: `scripts/install.sh`, `scripts/install.ps1`, `hermes_cli/subcommands/dashboard.py`, `hermes_cli/main_desktop.py`, `hermes_cli/_launchers.py`, `tools/environments/docker.py`. Archived Desktop package receipts in `research/` and `versions.json` are historical provenance only, not packages installed by this flow.

```bash
python3 -W error::ResourceWarning -m unittest discover -s tests -v
python3 -m py_compile bootstrap.py tests/test_bootstrap.py
bash -n bootstrap.sh
```

Tests mock installer/Docker/Tailscale/Desktop effects; a real local HTTP fixture verifies cookies, not actual Hermes integration. CI runs Linux/macOS/Windows mocks and parses PowerShell. See `VERIFICATION.md`. No host installation, service restart, provider call or tailnet mutation was performed in development. Actual source builds, Desktop home selection/update, sandbox mounts/commands, Windows ACLs and authorised/unauthorised tailnet browser access remain mandatory rehearsal gates.
