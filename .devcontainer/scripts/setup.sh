#!/bin/bash

# ABOUTME: Script to set up the development environment after devcontainer creation
# ABOUTME: Installs dependencies for both frontend and backend

set -e

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

echo "Setting up development environment..."

# Install uv if not already available
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    setup_uv_path
    # Add uv to PATH for future sessions
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
fi

# Ensure uv is in PATH
setup_uv_path

# Make scripts executable
chmod +x "$(dirname "${BASH_SOURCE[0]}")"/*.sh

# Clean up any existing virtual environment in the root directory
cd_project_root
cleanup_venv

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd_frontend
npm install

# Install backend dependencies
echo "Installing backend dependencies..."
cd_backend
# Ensure uv is available
setup_uv_path

# Clean up any existing virtual environment to avoid conflicts
cleanup_venv

uv sync --dev

echo "Setup complete!"
echo "Use .devcontainer/scripts/start-backend.sh to start the backend server"
echo "Use .devcontainer/scripts/start-frontend.sh to start the frontend server"