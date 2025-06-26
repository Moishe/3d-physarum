# ABOUTME: API routes for simulation management and execution
# ABOUTME: Handles simulation creation, status queries, results, and cancellation

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any
import os
import logging
import time

from ...models.simulation import (
    SimulationRequest, SimulationResponse, SimulationStatusResponse,
    SimulationResult, SimulationStatus, ProgressUpdate
)
from ...models.responses import SuccessResponse, ErrorResponse
from ...core.simulation_manager import simulation_manager
from ...core.parameter_adapter import ParameterAdapter


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["simulation"])


@router.post("/simulate", response_model=SimulationResponse)
async def start_simulation(request: SimulationRequest):
    """Start a new simulation job."""
    try:
        # Validate parameters
        validation_errors = ParameterAdapter.validate_web_parameters(request.parameters)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Parameter validation failed",
                    "message": "One or more parameters are invalid",
                    "validation_errors": validation_errors
                }
            )
        
        # Get complexity estimate
        complexity = ParameterAdapter.estimate_complexity(request.parameters)
        
        # Start simulation
        job_id = simulation_manager.start_simulation(request.parameters)
        
        logger.info(f"Started simulation job {job_id} with {complexity['complexity_level']} complexity")
        
        return SimulationResponse(
            job_id=job_id,
            status=SimulationStatus.pending,
            message=f"Simulation started with {complexity['complexity_level']} complexity. Estimated runtime: {complexity['estimated_runtime_seconds']:.1f} seconds."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting simulation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to start simulation: {str(e)}"
            }
        )


@router.get("/simulate/{job_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(job_id: str):
    """Get the current status of a simulation job."""
    try:
        job = simulation_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "message": f"No simulation job found with ID: {job_id}"
                }
            )
        
        return SimulationStatusResponse(
            job_id=job_id,
            status=job.status,
            progress=job.progress,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting simulation status for {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get simulation status: {str(e)}"
            }
        )


@router.get("/simulate/{job_id}/result", response_model=SimulationResult)
async def get_simulation_result(job_id: str):
    """Get the result of a completed simulation."""
    try:
        job = simulation_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "message": f"No simulation job found with ID: {job_id}"
                }
            )
        
        if job.status != SimulationStatus.completed:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Job not completed",
                    "message": f"Simulation job {job_id} is not completed (status: {job.status.value})"
                }
            )
        
        # Convert absolute paths to relative paths for API response
        relative_files = {}
        for file_type, file_path in job.result_files.items():
            relative_files[file_type] = os.path.basename(file_path)
        
        return SimulationResult(
            job_id=job_id,
            status=job.status,
            parameters=job.parameters,
            files=relative_files,
            statistics=job.statistics,
            mesh_quality=job.mesh_quality,
            completed_at=job.completed_at,
            file_sizes=job.file_sizes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting simulation result for {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get simulation result: {str(e)}"
            }
        )


@router.get("/simulate/{job_id}/preview")
async def get_simulation_preview(job_id: str):
    """Get preview image for a simulation (during or after completion)."""
    try:
        job = simulation_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "message": f"No simulation job found with ID: {job_id}"
                }
            )
        
        # Look for preview image file
        preview_path = None
        if job.result_files and "jpg" in job.result_files:
            preview_path = job.result_files["jpg"]
        else:
            # Try to find preview file in output directory
            output_dir = simulation_manager.output_dir
            potential_paths = [
                os.path.join(output_dir, f"{job_id}.jpg"),
                os.path.join(output_dir, f"{job_id}_preview.jpg")
            ]
            for path in potential_paths:
                if os.path.exists(path):
                    preview_path = path
                    break
        
        if not preview_path or not os.path.exists(preview_path):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Preview not found",
                    "message": f"No preview image found for simulation {job_id}"
                }
            )
        
        return FileResponse(
            preview_path,
            media_type="image/jpeg",
            filename=f"{job_id}_preview.jpg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preview for {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get preview: {str(e)}"
            }
        )


@router.delete("/simulate/{job_id}", response_model=SuccessResponse)
async def cancel_simulation(job_id: str):
    """Cancel a running or pending simulation."""
    try:
        success = simulation_manager.cancel_job(job_id)
        
        if not success:
            job = simulation_manager.get_job_status(job_id)
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Job not found",
                        "message": f"No simulation job found with ID: {job_id}"
                    }
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Cannot cancel job",
                        "message": f"Job {job_id} cannot be cancelled (status: {job.status.value})"
                    }
                )
        
        return SuccessResponse(
            message=f"Cancellation requested for simulation {job_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling simulation {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to cancel simulation: {str(e)}"
            }
        )


@router.get("/simulate/{job_id}/download/{file_type}")
async def download_simulation_file(job_id: str, file_type: str):
    """Download files from a completed simulation."""
    try:
        job = simulation_manager.get_job_status(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "message": f"No simulation job found with ID: {job_id}"
                }
            )
        
        if job.status != SimulationStatus.completed:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Job not completed",
                    "message": f"Simulation job {job_id} is not completed"
                }
            )
        
        # Map file types to extensions and content types
        file_mappings = {
            "stl": {"content_type": "application/octet-stream", "extension": ".stl"},
            "json": {"content_type": "application/json", "extension": ".json"},
            "jpg": {"content_type": "image/jpeg", "extension": ".jpg"},
            "preview": {"content_type": "image/jpeg", "extension": ".jpg"}
        }
        
        if file_type not in file_mappings:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid file type",
                    "message": f"File type '{file_type}' is not supported. Valid types: {list(file_mappings.keys())}"
                }
            )
        
        # Get file path
        file_path = None
        if file_type == "preview":
            file_type = "jpg"  # Preview is just the JPG file
        
        if file_type in job.result_files:
            file_path = job.result_files[file_type]
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "File not found",
                    "message": f"File '{file_type}' not found for simulation {job_id}"
                }
            )
        
        mapping = file_mappings[file_type]
        filename = f"{job_id}{mapping['extension']}"
        
        return FileResponse(
            file_path,
            media_type=mapping["content_type"],
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_type} for {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to download file: {str(e)}"
            }
        )


@router.get("/jobs", response_model=Dict[str, Any])
async def list_jobs():
    """Get statistics about all simulation jobs."""
    try:
        stats = simulation_manager.get_job_statistics()
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting job statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get job statistics: {str(e)}"
            }
        )


@router.post("/jobs/cleanup", response_model=SuccessResponse)
async def cleanup_old_jobs(max_age_hours: int = 24):
    """Clean up old completed jobs and their files."""
    try:
        simulation_manager.cleanup_completed_jobs(max_age_hours)
        return SuccessResponse(
            message=f"Cleanup completed for jobs older than {max_age_hours} hours"
        )
        
    except Exception as e:
        logger.error(f"Error during job cleanup: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to cleanup jobs: {str(e)}"
            }
        )