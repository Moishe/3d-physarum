# ABOUTME: FastAPI application entry point for the 3D Physarum model generator web backend
# ABOUTME: Provides REST API endpoints and WebSocket support for real-time simulation updates

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import traceback
import time

from .api.routes.simulation import router as simulation_router
from .api.routes.models import router as models_router
from .core.progress_reporter import progress_reporter
from .core.model_registry import model_registry
from .models.responses import HealthResponse
from .config import settings

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
if settings.CORS_ALLOW_ALL:
    # Allow all origins (for testing)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Can't use credentials with allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Specific origins only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that provides detailed debugging information."""
    # Extract request information
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        "timestamp": time.time()
    }
    
    # Log detailed exception information
    logger.error(
        f"UNHANDLED EXCEPTION:\n"
        f"Request: {request_info}\n"
        f"Exception: {type(exc).__name__}: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}",
        exc_info=True
    )
    
    # Return detailed error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "error_type": type(exc).__name__,
            "request_info": request_info if logger.level <= logging.DEBUG else None,
            "timestamp": time.time()
        }
    )

# Include API routes
app.include_router(simulation_router)
app.include_router(models_router)

# Startup event to scan for existing models
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting up application...")
    
    # Log CORS configuration for debugging
    if settings.CORS_ALLOW_ALL:
        logger.info("CORS: Allowing all origins")
    else:
        logger.info(f"CORS: Allowed origins: {settings.ALLOWED_ORIGINS}")
    
    # Ensure output directory exists
    settings.OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Scan for existing models in output directory
    try:
        registered_count = model_registry.scan_and_register_models()
        logger.info(f"Startup scan complete. Found {registered_count} models.")
    except Exception as e:
        logger.error(f"Failed to scan models on startup: {e}")
    
    logger.info("Application startup complete.")

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
    try:
        await progress_reporter.connect(websocket, job_id)
        await progress_reporter.handle_websocket_messages(websocket, job_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(
            f"WEBSOCKET ERROR for job {job_id}:\n"
            f"Exception: {type(e).__name__}: {str(e)}\n"
            f"Client: {websocket.client.host if websocket.client else 'unknown'}\n"
            f"Traceback: {traceback.format_exc()}",
            exc_info=True
        )
        try:
            await websocket.close(code=1011, reason=f"Server error: {str(e)}")
        except Exception:
            pass  # Connection might already be closed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")