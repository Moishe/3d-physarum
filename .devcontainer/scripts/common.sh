#!/bin/bash

# ABOUTME: Common utility functions for devcontainer scripts
# ABOUTME: Provides shared directory navigation and path resolution

# Ensure uv is in PATH
setup_uv_path() {
    export PATH="$HOME/.local/bin:$PATH"
}

# Get the absolute path to the project root directory
get_project_root() {
    # Find the .devcontainer directory and navigate to its parent
    local current_dir="$(pwd)"
    while [[ "$current_dir" != "/" ]]; do
        if [[ -d "$current_dir/.devcontainer" ]]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    
    # Fallback: assume we're in the scripts directory
    local script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    echo "$( cd "$script_dir/../.." && pwd )"
}

# Navigate to the project root
cd_project_root() {
    cd "$(get_project_root)"
}

# Navigate to the backend directory
cd_backend() {
    cd "$(get_project_root)/web/backend"
}

# Navigate to the frontend directory  
cd_frontend() {
    cd "$(get_project_root)/web/frontend"
}