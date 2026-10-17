#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python 3.9+ is required. Install it using your approved host process; no packages were installed.' >&2
  exit 1
fi
exec python3 bootstrap.py "$@"
