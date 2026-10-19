# Verification record

Development verification on Linux only, without installing host packages, changing host
services or touching the real `~/.hermes`:

- `python3 -W error::ResourceWarning -m unittest discover -s tests -v`: **25 tests passed**.
- The tests include a real loopback HTTP cookie fixture proving authenticated cookie
  persistence against a local handler (not a real Hermes dashboard). Docker, Tailscale,
  the native installer, the dashboard and OS package-opening effects are mocked.
- `python3 -m py_compile bootstrap.py tests/test_bootstrap.py`: passed.
- `bash -n bootstrap.sh`: passed.
- `git diff --cached --check`: passed before publication.
- Native install one-liner HEAD requests: HTTP 200 for
  `https://hermes-agent.nousresearch.com/install.sh` and `install.ps1`.
- Official Desktop artifact HEAD requests: HTTP 200 for the exact macOS/Windows URLs in
  `versions.json`. Receipt SHA-256 verified before deriving pins.
- Pinned-source review (`NousResearch/hermes-agent` v0.22.2) confirmed: the dashboard
  defaults to loopback `127.0.0.1:9119`; the auth middleware is a no-op on loopback (no
  `--insecure` needed) yet the cookie gate engages because the basic auth provider is
  configured; `terminal.backend: docker` uses the host Docker daemon and `terminal.docker_volumes`
  entries are passed verbatim to `docker -v` (so `:ro` survives).

PowerShell was not installed on the development host. The GitHub workflow parses the wrapper
on Windows and runs mocked tests on all three runner OSes. Consult the actual Actions run for
results; the workflow is not a Desktop/runtime E2E test.

Missing acceptance checks (honest E2E gaps, not claimed capabilities): a real native Hermes
install on macOS/Windows/Linux; a real provider wizard and a paid/approved synthetic model
response; a real Docker terminal sandbox launch running a command; the full multi-gigabyte
Desktop download and OS installation; real Desktop native sign-in and its one-click update;
real tailnet forwarding/ACL denial; Windows ACL review; Linux Desktop source build. No claim
of real Mac/Windows E2E verification is made.
