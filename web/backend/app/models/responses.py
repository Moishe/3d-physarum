# ABOUTME: Common response models for the API endpoints
# ABOUTME: Defines standard success and error response formats

from pydantic import BaseModel
from typing import Optional, Dict, Any


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str = "1.0.0"
    uptime: Optional[float] = None