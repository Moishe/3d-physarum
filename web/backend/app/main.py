# ABOUTME: FastAPI application entry point for the 3D Physarum model generator web backend
# ABOUTME: Provides REST API endpoints and WebSocket support for real-time simulation updates

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from .api.routes.simulation import router as simulation_router
from .core.progress_reporter import progress_reporter
from .models.responses import HealthResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="3D Physarum Model Generator API",
    description="Backend API for generating 3D models from Physarum simulations",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(simulation_router)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="3d-physarum-api"
    )

# WebSocket endpoint for real-time progress updates
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await progress_reporter.connect(websocket, job_id)
    await progress_reporter.handle_websocket_messages(websocket, job_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")