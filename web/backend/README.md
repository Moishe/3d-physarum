# 3D Physarum Model Generator - Backend API

Backend API server for the 3D Physarum model generator web application. Provides REST API endpoints and WebSocket support for real-time simulation execution and progress tracking.

## Features

- **REST API** for simulation management (create, monitor, download results)
- **WebSocket support** for real-time progress updates
- **Background job processing** with concurrent simulation support
- **Parameter validation** using the same logic as the CLI
- **File management** with automatic cleanup and unique naming
- **Complexity estimation** for runtime prediction
- **Job cancellation** support

## Quick Start

### Prerequisites

- Python 3.9+
- uv package manager (or pip)

### Installation & Launch

From the **project root directory** (`/user_home/workspace`):

```bash
# Install dependencies (if not already done)
uv add fastapi uvicorn websockets python-multipart pydantic

# Start the backend server
uv run uvicorn web.backend.app.main:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
uv run uvicorn web.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"3d-physarum-api","version":"1.0.0","uptime":null}
```

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## API Endpoints

### Simulation Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/simulate` | Start a new simulation |
| `GET` | `/api/simulate/{job_id}/status` | Get simulation status |
| `GET` | `/api/simulate/{job_id}/result` | Get completed simulation result |
| `GET` | `/api/simulate/{job_id}/preview` | Get preview image |
| `DELETE` | `/api/simulate/{job_id}` | Cancel running simulation |

### File Downloads

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/simulate/{job_id}/download/stl` | Download STL file |
| `GET` | `/api/simulate/{job_id}/download/json` | Download parameters JSON |
| `GET` | `/api/simulate/{job_id}/download/jpg` | Download preview image |

### System Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/jobs` | Get job statistics |
| `POST` | `/api/jobs/cleanup` | Clean up old jobs |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `WS` | `/ws/{job_id}` | Real-time progress updates for a job |

## Usage Examples

### 1. Start a Simple Simulation

```bash
curl -X POST "http://localhost:8000/api/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "width": 100,
      "height": 100,
      "actors": 50,
      "steps": 100,
      "decay": 0.01,
      "threshold": 0.1,
      "output": "my_model.stl"
    }
  }'
```

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "pending",
  "message": "Simulation started with medium complexity. Estimated runtime: 45.2 seconds."
}
```

### 2. Monitor Progress

```bash
# Get current status
curl "http://localhost:8000/api/simulate/abc123.../status"

# Response:
{
  "job_id": "abc123...",
  "status": "running",
  "progress": {
    "step": 25,
    "total_steps": 100,
    "layers_captured": 5,
    "actor_count": 48,
    "max_trail": 1.234,
    "mean_trail": 0.056,
    "estimated_completion_time": 30.5
  }
}
```

### 3. Download Results

```bash
# Get result metadata
curl "http://localhost:8000/api/simulate/abc123.../result"

# Download STL file
curl -o model.stl "http://localhost:8000/api/simulate/abc123.../download/stl"

# Download preview image
curl -o preview.jpg "http://localhost:8000/api/simulate/abc123.../download/jpg"
```

### 4. WebSocket for Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/abc123...');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  if (data.type === 'progress') {
    console.log(`Step ${data.step}/${data.total_steps}`);
    console.log(`Progress: ${(data.step/data.total_steps*100).toFixed(1)}%`);
  } else if (data.type === 'final') {
    console.log('Simulation completed!');
    console.log('Files:', data.files);
  }
};
```

## Configuration

### Environment Variables

- `UVICORN_HOST` - Host to bind to (default: 0.0.0.0)
- `UVICORN_PORT` - Port to bind to (default: 8000)
- `OUTPUT_DIR` - Directory for output files (default: output)

### Server Settings

The backend supports these configuration options:

- **Max concurrent jobs**: 3 (configurable in `SimulationManager`)
- **File retention**: 24 hours (configurable via cleanup endpoint)
- **CORS origins**: Configured for React dev servers (localhost:3000, localhost:5173)

## Output Files

Generated files are stored in the `output/` directory with job IDs as filenames:

```
output/
├── abc123-def456-ghi789.stl      # 3D model file
├── abc123-def456-ghi789.json     # Parameters and metadata
└── abc123-def456-ghi789.jpg      # Preview image
```

## Development

### Project Structure

```
web/backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/routes/
│   │   └── simulation.py          # Simulation API routes
│   ├── core/
│   │   ├── simulation_manager.py  # Background job management
│   │   ├── parameter_adapter.py   # Parameter conversion & validation
│   │   └── progress_reporter.py   # WebSocket progress updates
│   ├── models/
│   │   ├── simulation.py          # Pydantic models for API
│   │   └── responses.py           # Standard response models
│   └── utils/
├── pyproject.toml                 # Python package configuration
└── README.md                      # This file
```

### Adding New Features

1. **New API endpoints**: Add to `app/api/routes/`
2. **Background tasks**: Extend `SimulationManager`
3. **Parameter validation**: Update `ParameterAdapter`
4. **WebSocket events**: Extend `ProgressReporter`

### Testing

```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio httpx

# Run tests (when available)
uv run pytest
```

## Integration with Frontend

The backend is designed to work with the React frontend in `../frontend/`. Key integration points:

- **CORS**: Pre-configured for React dev servers
- **WebSocket**: Real-time progress updates
- **File serving**: Direct download links for generated files
- **Error handling**: Structured error responses for UI feedback

## Troubleshooting

### Common Issues

1. **Server won't start**:
   ```bash
   # Check if port is in use
   lsof -i :8000
   
   # Use different port
   uv run uvicorn web.backend.app.main:app --port 8001
   ```

2. **Import errors**:
   ```bash
   # Ensure you're in the project root
   cd /user_home/workspace
   
   # Check Python path
   uv run python -c "import sys; print(sys.path)"
   ```

3. **Simulation fails**:
   ```bash
   # Check server logs for detailed error messages
   # Verify all simulation dependencies are installed
   uv run python -c "import physarum, model_3d, model_3d_smooth"
   ```

4. **WebSocket connection issues**:
   - Ensure firewall allows WebSocket connections
   - Check browser developer tools for connection errors
   - Verify job ID is correct in WebSocket URL

### Logs

Server logs are printed to stdout/stderr. For debugging:

```bash
# Start with debug logging
uv run uvicorn web.backend.app.main:app --log-level debug

# Or redirect to file
uv run uvicorn web.backend.app.main:app > backend.log 2>&1
```

## Performance Notes

- **Concurrent simulations**: Limited to 3 by default to prevent resource exhaustion
- **Memory usage**: Depends on simulation parameters (grid size × actors × steps)
- **File cleanup**: Automatic cleanup of files older than 24 hours
- **Background processing**: Non-blocking simulation execution using thread pool

## License

Same as the main project.