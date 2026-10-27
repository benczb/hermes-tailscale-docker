# Hermes Setup graphical installer

This desktop wizard collects a profile name, dashboard username and confirmed password and a Docker/local terminal choice before installation starts. It runs the existing, bundled platform scripts in a background pseudoterminal and routes their dashboard prompts to the supplied presets. Users see component progress, required input and a verification report in a window.

The companion includes Electron for its own window; it does not bundle or replace Hermes Desktop. Attendees do not need Node, Python or Homebrew merely to open it. On macOS the setup script installs Homebrew if needed; Apple Command Line Tools setup may still require a system dialog. On Windows, the packaged executable requests administrator approval; Docker mode uses WSL2, while local-terminal mode skips Docker and WSL2 setup. Use the same normal Windows account with administrator rights; do not supply another account's credentials.

## Original Desktop installation

The default is **Original Hermes Desktop installer** on supported platforms, not a source build by this companion and not an agent Docker image. The companion opens Nous Research's original `Hermes-Setup.exe` or `Hermes-Setup.dmg` download. The user completes that installer, including its Desktop stage, then returns to the companion. The companion requires the original helper/completion marker, built Desktop and native CLI before applying configuration in reuse-only mode. A missing runtime stops setup; it never triggers a second checkout or companion Desktop build in this mode.

The original DMG bootstrap installer is Apple Silicon-only. Intel Mac and Linux users can deliberately choose **Source build · advanced alternative**; it is never selected automatically. Intel source builds are best effort. The original bootstrap installer can itself prepare/build dependencies, so it does not guarantee the absence of upstream build errors.

This preview supports the original bootstrap installer's standard native layout. Detected bundled/Store applications block this integration because their sealed runtime must not be silently replaced or confused with a separate PATH CLI. Configure that installed app directly until its payload mapping is supported.

## Current scope

- Native Hermes and Desktop on the current host, managed by the original installer by default or an explicit source-build alternative. Choose Docker sandbox (default) or local terminal; local mode runs commands with your account permissions and skips Docker/WSL setup.
- Profile name and dashboard credentials entered before installation, with a password visibility toggle.
- Preserve existing profiles and login by default; an explicit checkbox replaces an existing login.
- Read-only system inspection before the user approves installation.
- Live activity and component input inside the window, including Homebrew/sudo prompts when needed. Browser sign-in and OS/component dialogs remain external.
- Provider/model setup deferred to Hermes Desktop, so no terminal model wizard is opened.
- Retry with remembered profile/username. Passwords must be re-entered after a restart. No automatic reboot is initiated.
- Success requires the backend script to exit successfully and produce its installation verification report. Actual conversation and second-device tailnet access still need verification.

The wizard is a **preview**, not a replacement for the published terminal ZIPs yet. Its prompt bridge is covered by unit tests, but each OS still requires a clean-machine end-to-end run. Upstream prompt text can change; a manual component-response field is available in installation details when a component waits for input.

## Build and test

Use Node.js 24 or later on the build machine:

```sh
cd installer-ui
npm ci
npm test
npm start
npm run dist
```

The GUI build workflow creates separate Windows x64, Intel macOS, Apple Silicon macOS and Linux x64 packages. It bundles the exact platform scripts from the same commit. Build each package on its native OS so `node-pty` is built for the right platform and Electron ABI.

Mac preview ZIPs use an ad-hoc code signature, verified during the build. This validates package integrity but does not establish a trusted publisher or satisfy Gatekeeper notarization. Windows packages are unsigned portable executables that request administrator approval. Public distribution still needs Apple Developer signing/notarization and Windows Authenticode signing, plus clean-machine validation. Changing the archive format does not remove those trust requirements. Intel Macs use a source build of Hermes Desktop; an Apple Silicon-only upstream DMG is never substituted.

## Credential handling

Only profile name, username, Desktop installation method, port and terminal-backend choice are saved in the wizard's preferences. Passwords are validated in the main process, held in memory and supplied to known dashboard prompts through the child process's input. They are not passed in argv, environment variables, preferences or exported logs. Complete log lines are buffered before redaction so split output chunks cannot reveal the known password. All manual component responses are also redacted.

The existing backend scripts still write dashboard credentials into Hermes' protected local profile and installer login file. The UI does not change that storage policy. It does not upload credentials or include them in packages. The renderer has no Node access, no outbound network access and only narrowly scoped IPC methods; new windows and navigation are blocked.

Stopping is not an uninstall: already installed components and profiles remain. Resume reuses those components. Full automatic rollback, post-reboot auto-launch and unattended account OAuth are outside this preview.

Local terminal mode creates a `workspace` directory inside the selected Hermes profile and sets `terminal.cwd` to that host path. Docker mode uses `/workspace` inside the container. The final optional profile wizard restores both the selected backend and its workspace.

The Tailscale TCP port field is pre-filled with 9119 and labeled **(Default: 9119)**. Both platform scripts receive the chosen port. The local backend can reuse another saved/free port; the report distinguishes the local service from its private access address. Default radio/checkbox choices are labeled in the form. No username/password defaults are invented.
