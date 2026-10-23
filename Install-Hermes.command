#!/bin/bash
# macOS: double-click after extracting the installer bundle.
cd "$(dirname "$0")" || exit 1
/bin/bash scripts/setup-macos-linux.sh
result=$?
printf '\nInstaller exit code: %s\n' "$result"
read -r -p 'Press Return to close. ' _
exit "$result"
