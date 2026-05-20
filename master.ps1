# master.ps1
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Validate command
if ($args.Count -eq 0) {
    Write-Host "Usage: .\master.ps1 <command> [args...]"
    Write-Host "Commands: setup-dev, setup-build, download-build-wheels, build, activate-dev, activate-build"
    Write-Host
    exit 1
}

$command = $args[0]
$restArgs = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }
$scriptPath = Join-Path "scripts" "windows\$command.ps1"

if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Error: Script '$scriptPath' not found."
    exit 1
}

# Run target script with remaining arguments
& $scriptPath @restArgs
