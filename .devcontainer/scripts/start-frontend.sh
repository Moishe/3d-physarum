#!/bin/bash

# ABOUTME: Script to start the React/Vite frontend development server
# ABOUTME: Runs with hot reload enabled on port 3000

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

cd_frontend
echo "Starting frontend development server..."
npm run dev