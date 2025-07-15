#!/bin/bash

# ABOUTME: Script to run all tests for the project
# ABOUTME: Runs both Python backend tests and frontend tests

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

EXIT_CODE=0

echo "Running backend tests..."
cd_backend
if ! uv run pytest; then
    echo "Backend tests failed"
    EXIT_CODE=1
fi

echo "Running frontend tests..."
cd_frontend
# Check if test script exists first
if grep -q '"test"' package.json; then
    if ! npm run test; then
        echo "Frontend tests failed"
        EXIT_CODE=1
    fi
else
    echo "Frontend tests not configured yet"
fi

echo "Running root project tests..."
cd_project_root
if ! uv run pytest; then
    echo "Root project tests failed"
    EXIT_CODE=1
fi

exit $EXIT_CODE