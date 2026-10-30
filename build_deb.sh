#!/usr/bin/env bash
# Convenience shell script to build MsmLogo Debian package
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "    MsmLogo Linux .deb Package Builder    "
echo "=========================================="

python3 "$SCRIPT_DIR/build_deb.py"

echo ""
echo "🎉 Build complete! The .deb package is located in: $SCRIPT_DIR/dist/"
echo "To install on your system, run:"
echo "    sudo apt install ./dist/msmlogo_1.0.1_amd64.deb"
echo "Or:"
echo "    sudo dpkg -i ./dist/msmlogo_1.0.1_amd64.deb && sudo apt-get install -f"
