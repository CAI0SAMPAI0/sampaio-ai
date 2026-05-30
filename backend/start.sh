#!/bin/sh
set -e

PYTHON_CMD="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_CMD" ]; then
  echo "Error: Python not found in container."
  exit 1
fi

"$PYTHON_CMD" -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  "$PYTHON_CMD" -m pip install -r requirements.txt
fi

echo "Starting backend..."
exec sh entrypoint.sh
