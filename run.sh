#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$SCRIPT_DIR/libs:$HOME/.local/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
exec python3 "$SCRIPT_DIR/msmlogo/main.py" "$@"
