# ABOUTME: FastAPI application entry point for the 3D Physarum model generator web backend
# ABOUTME: Provides REST API endpoints and WebSocket support for real-time simulation updates

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
from typing import Dict, List
import uuid
import json

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

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info(f"WebSocket connected for job {job_id}")

    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_progress_update(self, job_id: str, data: dict):
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending progress update to {job_id}: {e}")
                self.disconnect(job_id)

manager = ConnectionManager()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "3d-physarum-api"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)

# File serving endpoints for downloads
@app.get("/api/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """Serve generated files (STL, JSON, JPG)"""
    # Define output directory (relative to project root)
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "..", "output")
    
    # Map file types to extensions and content types
    file_mappings = {
        "stl": {"ext": ".stl", "content_type": "application/octet-stream"},
        "json": {"ext": ".json", "content_type": "application/json"},
        "jpg": {"ext": ".jpg", "content_type": "image/jpeg"},
        "preview": {"ext": "_preview.jpg", "content_type": "image/jpeg"}
    }
    
    if file_type not in file_mappings:
        return {"error": "Invalid file type"}
    
    mapping = file_mappings[file_type]
    file_path = os.path.join(output_dir, f"{job_id}{mapping['ext']}")
    
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    return FileResponse(
        file_path,
        media_type=mapping["content_type"],
        filename=f"{job_id}{mapping['ext']}"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")