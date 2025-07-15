#!/bin/bash

# ABOUTME: Script to set up the development environment after devcontainer creation
# ABOUTME: Installs dependencies for both frontend and backend

set -e

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

echo "Setting up development environment..."

# Make scripts executable
chmod +x "$(dirname "${BASH_SOURCE[0]}")"/*.sh

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd_frontend
npm install

# Install backend dependencies
echo "Installing backend dependencies..."
cd_backend
uv sync --dev

echo "Setup complete!"
echo "Use .devcontainer/scripts/start-backend.sh to start the backend server"
echo "Use .devcontainer/scripts/start-frontend.sh to start the frontend server"