# Verification record

Development verification on Linux only, without installing dependencies or changing host services:

- `python3 -W error::ResourceWarning -m unittest discover -s tests -v`: 18 tests passed.
- The tests include a real loopback HTTP fixture proving cookie persistence, not a real Hermes dashboard. Docker/Tailscale effects and OS package opening are mocked.
- `python3 -m py_compile bootstrap.py tests/test_bootstrap.py`: passed.
- `bash -n bootstrap.sh`: passed.
- Real `docker compose -f <isolated-generated-file> config --quiet`: passed. No daemon changes or container launches.
- `git diff --cached --check`: passed before publication.
- Official Desktop artifact HEAD requests: HTTP 200 for the exact macOS/Windows URLs in versions.json. Receipt SHA-256 verified before deriving pins.
- Docker Hub manifest GET: v0.22.2 resolved to the pinned multi-architecture digest, with Linux amd64 and arm64 platform manifests.

PowerShell was not installed on the development host. The GitHub workflow parses the wrapper on Windows and runs mocked tests on all three runner OSes. Consult the actual Actions run for results; the workflow is not a Desktop/runtime E2E test.

Missing acceptance checks: real Docker launch and provider wizard; a paid/approved synthetic model response; full multi-gigabyte Desktop download and OS installation; real Desktop native sign-in; real tailnet forwarding/ACL denial; Windows ACL review; Linux Desktop source build. No claim of real Mac/Windows E2E verification is made.
