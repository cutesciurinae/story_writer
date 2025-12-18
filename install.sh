#!/usr/bin/env bash
# Minimal installer for Unix/macOS
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Checking for Python..."
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=python
else
  echo "Python not found. Please install Python 3.8+ and re-run this script." >&2
  exit 1
fi

echo "Using $PYTHON_CMD"

VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR..."
  $PYTHON_CMD -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

echo "Upgrading pip and installing requirements..."
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

echo "Starting server (press Ctrl+C to stop)..."
exec python server.py
