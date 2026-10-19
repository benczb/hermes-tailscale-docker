# Verification record

Baseline `0dd9565105b9d4f85364a8df1e99588305911a8c`: 25 tests passed despite native-flow defects. Correction adds regression coverage for actual host mount source/cwd, occupied port with Tailscale enabled, detached launch and cleanup, persistent scoped Desktop launchers, restricted dotenv passwords and default Desktop-included official install commands.

Development checks on Linux, without installing packages or restarting services:

- `python3 -W error::ResourceWarning -m unittest discover -s tests -v`: 31 tests pass.
- `python3 -m py_compile bootstrap.py tests/test_bootstrap.py`: passes.
- `bash -n bootstrap.sh`: passes.
- `git diff --check`: passes.
- A real loopback HTTP cookie fixture checks anonymous/wrong-password denial and cookie persistence, not a real Hermes dashboard. A real ephemeral occupied socket checks the preflight refusal. Installer, Docker, Tailscale and dashboard subprocess effects are mocked.

Official installer bodies and current upstream main source were retrieved and reviewed. `--include-desktop` / `-IncludeDesktop` select a source Desktop build; noninteractive skips setup/gateway wizard stages. Dashboard and serve share a foreground handler and have no background flag. Desktop `--hermes-root` sets `HERMES_DESKTOP_HERMES_ROOT`; `HERMES_HOME` still must be selected separately. Docker volume strings are passed to Docker verbatim; automatic cwd mounting is independently configurable. The source build supports private executable launchers; Windows `.cmd` fallback is explicitly refused by this bootstrap.

`cli.expose_on_path: false` disables POSIX global conveniences. Upstream Windows installer still prepends workspace bin to User PATH and upstream POSIX may edit shell rc PATH lines; consent and README disclose these effects. No personal wrapper is replaced by this project. Use an approved fresh workspace account. Stable installer/channel is mutable, not an immutable provenance pin; older archived package receipts are not installed.

CI runs mocked checks on Linux/macOS/Windows and parses PowerShell on Windows. Consult the exact published revision's Actions result; this is not OS/Desktop E2E evidence.

Unverified acceptance: actual source runtime/Desktop builds on each OS; correct live Desktop workspace home/source selection; GUI update; a real Docker sandbox mount/command; provider authentication and approved synthetic response; Windows ACLs; Tailscale authenticated browser access/ACL denial. Dashboard child is detached, not a reboot-persistent service. Source dependency/build failures remain possible and fail closed before Serve. No live profile, host package installation, service restart or tailnet change occurred during development.
