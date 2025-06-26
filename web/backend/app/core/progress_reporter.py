# ABOUTME: Handles real-time progress reporting via WebSocket connections
# ABOUTME: Manages WebSocket connections and broadcasts simulation progress updates

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

from ..models.simulation import ProgressUpdate
from .simulation_manager import simulation_manager


logger = logging.getLogger(__name__)


class ProgressReporter:
    """Manages WebSocket connections and progress updates for simulations."""
    
    def __init__(self):
        # job_id -> set of WebSocket connections
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.connection_jobs: Dict[WebSocket, str] = {}  # websocket -> job_id for cleanup
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Register a new WebSocket connection for a specific job."""
        await websocket.accept()
        
        if job_id not in self.connections:
            self.connections[job_id] = set()
        
        self.connections[job_id].add(websocket)
        self.connection_jobs[websocket] = job_id
        
        # Register progress callback with simulation manager
        if job_id not in [ws_job for ws_job in self.connections.keys() if len(self.connections[ws_job]) > 1]:
            # This is the first connection for this job, register callback
            simulation_manager.register_progress_callback(job_id, self._progress_callback)
        
        logger.info(f"WebSocket connected for job {job_id} (total connections: {len(self.connections[job_id])})")
        
        # Send initial status if available
        await self._send_initial_status(websocket, job_id)
    
    def disconnect(self, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        if websocket not in self.connection_jobs:
            return
        
        job_id = self.connection_jobs[websocket]
        
        # Remove from connections
        if job_id in self.connections:
            self.connections[job_id].discard(websocket)
            
            # If no more connections for this job, unregister callback
            if not self.connections[job_id]:
                del self.connections[job_id]
                simulation_manager.unregister_progress_callback(job_id)
                logger.info(f"Unregistered progress callback for job {job_id} (no more connections)")
        
        del self.connection_jobs[websocket]
        logger.info(f"WebSocket disconnected for job {job_id}")
    
    async def _send_initial_status(self, websocket: WebSocket, job_id: str):
        """Send initial job status to a newly connected WebSocket."""
        try:
            job = simulation_manager.get_job_status(job_id)
            if not job:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Job {job_id} not found"
                }))
                return
            
            # Send current status
            status_message = {
                "type": "status",
                "job_id": job_id,
                "status": job.status.value,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "error_message": job.error_message
            }
            
            # Add progress info if available
            if job.progress:
                status_message["progress"] = job.progress.dict()
            
            await websocket.send_text(json.dumps(status_message))
            
            # If job is completed, send final result info
            if job.status.value in ["completed", "failed", "cancelled"]:
                result_message = {
                    "type": "final",
                    "job_id": job_id,
                    "status": job.status.value,
                    "completed_at": job.completed_at,
                    "error_message": job.error_message
                }
                
                if job.status.value == "completed" and job.result_files:
                    result_message["files"] = {
                        file_type: f"/api/simulate/{job_id}/download/{file_type}"
                        for file_type in job.result_files.keys()
                    }
                    result_message["statistics"] = job.statistics
                    if job.mesh_quality:
                        result_message["mesh_quality"] = job.mesh_quality.dict()
                
                await websocket.send_text(json.dumps(result_message))
                
        except Exception as e:
            logger.error(f"Error sending initial status for {job_id}: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error getting job status: {str(e)}"
                }))
            except:
                pass  # WebSocket might be closed
    
    def _progress_callback(self, progress: ProgressUpdate):
        """Callback function called by SimulationManager for progress updates."""
        if progress.job_id not in self.connections:
            return
        
        # Create message
        message = {
            "type": "progress",
            **progress.dict()
        }
        
        # Send to all connections for this job
        asyncio.create_task(self._broadcast_to_job(progress.job_id, message))
    
    async def _broadcast_to_job(self, job_id: str, message: dict):
        """Broadcast a message to all WebSocket connections for a specific job."""
        if job_id not in self.connections:
            return
        
        # Get list of connections (copy to avoid modification during iteration)
        connections = list(self.connections[job_id])
        
        # Send message to all connections
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket for job {job_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected WebSockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_job_completion(self, job_id: str):
        """Broadcast job completion message to all connected clients."""
        job = simulation_manager.get_job_status(job_id)
        if not job:
            return
        
        message = {
            "type": "final",
            "job_id": job_id,
            "status": job.status.value,
            "completed_at": job.completed_at,
            "error_message": job.error_message
        }
        
        if job.status.value == "completed" and job.result_files:
            message["files"] = {
                file_type: f"/api/simulate/{job_id}/download/{file_type}"
                for file_type in job.result_files.keys()
            }
            message["statistics"] = job.statistics
            if job.mesh_quality:
                message["mesh_quality"] = job.mesh_quality.dict()
        
        await self._broadcast_to_job(job_id, message)
    
    async def handle_websocket_messages(self, websocket: WebSocket, job_id: str):
        """Handle incoming WebSocket messages (mostly keep-alive)."""
        try:
            while True:
                # Wait for messages (mostly ping/pong for keep-alive)
                message = await websocket.receive_text()
                
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif data.get("type") == "request_status":
                        await self._send_initial_status(websocket, job_id)
                except json.JSONDecodeError:
                    # Ignore invalid JSON
                    pass
                    
        except WebSocketDisconnect:
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error in WebSocket handler for job {job_id}: {e}")
            self.disconnect(websocket)


# Global instance
progress_reporter = ProgressReporter()