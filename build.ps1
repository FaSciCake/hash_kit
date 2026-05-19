# build.ps1
# Activate the build virtual environment
.\.venv-build\Scripts\Activate.ps1

# Install the project and its build tools (non-editable - clean snapshot)
pip install ".[build]"

# Run PyInstaller using the spec file
pyinstaller hash_kit.spec

# Deactivate the environment
deactivate
