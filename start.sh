#!/bin/sh
set -e

# Root start script used by Railpack to build and start the app.
# It installs Python requirements for the backend and delegates to the backend entrypoint.

if [ -d backend ]; then
  echo "Building backend..."
  PYTHON_CMD="$(command -v python3 || command -v python || true)"
  if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python not found in container."
    exit 1
  fi

  "$PYTHON_CMD" -m pip install --upgrade pip
  if [ -f backend/requirements.txt ]; then
    "$PYTHON_CMD" -m pip install -r backend/requirements.txt
  fi

  echo "Starting backend..."
  exec sh backend/entrypoint.sh
fi

echo "No backend directory found. Nothing to start."
exit 1
