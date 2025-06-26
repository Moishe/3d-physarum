# ABOUTME: API routes for simulation management and execution
# ABOUTME: Handles simulation creation, status queries, results, and cancellation

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any
import os
import logging
import time
import psutil
import traceback
import sys

from ...models.simulation import (
    SimulationRequest, SimulationResponse, SimulationStatusResponse,
    SimulationResult, SimulationStatus, ProgressUpdate
)
from ...models.responses import SuccessResponse, ErrorResponse
from ...core.simulation_manager import simulation_manager
from ...core.parameter_adapter import ParameterAdapter


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["simulation"])


def get_debug_context(job_id: str = None, parameters: Dict = None) -> Dict[str, Any]:
    """Collect comprehensive debugging context for exception handling."""
    try:
        # System resource information
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        disk_usage = psutil.disk_usage('/')
        
        # Process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Simulation manager state
        manager_stats = simulation_manager.get_job_statistics()
        
        debug_context = {
            "timestamp": time.time(),
            "system": {
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent,
                "cpu_percent": cpu_percent,
                "disk_free_gb": round(disk_usage.free / (1024**3), 2),
                "disk_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
            },
            "process": {
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "pid": process.pid,
                "threads": process.num_threads()
            },
            "simulation_manager": {
                "total_jobs": manager_stats["total_jobs"],
                "active_jobs": manager_stats["active_jobs"],
                "max_concurrent": manager_stats["max_concurrent_jobs"],
                "status_counts": manager_stats["status_counts"]
            }
        }
        
        # Add job-specific context if available
        if job_id:
            debug_context["job_context"] = {
                "job_id": job_id,
                "exists": job_id in simulation_manager.jobs
            }
            
            if job_id in simulation_manager.jobs:
                job = simulation_manager.jobs[job_id]
                debug_context["job_context"].update({
                    "status": job.status.value,
                    "started_at": job.started_at,
                    "runtime_seconds": (time.time() - job.started_at) if job.started_at else None,
                    "has_progress": job.progress is not None,
                    "cancel_requested": job.cancel_requested,
                    "result_files_count": len(job.result_files)
                })
        
        # Add parameter context if available
        if parameters:
            debug_context["parameters"] = {
                "steps": getattr(parameters, 'steps', None),
                "actors": getattr(parameters, 'actors', None),
                "width": getattr(parameters, 'width', None),
                "height": getattr(parameters, 'height', None),
                "smooth": getattr(parameters, 'smooth', None)
            }
        
        return debug_context
        
    except Exception as e:
        # Fallback debug context if collecting fails
        return {
            "debug_collection_error": str(e),
            "timestamp": time.time(),
            "basic_info": {
                "job_id": job_id,
                "parameters_provided": parameters is not None
            }
        }


def log_detailed_exception(operation: str, exception: Exception, context: Dict[str, Any]):
    """Log exception with comprehensive debugging information."""
    # Get full stack trace
    exc_type, exc_value, exc_traceback = sys.exc_info()
    stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
    
    # Extract local variables from the traceback
    local_vars = {}
    if exc_traceback:
        frame = exc_traceback.tb_frame
        local_vars = {k: repr(v)[:200] for k, v in frame.f_locals.items() 
                     if not k.startswith('_') and k not in ['request', 'self']}
    
    logger.error(
        f"DETAILED EXCEPTION in {operation}:\n"
        f"Exception Type: {type(exception).__name__}\n"
        f"Exception Message: {str(exception)}\n"
        f"Context: {context}\n"
        f"Local Variables: {local_vars}\n"
        f"Stack Trace: {''.join(stack_trace)}",
        exc_info=True
    )


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
        debug_context = get_debug_context(parameters=request.parameters)
        log_detailed_exception("start_simulation", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to start simulation: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__
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
        debug_context = get_debug_context(job_id=job_id)
        log_detailed_exception("get_simulation_status", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get simulation status: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__,
                "job_id": job_id
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
        debug_context = get_debug_context(job_id=job_id)
        log_detailed_exception("get_simulation_result", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get simulation result: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__,
                "job_id": job_id
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
        debug_context = get_debug_context(job_id=job_id)
        log_detailed_exception("get_simulation_preview", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get preview: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__,
                "job_id": job_id
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
        debug_context = get_debug_context(job_id=job_id)
        log_detailed_exception("cancel_simulation", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to cancel simulation: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__,
                "job_id": job_id
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
        debug_context = get_debug_context(job_id=job_id)
        debug_context["file_type"] = file_type
        log_detailed_exception("download_simulation_file", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to download file: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__,
                "job_id": job_id,
                "file_type": file_type
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
        debug_context = get_debug_context()
        log_detailed_exception("list_jobs", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to get job statistics: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__
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
        debug_context = get_debug_context()
        debug_context["max_age_hours"] = max_age_hours
        log_detailed_exception("cleanup_old_jobs", e, debug_context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to cleanup jobs: {str(e)}",
                "debug_context": debug_context if logger.level <= logging.DEBUG else None,
                "error_type": type(e).__name__,
                "max_age_hours": max_age_hours
            }
        )