# Contributing

Contributions are welcome: installation bug reports, documentation corrections,
accessibility improvements and reproducible platform fixes. This is a community
companion for native Hermes Desktop and its agent, optional Docker terminal tools,
and host Tailscale. It is not an official Nous Research distribution.

## Report a problem or suggest a change

Check [existing issues](https://github.com/benczb/hermes-tailscale-docker/issues)
first, then use the bug or feature template. Include the OS edition/version, CPU
architecture, installer path/revision, terminal choice and a minimal reproduction.
Remove passwords, tokens, OAuth JSON contents, private hostnames and personal paths
from logs and screenshots. Report vulnerabilities through [SECURITY.md](SECURITY.md),
not a public issue. Follow [the code of conduct](CODE_OF_CONDUCT.md).

Discuss changes to supported platforms, installation architecture, authentication,
remote access or release delivery in an issue before implementing a large change.
Small documentation and bug fixes can go directly to a pull request against main.
Keep the change focused and explain the observed problem and resulting behavior.

## Work locally

Fork and clone the repository. Use Python 3.9+ for Python checks, Bash for POSIX
scripts, and PowerShell 7 for helper tests. Windows PowerShell 5.1 is also tested
on Windows. The graphical companion uses Node.js 24 and npm; native helper builds
may need Python and a C++ compiler. Work in a disposable test account or VM for
real installation tests. Setup scripts change host software, services and Tailscale
configuration; do not run them just to check a documentation edit.

For installer scripts or profile changes:

```bash
python3 scripts/test-installers.py
python3 scripts/test-command-launchers.py
bash -n scripts/setup-macos-linux.sh
bash -n start-setup.sh
```

For graphical companion changes, from `installer-ui/`:

```bash
npm ci
npm test
node test/pty-smoke.cjs
```

For the separate legacy Python bootstrap:

```bash
python3 -m unittest discover -s tests -v
```

CI also runs the PowerShell helper tests in `scripts/test-*.ps1`, including
Windows PowerShell 5.1 checks. Run the applicable helpers after changing Windows
behavior. Distinguish mocked checks from tests on a real supported computer.

After authored profile changes, run `python3 scripts/sync-profile-template.py`.
After installer or profile changes, run `python3 scripts/package-installer.py`
and commit the regenerated downloads and SHA256SUMS. The separate slides
repository has synchronized script copies; coordinate applicable updates there.

## Installation behavior to preserve

- Hermes Desktop and its agent stay native; only terminal tools optionally use Docker.
- Tailscale stays on the host. Never replace private Serve access with public Funnel.
- Personal profile names and credentials remain user choices. Preserve existing
  profiles and logins unless the user explicitly selects a reset.
- Do not log secrets, disable TLS/checksum/authentication checks, kill unrelated
  listeners, or imply a local check proves access from another tailnet device.
- State official-installer platform limits and source-build alternatives accurately.

Changes to a launcher snapshot require updating its pinned revision and SHA-256
in both start-setup launchers, matching test expectations, and the command guide.
Verify the actual archive and relevant platform checks; never bypass a mismatch.

## Review, licensing and maintenance

Describe what changed, why, and which checks passed. Note platform tests you could
not run. Use the pull request template. The maintainer, [@benczb](https://github.com/benczb),
reviews changes; there is no guaranteed response or release schedule.

By contributing, you agree your contribution is provided under this repository's
[MIT license](LICENSE). Preserve existing copyright and required third-party notices.
Bundled/downloaded dependencies retain their own licenses; the repository license
does not relicense them. Only contribute material you have permission to share.

See [the release checklist](docs/releasing.md) before proposing a release.
