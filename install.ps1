# Minimal installer for Windows PowerShell
param()
Set-StrictMode -Version Latest

$Root = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Set-Location $Root

Write-Host "Checking for Python..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Python not found in PATH. Please install Python 3.8+ and re-run this script." -ForegroundColor Red
    exit 1
}

$python = "python"
Write-Host "Using $python"

$venv = Join-Path $Root ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment in $venv..."
    & $python -m venv $venv
}

Write-Host "Activating virtual environment..."
# Dot-source the Activate script for PowerShell
. "$venv\Scripts\Activate.ps1"

Write-Host "Upgrading pip and installing requirements..."
& $python -m pip install --upgrade pip
if (Test-Path "requirements.txt") {
    & $python -m pip install -r requirements.txt
}

Write-Host "Starting server (press Ctrl+C to stop)..."
& $python server.py
