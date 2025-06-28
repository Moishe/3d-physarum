# ABOUTME: API routes for model registry and historical model management
# ABOUTME: Provides endpoints for listing, downloading, and managing persistent model history

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional, List
import os
import logging
from datetime import datetime

from ...models.responses import SuccessResponse, ErrorResponse
from ...core.model_registry import model_registry, ModelRecord

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/", response_model=Dict[str, Any])
async def list_models(
    source: Optional[str] = Query(None, description="Filter by source: 'cli', 'web', etc."),
    favorites: bool = Query(False, description="Only show favorite models"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Number of results to skip", ge=0)
):
    """List all registered models with optional filtering."""
    try:
        models = model_registry.list_models(
            source=source,
            favorite_only=favorites,
            limit=limit,
            offset=offset
        )
        
        # Convert to API format
        model_dicts = [model.to_dict() for model in models]
        
        # Get statistics for metadata
        stats = model_registry.get_statistics()
        
        return {
            "success": True,
            "data": {
                "models": model_dicts,
                "total_count": stats.get('total_models', 0),
                "returned_count": len(model_dicts),
                "offset": offset,
                "has_more": len(model_dicts) == limit
            },
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to list models: {str(e)}",
                "error_type": type(e).__name__
            }
        )


@router.get("/{model_id}", response_model=Dict[str, Any])
async def get_model(model_id: str):
    """Get detailed information about a specific model."""
    try:
        model = model_registry.get_model(model_id)
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Model not found",
                    "message": f"No model found with ID: {model_id}"
                }
            )
        
        return {
            "success": True,
            "data": model.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model {model_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get model: {str(e)}",
                "error_type": type(e).__name__,
                "model_id": model_id
            }
        )


@router.get("/{model_id}/download/{file_type}")
async def download_model_file(model_id: str, file_type: str):
    """Download files from a registered model."""
    try:
        model = model_registry.get_model(model_id)
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Model not found",
                    "message": f"No model found with ID: {model_id}"
                }
            )
        
        # Map file types to model attributes and content types
        file_mappings = {
            "stl": {
                "path_attr": "stl_path",
                "content_type": "application/octet-stream",
                "extension": ".stl"
            },
            "json": {
                "path_attr": "json_path", 
                "content_type": "application/json",
                "extension": ".json"
            },
            "jpg": {
                "path_attr": "jpg_path",
                "content_type": "image/jpeg", 
                "extension": ".jpg"
            },
            "preview": {
                "path_attr": "jpg_path",  # Preview is just the JPG file
                "content_type": "image/jpeg",
                "extension": ".jpg"
            }
        }
        
        if file_type not in file_mappings:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid file type",
                    "message": f"File type '{file_type}' is not supported. Valid types: {list(file_mappings.keys())}"
                }
            )
        
        mapping = file_mappings[file_type]
        file_path = getattr(model, mapping["path_attr"])
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "File not found",
                    "message": f"File '{file_type}' not found for model {model_id}"
                }
            )
        
        filename = f"{model.name}_{model_id}{mapping['extension']}"
        
        return FileResponse(
            file_path,
            media_type=mapping["content_type"],
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {file_type} for model {model_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to download file: {str(e)}",
                "error_type": type(e).__name__,
                "model_id": model_id,
                "file_type": file_type
            }
        )


@router.put("/{model_id}", response_model=SuccessResponse)
async def update_model(model_id: str, updates: Dict[str, Any]):
    """Update model metadata (name, favorite status, tags, etc.)."""
    try:
        model = model_registry.get_model(model_id)
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Model not found",
                    "message": f"No model found with ID: {model_id}"
                }
            )
        
        # Validate and filter updates
        allowed_updates = {}
        if 'name' in updates and isinstance(updates['name'], str):
            allowed_updates['name'] = updates['name'].strip()
        
        if 'favorite' in updates:
            allowed_updates['favorite'] = bool(updates['favorite'])
        
        if 'tags' in updates:
            if isinstance(updates['tags'], list):
                allowed_updates['tags'] = ','.join(str(tag).strip() for tag in updates['tags'])
            elif isinstance(updates['tags'], str):
                allowed_updates['tags'] = updates['tags'].strip()
        
        if not allowed_updates:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No valid updates provided",
                    "message": "Provide at least one of: name, favorite, tags"
                }
            )
        
        success = model_registry.update_model(model_id, allowed_updates)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Update failed",
                    "message": f"Failed to update model {model_id}"
                }
            )
        
        return SuccessResponse(
            message=f"Model {model_id} updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update model {model_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to update model: {str(e)}",
                "error_type": type(e).__name__,
                "model_id": model_id
            }
        )


@router.delete("/{model_id}", response_model=SuccessResponse)
async def delete_model(model_id: str, delete_files: bool = Query(False, description="Also delete associated files")):
    """Delete a model from the registry and optionally its files."""
    try:
        model = model_registry.get_model(model_id)
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Model not found",
                    "message": f"No model found with ID: {model_id}"
                }
            )
        
        success = model_registry.delete_model(model_id, delete_files=delete_files)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Delete failed",
                    "message": f"Failed to delete model {model_id}"
                }
            )
        
        message = f"Model {model_id} deleted from registry"
        if delete_files:
            message += " and files removed"
        
        return SuccessResponse(message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model {model_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to delete model: {str(e)}",
                "error_type": type(e).__name__,
                "model_id": model_id
            }
        )


@router.post("/scan", response_model=SuccessResponse)
async def scan_models():
    """Trigger a scan of the output directory to register new models."""
    try:
        registered_count = model_registry.scan_and_register_models()
        
        return SuccessResponse(
            message=f"Scan completed. Registered {registered_count} new models."
        )
        
    except Exception as e:
        logger.error(f"Failed to scan models: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to scan models: {str(e)}",
                "error_type": type(e).__name__
            }
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_model_statistics():
    """Get statistics about registered models."""
    try:
        stats = model_registry.get_statistics()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get model statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get statistics: {str(e)}",
                "error_type": type(e).__name__
            }
        )