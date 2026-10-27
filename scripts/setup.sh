#!/usr/bin/env bash
# ============================================================================
# CSSS 441 DevSecOps Pipeline - Development Environment Setup Script
# ============================================================================
set -euo pipefail

echo "==> Setting up CSSS 441 Secure Book Catalogue Environment..."

# Detect Python 3
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 is required but not found in PATH." >&2
    exit 1
fi

echo "--> Using Python: $($PYTHON_CMD --version)"

# Create virtual environment if not present
if [ ! -d ".venv" ]; then
    echo "--> Creating virtual environment in .venv..."
    $PYTHON_CMD -m venv .venv
fi

# Detect OS-specific venv path
if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/Scripts/activate
fi

echo "--> Upgrading pip..."
python -m pip install --upgrade pip

echo "--> Installing project and development dependencies..."
pip install -r requirements-dev.txt

if command -v pre-commit &>/dev/null; then
    echo "--> Installing pre-commit git hooks..."
    pre-commit install
fi

echo "==> Setup complete! Run 'pytest' to verify test suite."
