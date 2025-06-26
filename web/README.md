# Physarum 3D Generator Web Interface

This directory contains the web interface for the Physarum 3D Generator, consisting of a React frontend and FastAPI backend that work together to provide an interactive web-based experience for generating 3D models from Physarum slime mold simulations.

## Project Structure

```
web/
├── backend/          # FastAPI backend server
│   ├── app/         # Application source code
│   ├── pyproject.toml
│   └── README.md
├── frontend/        # React frontend application
│   ├── src/         # Frontend source code
│   ├── package.json
│   └── README.md
└── README.md        # This file
```

## Prerequisites

- Python 3.12+ with uv package manager
- Node.js 18+ with npm
- Git

## Quick Start

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd web
```

### 2. Setup Backend

```bash
cd backend
uv sync
```

### 3. Setup Frontend

```bash
cd ../frontend
npm install
```

### 4. Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Development Workflow

### Running Both Services

For development, you need both services running simultaneously:

1. **Backend** (Port 8000): Handles simulation execution, file management, and API endpoints
2. **Frontend** (Port 5173): Provides the user interface and communicates with the backend

### Environment Configuration

The frontend is configured to connect to the backend via environment variables:

**Frontend (.env):**
```
VITE_API_BASE_URL=http://localhost:8000
```

### API Integration

The frontend communicates with the backend through:
- **POST /api/simulate** - Start new simulations
- **GET /api/simulate/{job_id}/status** - Poll simulation progress
- **GET /api/simulate/{job_id}/result** - Get completed results
- **GET /api/simulate/{job_id}/download/{file_type}** - Download files
- **DELETE /api/simulate/{job_id}** - Cancel simulations

## Building for Production

### Backend Production Build

```bash
cd backend
uv sync --frozen
# Deploy with your preferred ASGI server (uvicorn, gunicorn, etc.)
```

### Frontend Production Build

```bash
cd frontend
npm run build
# Serve the dist/ directory with your preferred web server
```

## Key Features

### Frontend Features
- **Interactive Parameter Form**: Adjust simulation and 3D model parameters
- **Preset Configurations**: Pre-configured parameter sets for different use cases
- **Real-time Progress**: Live updates during simulation execution
- **Results Display**: Preview and download generated models
- **Download History**: Track and manage previous simulations
- **Error Handling**: Comprehensive error display and recovery options

### Backend Features
- **Simulation Management**: Queue and execute simulations
- **Progress Tracking**: Real-time status updates
- **File Management**: Automatic cleanup and organization
- **Parameter Validation**: Comprehensive input validation
- **API Documentation**: Interactive Swagger/OpenAPI docs

## API Endpoints

### Simulation Management
- `POST /api/simulate` - Start simulation
- `GET /api/simulate/{job_id}/status` - Get status
- `GET /api/simulate/{job_id}/result` - Get result
- `DELETE /api/simulate/{job_id}` - Cancel simulation

### File Operations
- `GET /api/simulate/{job_id}/download/stl` - Download STL model
- `GET /api/simulate/{job_id}/download/json` - Download parameters
- `GET /api/simulate/{job_id}/download/preview` - Download preview image
- `GET /api/simulate/{job_id}/preview` - View preview image

### System Operations
- `GET /api/jobs` - List job statistics
- `POST /api/jobs/cleanup` - Clean up old jobs

## Troubleshooting

### Common Issues

**Backend won't start:**
- Ensure Python 3.12+ is installed
- Check that uv is properly installed: `uv --version`
- Verify dependencies: `cd backend && uv sync`

**Frontend won't start:**
- Ensure Node.js 18+ is installed: `node --version`
- Install dependencies: `cd frontend && npm install`
- Check for port conflicts (default: 5173)

**API Connection Issues:**
- Verify backend is running on port 8000
- Check CORS settings in backend configuration
- Ensure frontend .env file has correct API URL

**Simulation Errors:**
- Check backend logs for detailed error messages
- Verify simulation parameters are within valid ranges
- Ensure sufficient disk space for output files

### Development Tips

1. **Hot Reload**: Both services support hot reload during development
2. **Logging**: Backend provides detailed logging in development mode
3. **CORS**: Configured to allow frontend-backend communication
4. **Error Handling**: Comprehensive error handling on both frontend and backend

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure both frontend and backend remain compatible

## License

See the main project LICENSE file for details.