# Start setup with a command

For attendees who prefer a command, these launchers fetch the files automatically
and open the graphical setup wizard. There is no ZIP to find or extract yourself.
Downloads still happen in the background. Package downloads remain another option.

This is a **source-launch preview**, not a prebuilt installer release. Install
[Node.js 24 LTS](https://nodejs.org/) first. Its native GUI helper may also need
Python 3 and C/C++ build tools: Xcode Command Line Tools on macOS; build-essential
or your distribution's equivalent on Linux; Visual Studio Build Tools with
**Desktop development with C++** on Windows. Linux needs a graphical desktop and
Electron's desktop libraries. Missing prerequisites stop preparation with guidance;
these launchers do not install Node or compiler tools themselves.

## macOS / Linux

Run as your normal desktop user in Terminal, without sudo:

```bash
f=$(mktemp) && curl -fsSL https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/start-setup.sh -o "$f" && bash "$f"
```

Requires curl, unzip, a SHA-256 utility and Node.js/npm. The same command works in
macOS zsh because it runs the downloaded launcher with Bash explicitly.

## Windows

Open **64-bit Windows PowerShell as Administrator** under your normal account:

```powershell
$f = Join-Path $env:TEMP ('hermes-start-' + [guid]::NewGuid().ToString('N') + '.ps1'); Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/start-setup.ps1 -OutFile $f -ErrorAction Stop; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $f
```

Use native PowerShell, not WSL. If organization policy blocks scripts, use your
approved installation process. The command does not override organization policy.

## What happens

1. Check launcher prerequisites, download source revision
   `bd1260ac4249763a447db56faca582e4f5ade10c`, and verify its embedded SHA-256.
2. Extract to a fresh temporary directory. Existing Hermes folders are untouched
   during launcher preparation. Run `npm ci --include=dev` with the lockfile and
   open the graphical companion using `npm start`.
3. Enter profile name, personal dashboard username/password, terminal choice and
   Tailscale TCP port **(Default: 9119)** before approving component installation.
4. Follow the wizard's original Desktop installer handoff on supported platforms,
   then configure the native runtime, optional Docker terminal and host Tailscale.
   Original-install completion, sign-ins, OS approvals and reboots still require
   the user. This is guided setup, not unattended installation.

The original Desktop installer in this preview supports Windows and Apple Silicon.
Intel Mac and Linux require explicitly selecting **Source build — advanced
alternative**. Intel Desktop remains best effort. Only terminal commands run in
Docker when selected; neither Hermes Desktop nor the agent is a Docker container.
Local terminal mode skips Docker/WSL preparation. Windows Docker mode may update
WSL2 or request a reboot. There is no separate Linux backend IP to supply.

The printed temporary directory retains the extracted source/dependencies for
troubleshooting. The source ZIP is removed on exit. Native components and profiles
installed by the wizard persist independently of the launcher. Do not delete the
temporary directory while the wizard is running. Launchers do not auto-update a
running wizard or remove an earlier setup directory.

The command trusts this public repository's current launcher. The embedded hash
checks the fixed source archive; it is not an independent publisher signature.
For an immutable command, replace `main` in the launcher URL with a reviewed
commit SHA that contains the launcher. If GitHub regenerates the archive with
different bytes, verification stops; do not bypass it. npm dependencies are
lockfile-controlled and install scripts/native compilation still execute.

## Ask your agent

> Install Hermes using https://github.com/benczb/hermes-tailscale-docker.
> Read AGENTS.md and docs/command-setup.md, check this computer's prerequisites,
> and start the graphical wizard. Keep Hermes native and use Docker only for
> terminal commands if I select it. Let me enter passwords and approve sign-ins.

Agents can help prepare prerequisites and start setup. They cannot remove official
Intel Mac limitations or guarantee successful clean-machine installation.
