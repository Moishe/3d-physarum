# TODO: Web Application Implementation

This document outlines the plan to create a web application for the 3D Physarum model generator, allowing users to set parameters via a web interface and download generated STL files.

## Architecture Overview

- **Frontend**: React application with modern UI components
- **Backend**: FastAPI (Python) for API endpoints and simulation execution  
- **File Storage**: Local filesystem for STL file storage and serving
- **Real-time Updates**: WebSocket or Server-Sent Events for progress updates

## Frontend Implementation (React)

### 1. Project Setup & Dependencies
- [ ] Initialize React project with Vite
- [ ] Install UI library (Material-UI or Tailwind CSS + Headless UI)
- [ ] Add form validation library (React Hook Form + Zod)
- [ ] Add state management (Zustand or React Query)
- [ ] Setup WebSocket client for real-time updates

### 2. Core Components
- [ ] **ParameterForm**: Main form with all simulation parameters organized in sections:
  - Simulation Parameters (width, height, actors, steps, decay, etc.)
  - 3D Model Parameters (smooth, layer_height, threshold, smoothing options)
  - Output Parameters (filename)
  - Advanced Parameters (collapsed by default)
- [ ] **SimulationStatus**: Progress display component showing:
  - Current simulation step
  - Captured layers count
  - Actor count
  - Trail statistics
  - Estimated time remaining
- [ ] **ResultsDisplay**: Shows completed simulation results with:
  - Download button for STL file
  - Preview image
  - Model statistics (file size, mesh quality)
  - Parameters used (from JSON sidecar)

### 3. User Experience Features
- [ ] Parameter validation with real-time feedback
- [ ] Parameter presets (e.g., "Fast Preview", "High Quality", "Complex Structure")
- [ ] Responsive design for mobile/tablet use
- [ ] Progress visualization (progress bar + live stats)
- [ ] Error handling and user-friendly error messages
- [ ] Download history/recent generations list

## Backend Implementation (FastAPI)

### 1. Project Setup
- [ ] Create FastAPI application structure
- [ ] Add CORS middleware for frontend communication
- [ ] Setup WebSocket endpoint for real-time updates
- [ ] Add file serving endpoints for STL downloads
- [ ] Add logging and error handling

### 2. API Endpoints
- [ ] **POST /api/simulate**: Start new simulation
  - Accept all parameters from main.py argument parser
  - Validate parameters using existing validation logic
  - Return simulation job ID
  - Start background task for simulation execution
- [ ] **GET /api/simulate/{job_id}/status**: Get simulation status
  - Return current progress, step count, statistics
  - Include estimated completion time
- [ ] **GET /api/simulate/{job_id}/result**: Get completed simulation result
  - Return file paths, statistics, parameters used
- [ ] **GET /api/download/{job_id}/{file_type}**: Download files
  - Serve STL, JSON, and JPG files
  - Handle proper content-type headers
- [ ] **GET /api/simulate/{job_id}/preview**: Get preview image during simulation
- [ ] **DELETE /api/simulate/{job_id}**: Cancel running simulation

### 3. Background Task Management
- [ ] **SimulationManager**: Handle concurrent simulations
  - Job queue with unique IDs
  - Background task execution using FastAPI BackgroundTasks
  - Progress tracking and status updates
  - File cleanup after configurable retention period
- [ ] **ProgressReporter**: WebSocket/SSE progress updates
  - Real-time step updates
  - Trail statistics
  - Layer capture notifications
  - Error reporting

### 4. Integration with Existing Code
- [ ] **ParameterAdapter**: Convert web parameters to main.py format
  - Map frontend form data to argparse-like structure
  - Apply same validation logic from validate_parameters()
- [ ] **SimulationRunner**: Wrapper around existing simulation code
  - Import and use existing PhysarumSimulation, Model3DGenerator classes
  - Integrate with OutputManager for file handling
  - Add progress callbacks for web updates
  - Handle cancellation gracefully

## File Structure

```
web/
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── ParameterForm.tsx
│   │   │   ├── SimulationStatus.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   └── layout/
│   │   ├── hooks/
│   │   │   ├── useSimulation.ts
│   │   │   └── useWebSocket.ts
│   │   ├── types/
│   │   │   └── simulation.ts
│   │   ├── utils/
│   │   │   ├── validation.ts
│   │   │   └── api.ts
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/                    # FastAPI application  
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── simulation.py
│   │   │   │   └── files.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── simulation_manager.py
│   │   │   ├── parameter_adapter.py
│   │   │   └── progress_reporter.py
│   │   ├── models/
│   │   │   ├── simulation.py  # Pydantic models
│   │   │   └── responses.py
│   │   └── utils/
│   │       └── file_utils.py
│   ├── requirements.txt
│   └── Dockerfile (optional)
└── docker-compose.yml (optional)
```

## Development Tasks

### Phase 1: Backend Foundation
1. [ ] Setup FastAPI project structure
2. [ ] Create simulation parameter models with Pydantic
3. [ ] Implement parameter validation using existing logic
4. [ ] Create SimulationManager for job handling
5. [ ] Add basic simulation endpoint that works with existing code
6. [ ] Test STL file generation through API

### Phase 2: Real-time Communication
1. [ ] Implement WebSocket endpoint for progress updates
2. [ ] Modify existing simulation code to support progress callbacks
3. [ ] Create ProgressReporter for real-time updates
4. [ ] Test end-to-end simulation with progress tracking

### Phase 3: Frontend Core
1. [ ] Setup React project with chosen UI library
2. [ ] Create ParameterForm with all simulation parameters
3. [ ] Add form validation and parameter presets
4. [ ] Implement WebSocket client for progress updates
5. [ ] Create SimulationStatus component with real-time updates

### Phase 4: File Management & Downloads
1. [ ] Implement file serving endpoints
2. [ ] Add download functionality to frontend
3. [ ] Create ResultsDisplay component
4. [ ] Add preview image display during and after simulation
5. [ ] Implement file cleanup and retention policies

### Phase 5: Polish & Production
1. [ ] Add error handling and user feedback
2. [ ] Implement simulation history/recent results
3. [ ] Add responsive design and mobile support
4. [ ] Performance optimization and caching
5. [ ] Add Docker deployment configuration
6. [ ] Write deployment documentation

## Technical Considerations

### Performance
- Use background tasks for long-running simulations
- Implement job queuing to handle multiple concurrent requests
- Add file size limits and simulation time limits
- Consider Redis for job state persistence in production

### Security
- Input validation and sanitization
- File upload restrictions (if image upload feature added)
- Rate limiting on API endpoints
- Secure file serving (prevent directory traversal)

### Monitoring
- Add logging for simulation requests and completions
- Track simulation performance metrics
- Monitor disk usage for generated files
- Add health check endpoints

## Integration Points

The web application will reuse existing code:
- `PhysarumSimulation` class for core simulation
- `Model3DGenerator` and `SmoothModel3DGenerator` for 3D generation
- `OutputManager` for file handling
- `PreviewGenerator` for preview images
- Parameter validation logic from `main.py`

This approach ensures consistency between CLI and web interfaces while providing a modern web experience for users.