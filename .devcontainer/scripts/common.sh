#!/bin/bash

# ABOUTME: Common utility functions for devcontainer scripts
# ABOUTME: Provides shared directory navigation and path resolution

# Get the absolute path to the project root directory
get_project_root() {
    local script_dir="$( cd "$( dirname "${BASH_SOURCE[1]}" )" && pwd )"
    echo "$script_dir/../.."
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