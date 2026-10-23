#!/usr/bin/env bash
# Linux: launch from a terminal in a desktop session.
cd "$(dirname "$0")" || exit 1
exec bash scripts/setup-macos-linux.sh
