#!/bin/bash
# download-build-wheels.sh
# Run from HashKit project root (where pyproject.toml lives)

# Exit on error, undefined vars, or pipe failures
set -euo pipefail

VENV_DIR=".venv-build"

# Check if virtual environment exists, create if not
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Virtual environment '$VENV_DIR' not found. Creating..."
    /home/SGC.OIL.GAS/fatkhutdinov_vd/dev_repo/python/Python-3.13.4/python -m venv "$VENV_DIR"
else
    echo "Virtual environment '$VENV_DIR' already exists. Skipping creation."
fi

# Activate the build virtual environment
source .venv-build/bin/activate

WHEEL_DIR=".build_wheels_linux"

# Remove old directory if it exists (fresh start)
if [ -d "$WHEEL_DIR" ]; then
    rm -rf "$WHEEL_DIR"
fi

# Download all wheels
pip download ".[build]" -d $WHEEL_DIR --index-url http://sng-alfa-sdev-1.sgc.oil.gas:8082/repository/pypi-all/simple --trusted-host sng-alfa-sdev-1.sgc.oil.gas

echo "Done! All wheels are now in '$WHEEL_DIR' folder!"

# Deactivate the environment
deactivate

# A fix to make this script executable:
# chmod +x download-build-wheels.sh
