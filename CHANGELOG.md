# Changelog

This file records user-facing changes from the date it was introduced. It is not
a complete reconstruction of older commits. No GitHub release has been published yet.

## Unreleased

### Graphical installation update

- Windows graphical setup EXE with companion shortcuts; macOS app packages.
- Initiate missing Docker/Tailscale installation and open their apps. Keep the
  installer session alive through readiness/sign-in checks; retry failed component
  installations in the window.
- Start and verify the selected profile's Hermes gateway through `gateway ensure`
  before authenticated backend/forwarding completion. Windows runs the gateway
  from the limited-user task and keeps PowerShell workers hidden.
- Versioned graphical prerelease publishing with SHA-256 checksums.

### Added

- Command launchers for macOS/Linux and native Windows that verify a fixed source
  snapshot, prepare dependencies and open the graphical companion preview.
- Agent installation instructions with user-owned credentials and sign-ins.
- Contribution, conduct, security and support guidance, issue/PR templates and a
  release checklist.

### Changed

- Renamed the bundled template folder to `profiles/starter-agent` and labeled it
  **Starter Agent**. New ZIPs extract into `hermes-starter-agent-installer/`.
  Fresh script installs suggest `starter-agent`; saved profile choices, existing
  installed profiles/state and public ZIP download filenames are preserved.

### Current preview behavior

- Native Hermes Desktop and agent; optional Docker isolation for terminal tools.
- Host Tailscale with a selectable TCP port, default 9119.
- Personal profile name, dashboard username and password configured in the wizard.
- Original Desktop installer handoff on supported Windows/Apple Silicon systems;
  explicit source alternative on Intel Mac/Linux. Intel source builds are best effort.

### Known limitations

- Command launch requires Node.js 24+ and may require Python/native build tools.
- Original installer handoff, sign-ins, OS prompts and reboots require user action.
- Clean-machine validation and trusted publisher signing/notarization remain pending.
- A pinned launcher snapshot does not automatically gain later fixes on main.
