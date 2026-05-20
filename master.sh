#!/bin/bash
# master.sh
set -euo pipefail

# Validate command
if [ $# -eq 0 ]; then
    echo "Usage: ./master.sh <command> [args...]"
    echo "Commands: setup-dev, setup-build, collect-wheels, build"
    exit 1
fi

COMMAND="$1"
shift
SCRIPT="scripts/linux/${COMMAND}.sh"

if [ ! -f "$SCRIPT" ]; then
    echo "❌ Error: Script '$SCRIPT' not found."
    exit 1
fi

# Run target script with remaining arguments
bash "$SCRIPT" "$@"
