# Installing Hermes for a user

This is a community setup companion, not an official Nous Research distribution.

For a user who asks to install from this repository, read README.md and
docs/command-setup.md first. Use start-setup.sh on native macOS/Linux or
start-setup.ps1 on native Windows to open the current graphical companion preview.
The launchers download and SHA-256-check a fixed source snapshot, prepare npm
dependencies, and open the wizard. They require Node.js 24+ and may require native
build tools. Do not substitute the older bootstrap.py/bootstrap.sh/bootstrap.ps1
flow: it has different prerequisites, profile behavior and installation defaults.

Keep Hermes Desktop and its agent runtime native. Docker is optional and is for
the terminal tool only. Tailscale runs on the host. No separate Linux machine or
backend IP is required. Let users choose a personal profile, dashboard username,
password, terminal backend, and TCP port (default 9119) in the graphical wizard.

Use the original Desktop installer on supported Windows/Apple Silicon systems.
The pinned preview's official DMG path does not support Intel Mac. Explain this
and let the user explicitly select its best-effort source alternative; do not
silently switch methods or promise Intel support. Linux also uses the explicit
source alternative. Respect bundled/Store-edition integration blocks.

Ask users to enter passwords, provider secrets, OS approvals and Tailscale sign-in
themselves. Do not put passwords in shell arguments, chat, commits or logs. Do not
remove existing Hermes data or replace an existing profile/login without explicit
user intent. Do not weaken checksum, TLS, authentication, or platform checks.

Local terminal mode skips Docker and Windows WSL setup. Docker mode on Windows
uses Docker Desktop's internal WSL2 backend; updates or a reboot may be needed.
Never claim WSL is unnecessary for this Windows Docker mode.

After setup, inspect installation-ready.txt and distinguish configured forwarding
from confirmed peer access. Verify port access from another authorized tailnet
device; do not use Funnel or expose an unauthenticated dashboard publicly.
Model/provider configuration and an actual Desktop conversation need verification.

The companion remains a preview. Passing automated tests does not prove installation
on a clean computer, publisher signing/notarization, or Intel Desktop compatibility.
