#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define the path to your virtual environment
VENV_PATH="/root/agenticai-interview/agentic" # Confirm this path

# Define the path to your project directory (where main.py is located)
PROJECT_PATH="/root/agenticai-interview" # Confirm this path

# --- Pre-checks and Path setup ---
# Check if VENV_PATH exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment directory not found at $VENV_PATH" >&2
    exit 1
fi

# Check if PROJECT_PATH exists
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project directory not found at $PROJECT_PATH" >&2
    exit 1
fi

# Change to the project directory first
cd "$PROJECT_PATH"

# Activate the virtual environment using the explicit full path to activate script
# The `.` (dot) command is more universally compatible than `source`
. "$VENV_PATH/bin/activate"

# Check if activation was successful (e.g., if python is from venv)
if ! command -v python >/dev/null 2>&1 || [[ "$(command -v python)" != *"$VENV_PATH"* ]]; then
    echo "Error: Virtual environment activation failed. 'python' not found in venv path." >&2
    exit 1
fi

echo "Virtual environment activated: $(which python)"

# --- Run your application ---
# For PRODUCTION, it's highly recommended to use Gunicorn as a process manager
# for Uvicorn workers. Gunicorn handles graceful restarts, multiple workers for
# CPU utilization, and robust process management.
# You need to 'pip install gunicorn uvicorn' in your virtual environment.
# Uncomment the line below and comment out the direct uvicorn call for production:
# echo "Starting Gunicorn with Uvicorn workers..."
# exec gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# For DEVELOPMENT or if you insist on direct Uvicorn without Gunicorn for a simple setup:
# IMPORTANT: REMOVE '--reload' for PRODUCTION. It causes restarts on file changes.
echo "Starting Uvicorn directly (without Gunicorn)..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
