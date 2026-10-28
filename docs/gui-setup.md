# Install in a window

Download the matching graphical package from the [graphical preview release](https://github.com/benczb/hermes-tailscale-docker/releases/tag/v0.3.0-preview.1).
These are community companion packages, not the Nous Research Desktop installer itself.

## Windows

1. Open the **Windows setup EXE**. Install Hermes Setup Companion and use its
   Start menu or desktop shortcut. Approve UAC under your normal account.
2. Choose your profile name, dashboard username/password, Docker or local terminal,
   and Tailscale TCP port **(Default: 9119)**. Review and start installation.
3. If required, follow the original Hermes Desktop installer handoff in the window.
   Complete its Desktop installation, then return to the companion and check again.
4. The companion installs missing Docker Desktop and Tailscale through winget and
   opens their apps. Complete Docker's first-run dialogs and Tailscale's browser
   sign-in/device approval. Readiness checks continue automatically in the window.
5. After configuration, the user-login task starts the native Hermes gateway and
   requires a ready result before starting the authenticated backend. Tailscale
   TCP forwarding is configured after those checks pass.

You do not need Node.js or an open PowerShell window to use this packaged app.
It runs PowerShell internally as a background worker. The advanced terminal ZIP
and source-launch command are different entry points and still use a shell.

Windows Docker mode uses WSL2 internally. If enabling Windows features requires
a restart, the companion explains it. Restart yourself, reopen its shortcut and
re-enter your password to resume. It does not reboot automatically. Local terminal
mode skips Docker and WSL preparation.

## macOS

1. Choose the **Apple Silicon** or **Intel** app ZIP, extract it, then open
   **Hermes Setup Companion.app**. You can move the app to Applications for reuse.
2. Enter your settings, review, and start. The original Hermes Desktop installer
   path supports Apple Silicon. Intel requires explicitly selecting the source
   alternative; Intel Desktop builds remain best effort.
3. The companion installs missing Homebrew and Docker/Tailscale casks, then opens
   the apps. Approve Docker's first-run dialogs and Tailscale's sign-in and macOS
   VPN/system-extension permissions. Setup keeps checking and resumes automatically.
4. Source builds may trigger Apple's Command Line Tools installation and need
   OpenSSL/compiler dependencies. The launcher verifies gateway readiness before
   the authenticated backend and private Tailscale forwarding are declared ready.

You do not need Node.js or Terminal merely to open the packaged companion. Source
builds and missing component installation can still require system/build tools.

## If a component needs attention

Use **Open Docker Desktop** or **Open Tailscale** in the window. Startup/connection
checks run every five seconds. Failed component installs are not repeated by a
timer: resolve the reported error and select **Retry this step**. You keep the
same setup session and settings. Cancelling keeps already installed components.

The companion checks the gateway and authenticated backend; a real model response
and access from another authorized tailnet device still need verification.

## Preview limits

Windows packages are unsigned, and macOS packages use an ad-hoc signature without
Apple notarization. OS trust checks can prevent opening them; do not disable
system protections to work around a block. Publisher signing and clean-machine
validation are still pending. A checksum verifies the downloaded bytes against
the published manifest, not publisher identity. SHA256SUMS is attached to the release.

Linux x64 users can use the AppImage on a supported graphical desktop; Electron
and AppImage/FUSE system requirements still apply. Linux/Intel Hermes Desktop uses
the explicit source alternative. The source-launch and terminal ZIP options are
documented in [command setup](command-setup.md) and [advanced setup](advanced-setup.md).
