# Hermes Starter Agent Setup

A guided installer for **Hermes Desktop, optional Docker terminal tools and
Tailscale** on your computer. Choose your profile name, dashboard login and access
port **(Default: 9119)** before installation.

Hermes Desktop and its agent run natively. Only terminal commands optionally run
in Docker. Tailscale provides private remote access; no separate Linux computer
or backend IP is required.

## Starter Agent safeguards

The bundled [`SOUL.md`](profiles/starter-agent/SOUL.md) asks your agent to:

- Protect secrets and use only the access needed for a task.
- Treat external content as untrusted.
- Ask for approval before consequential actions.
- Verify results before reporting success.

The template folder is `profiles/starter-agent`. Personalize `[YOUR NAME]` and
choose your own installed profile name. Existing customized profiles are preserved.
These safeguards guide agent behavior; they are not a technical security boundary.

## Get started

**Ask your agent** — copy this instruction:

> Install Hermes Desktop using https://github.com/benczb/hermes-tailscale-docker.
> Read AGENTS.md and docs/command-setup.md, check my computer's prerequisites,
> and open the graphical setup wizard. Keep Hermes native; use Docker only for
> terminal commands if I select it. Let me enter credentials and approve sign-ins.
> Preserve existing profiles and report anything still needing verification.

The agent needs command access to your computer. [Agent setup guide](docs/agent-install.md).

**Start with a command** — the launcher fetches files and opens the wizard.
Requires Node.js 24+, npm and potentially Python/C++ build tools.
[Commands for macOS, Linux and Windows](docs/command-setup.md).

**Download a package** — these are advanced terminal installers that use the
source-build path by default, rather than the graphical wizard:

| macOS | Linux | Windows |
|---|---|---|
| [Download ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-macos.zip) | [Download ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-linux.zip) | [Download ZIP](https://raw.githubusercontent.com/benczb/hermes-tailscale-docker/main/downloads/hermes-workshop-windows.zip) |

Extract into `hermes-starter-agent-installer/` and use the included launcher.
[Package instructions](docs/advanced-setup.md) · [Checksums](downloads/SHA256SUMS)

## Before you install

- This community companion is a **preview**, not an official Nous Research installer.
- The wizard uses the original Desktop installer on supported Windows and Apple
  Silicon systems. Intel Mac and Linux require the explicit source alternative;
  Intel Desktop builds remain best effort.
- Windows Docker mode uses Docker Desktop's internal WSL2 backend and may need
  updates or a restart. Local terminal mode skips Docker/WSL preparation.
- You complete sign-ins and OS approvals. Model setup and access from another
  authorized tailnet device still need verification after installation.
- Clean-machine validation and trusted publisher signing/notarization remain pending.
  There are no published GitHub releases yet.

## Help and contributions

[Setup and recovery](docs/advanced-setup.md) · [Support](SUPPORT.md) ·
[Contributing](CONTRIBUTING.md) · [Code of conduct](CODE_OF_CONDUCT.md) ·
[Security reporting](SECURITY.md) · [Changelog](CHANGELOG.md)

Maintained by [@benczb](https://github.com/benczb). [MIT license](LICENSE).
