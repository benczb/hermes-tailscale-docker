# Ask your agent to install Hermes

Give this instruction to an agent that can run commands on your computer:

> Install Hermes Desktop using https://github.com/benczb/hermes-tailscale-docker.
> Read AGENTS.md, README.md and docs/command-setup.md first. Check my OS and CPU,
> then help me prepare the documented prerequisites and launch the graphical
> setup wizard. Keep Hermes Desktop and its agent native. Use Docker only for
> terminal commands if I select it, and install/configure Tailscale on the host.
> Let me choose my profile name, dashboard username/password and TCP port
> (Default: 9119). I will enter secrets and approve sign-ins and OS prompts myself.
> Preserve existing Hermes data and logins. After setup, show what passed, what
> failed and what still needs verification, including access from another tailnet device.

This is an instruction to your agent, not a shell command. It works independently
of agent brand, provided the agent has local command access. An agent running only
in a remote cloud workspace cannot install desktop software on your own computer
unless you have separately connected that computer for local execution.

## What the agent should do

1. Read the current repository instructions and identify native Windows,
   macOS or Linux plus CPU architecture. Explain relevant platform limits.
2. Check Node.js 24+, npm and the command launcher's other prerequisites. Prepare
   missing tools through the computer's normal approved installation process;
   do not treat launching a wizard as permission to delete data or bypass controls.
3. Download and run `start-setup.sh` on macOS/Linux as the normal desktop user,
   or `start-setup.ps1` in native 64-bit Administrator Windows PowerShell under
   that user's account. Exact commands are in [command-setup.md](command-setup.md).
4. Let the user complete the form and review it before component installation.
   The command retrieves a fixed, checksum-verified source preview; it does not
   eliminate Node/compiler dependencies or build a prebuilt signed release.
5. Help with completion checks and failures. Inspect `installation-ready.txt`;
   verify a real Desktop conversation after provider/model configuration, and
   verify authenticated access from another authorized tailnet device when available.
   Report an unperformed check as pending, never passed.

The user still completes the original installer where supported, Tailscale and
provider sign-ins, OS approvals and possible restarts. An agent must not put
passwords or tokens into prompts, command arguments, logs or GitHub.

The pinned preview's original DMG installer is Apple Silicon-only. Intel Mac and
Linux require the explicit source alternative; Intel Desktop remains best effort.
Windows Docker mode may update WSL2 or require a reboot. Local terminal mode skips
Docker and WSL setup. No separate Linux backend address is required.

This repository is a community integration, not an official Nous Research installer.
See [support](../SUPPORT.md) if the agent cannot complete setup.
