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
    export PATH="$HOME/.cargo/bin:$PATH"
    # Add uv to PATH for future sessions
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
fi

# Ensure uv is in PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Make scripts executable
chmod +x "$(dirname "${BASH_SOURCE[0]}")"/*.sh

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd_frontend
npm install

# Install backend dependencies
echo "Installing backend dependencies..."
cd_backend
# Ensure uv is available
export PATH="$HOME/.cargo/bin:$PATH"
uv sync --dev

echo "Setup complete!"
echo "Use .devcontainer/scripts/start-backend.sh to start the backend server"
echo "Use .devcontainer/scripts/start-frontend.sh to start the frontend server"