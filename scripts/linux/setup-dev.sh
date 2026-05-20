#!/bin/bash
# setup-dev.sh

# Exit on error, undefined vars, or pipe failures
set -euo pipefail

VENV_DIR=".venv-dev"

# Check if virtual environment exists, create if not
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Virtual environment '$VENV_DIR' not found. Creating..."
    /home/SGC.OIL.GAS/fatkhutdinov_vd/dev_repo/python/Python-3.13.4/python -m venv "$VENV_DIR"
else
    echo "Virtual environment '$VENV_DIR' already exists. Skipping creation."
fi

# Activate the dev virtual environment
source "$VENV_DIR/bin/activate"

# Install the project and its dev tools - Local repository version
# pip install -e . --index-url http://sng-alfa-sdev-1.sgc.oil.gas:8082/repository/pypi-all/simple --trusted-host sng-alfa-sdev-1.sgc.oil.gas
# or
pip install -e .

# Install the project and its dev tools - Local directory version
# pip install -e . --no-index --find-links=".build_wheels_linux"

# Deactivate the environment
deactivate

# A fix to make this script executable:
# chmod +x setup-dev.sh
