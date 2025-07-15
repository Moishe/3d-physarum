# Devcontainer Configuration

This devcontainer is configured for developing the 3D Physarum simulation project, which includes both a Python backend (FastAPI) and a React/TypeScript frontend.

## What's Included

- **Python 3.11** with uv for dependency management
- **Node.js 18** for frontend development
- **VS Code extensions** for Python, TypeScript, and React development
- **Port forwarding** for both frontend (5173) and backend (8000)
- **Automatic dependency installation** on container startup
- **Automatic uv installation** if not already present

## Quick Start

1. Open this repository in VS Code
2. Click "Reopen in Container" when prompted, or use Command Palette > "Dev Containers: Reopen in Container"
3. Wait for the container to build and dependencies to install
4. Use the helper scripts to start development servers:

### Start Backend Server
```bash
.devcontainer/scripts/start-backend.sh
```
The backend will be available at http://localhost:8000

### Start Frontend Server
```bash
.devcontainer/scripts/start-frontend.sh
```
The frontend will be available at http://localhost:5173

### Run Tests
```bash
.devcontainer/scripts/run-tests.sh
```
Note: Frontend tests are not currently configured in package.json

## Development Workflow

1. **Backend Development**: 
   - Navigate to `web/backend/`
   - Use `uv run uvicorn app.main:app --reload` for development server
   - Tests: `uv run pytest`

2. **Frontend Development**:
   - Navigate to `web/frontend/`
   - Use `npm run dev` for development server
   - Build: `npm run build`

3. **Core Library Development**:
   - Navigate to `physarum-core/`
   - Install in development mode: `uv pip install -e .`

## Extensions Included

- **Python**: Full Python development support
- **TypeScript**: Enhanced TypeScript/React development
- **Tailwind CSS**: Utility-first CSS framework support
- **Prettier**: Code formatting
- **Spell Checker**: Code spell checking

## Port Forwarding

The devcontainer automatically forwards these ports:
- **5173**: Frontend development server (React/Vite)
- **8000**: Backend API server (FastAPI)

Both will be accessible from your local machine at `http://localhost:[port]`.

## Troubleshooting

### uv command not found

If you encounter "uv: command not found" errors, try the following:

1. **Reload your shell**: Open a new terminal tab or run `source ~/.bashrc` (or `source ~/.zshrc` if using zsh)

2. **Manual installation**: If uv is still not available, you can manually install it:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

3. **Check PATH**: Verify that uv is in your PATH:
   ```bash
   echo $PATH
   which uv
   ```

The devcontainer setup script automatically installs uv and adds it to your PATH, but sometimes you may need to reload your shell to pick up the changes.