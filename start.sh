#!/bin/sh
set -e

# Root start script used by Railpack to build and start the app.
# It installs Python requirements for the backend and delegates to the backend entrypoint.

if [ -d backend ]; then
  echo "Building backend..."
  pip install --upgrade pip
  if [ -f backend/requirements.txt ]; then
    pip install -r backend/requirements.txt
  fi
  echo "Starting backend..."
  exec sh backend/entrypoint.sh
fi

echo "No backend directory found. Nothing to start."
exit 1
