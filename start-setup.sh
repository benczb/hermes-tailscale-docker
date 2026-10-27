#!/usr/bin/env bash
# Launch the graphical companion from a verified, fixed source snapshot.
# Bash 3.2 compatible. Never run this launcher with sudo.
set -euo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || fail 'Run as your normal desktop user, not sudo/root.'
case "$(uname -s)" in
  Darwin|Linux) ;;
  *) fail 'Use start-setup.ps1 on native Windows.' ;;
esac
if [ -r /proc/version ] && grep -qiE 'microsoft|wsl' /proc/version; then
  fail 'Open native Windows PowerShell, not WSL, to start setup.'
fi
case "$(uname -m)" in x86_64|arm64|aarch64) ;; *) fail 'Requires a 64-bit Intel/AMD or ARM desktop.' ;; esac
for tool in curl unzip node npm; do
  command -v "$tool" >/dev/null || fail "Missing $tool. Install Node.js 24 LTS (nodejs.org) and your OS unzip tool, then retry."
done
node -e 'if (Number(process.versions.node.split(".")[0]) < 24) process.exit(1)' || fail 'Node.js 24 or newer is required. Install Node.js 24 LTS, then retry.'
if command -v shasum >/dev/null; then hash_tool=shasum;
elif command -v sha256sum >/dev/null; then hash_tool=sha256sum;
else fail 'A SHA-256 tool (shasum or sha256sum) is required.'; fi
revision=bd1260ac4249763a447db56faca582e4f5ade10c
expected=ceaec5f06ef08f7a78bb956d455aa51e3bae1b8285fc651181f26936e86a77a9
printf '%s\n' 'Starting Hermes Setup Companion preview from a fixed source revision.' 
printf '%s\n' 'This downloads source and npm dependencies and may compile native GUI helpers.'
printf '%s\n' 'Hermes/component installation starts only after you review settings in the wizard.'
work=$(mktemp -d "${TMPDIR:-/tmp}/hermes-companion.XXXXXXXX")
printf 'Setup files: %s\n' "$work"
printf '%s\n' 'If dependency preparation fails, install Python 3 and C/C++ build tools, then retry. Intel Mac Desktop source builds remain best effort.'
trap 'rm -f "$work/source.zip"' EXIT
curl --fail --show-error --silent --location --retry 2 --proto '=https' --tlsv1.2 \
  "https://codeload.github.com/benczb/hermes-tailscale-docker/zip/$revision" -o "$work/source.zip"
if [ "$hash_tool" = shasum ]; then actual=$(shasum -a 256 "$work/source.zip");
else actual=$(sha256sum "$work/source.zip"); fi
[ "${actual%% *}" = "$expected" ] || fail 'Source checksum mismatch. Nothing from the archive was executed. Download a fresh launcher or report the mismatch.'
unzip -q "$work/source.zip" -d "$work"
cd "$work/hermes-tailscale-docker-$revision/installer-ui"
npm ci --include=dev || fail "GUI dependency preparation failed. Check the build tools above. Files are retained at $work."
npm start
