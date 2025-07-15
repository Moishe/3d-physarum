#!/bin/bash

# ABOUTME: Script to start the FastAPI backend server for development
# ABOUTME: Runs with hot reload enabled on port 8000

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

cd_backend
echo "Starting backend server..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload