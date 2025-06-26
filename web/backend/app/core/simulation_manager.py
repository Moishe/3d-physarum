# ABOUTME: Manages background simulation jobs with progress tracking and cancellation
# ABOUTME: Handles concurrent simulations, job queuing, and WebSocket progress updates

import asyncio
import uuid
import time
import os
import logging
from typing import Dict, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum

from ..models.simulation import SimulationStatus, SimulationParameters, ProgressUpdate, MeshQualityMetrics


logger = logging.getLogger(__name__)


@dataclass
class SimulationJob:
    """Represents a simulation job with its state and metadata."""
    job_id: str
    parameters: SimulationParameters
    status: SimulationStatus = SimulationStatus.pending
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    progress: Optional[ProgressUpdate] = None
    result_files: Dict[str, str] = field(default_factory=dict)
    file_sizes: Dict[str, int] = field(default_factory=dict)
    mesh_quality: Optional[MeshQualityMetrics] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    cancel_requested: bool = False


class SimulationManager:
    """Manages simulation jobs with background execution and progress tracking."""
    
    def __init__(self, max_concurrent_jobs: int = 3, output_dir: str = "output"):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.output_dir = output_dir
        self.jobs: Dict[str, SimulationJob] = {}
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
        self.progress_callbacks: Dict[str, Callable[[ProgressUpdate], None]] = {}
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"SimulationManager initialized with max {max_concurrent_jobs} concurrent jobs")
    
    def generate_job_id(self) -> str:
        """Generate a unique job ID."""
        return str(uuid.uuid4())
    
    def start_simulation(self, parameters: SimulationParameters) -> str:
        """Start a new simulation job."""
        job_id = self.generate_job_id()
        
        # Create job record
        job = SimulationJob(
            job_id=job_id,
            parameters=parameters
        )
        self.jobs[job_id] = job
        
        logger.info(f"Created simulation job {job_id}")
        
        # Start background task if we haven't exceeded concurrent limit
        if len(self.active_jobs) < self.max_concurrent_jobs:
            self._start_job_task(job_id)
        else:
            logger.info(f"Job {job_id} queued - max concurrent jobs reached")
        
        return job_id
    
    def _start_job_task(self, job_id: str):
        """Start the actual background task for a job."""
        job = self.jobs[job_id]
        job.status = SimulationStatus.running
        job.started_at = time.time()
        
        # Create asyncio task for the simulation
        task = asyncio.create_task(self._run_simulation_async(job_id))
        self.active_jobs[job_id] = task
        
        logger.info(f"Started background task for job {job_id}")
    
    async def _run_simulation_async(self, job_id: str):
        """Run simulation in background thread with async wrapper."""
        job = self.jobs[job_id]
        
        try:
            # Run the actual simulation in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._run_simulation_sync,
                job_id
            )
            
        except Exception as e:
            logger.error(f"Simulation {job_id} failed: {e}", exc_info=True)
            job.status = SimulationStatus.failed
            job.error_message = str(e)
            job.completed_at = time.time()
            
        finally:
            # Clean up active job reference
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            # Start next queued job if any
            self._start_next_queued_job()
    
    def _run_simulation_sync(self, job_id: str):
        """Run the actual simulation synchronously (called from thread pool)."""
        job = self.jobs[job_id]
        
        try:
            # Import simulation modules (lazy import to avoid circular dependencies)
            import sys
            import os
            
            # Add parent directories to path to import main simulation code
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            project_root = os.path.dirname(os.path.dirname(backend_dir))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from physarum import PhysarumSimulation
            from model_3d import Model3DGenerator
            from model_3d_smooth import SmoothModel3DGenerator
            from output_manager import OutputManager
            from preview_generator import PreviewGenerator
            from .parameter_adapter import ParameterAdapter
            import numpy as np
            
            # Initialize output manager
            output_manager = OutputManager(default_output_dir=self.output_dir)
            
            # Use job_id as filename for web API
            web_filename = f"{job_id}.stl"
            
            # Convert parameters to args format for OutputManager
            args = ParameterAdapter.web_to_args(job.parameters, job_id)
            
            # Prepare output files
            final_stl_path, final_json_path, final_jpg_path = output_manager.prepare_output_files(
                web_filename, 
                args
            )
            
            # Create simulation with progress callback
            def progress_callback(step: int, total_steps: int, **kwargs):
                if job.cancel_requested:
                    raise InterruptedError("Simulation cancelled by user")
                
                # Create progress update
                progress = ProgressUpdate(
                    job_id=job_id,
                    step=step,
                    total_steps=total_steps,
                    layers_captured=kwargs.get('layers_captured', 0),
                    actor_count=kwargs.get('actor_count', 0),
                    max_trail=kwargs.get('max_trail', 0.0),
                    mean_trail=kwargs.get('mean_trail', 0.0),
                    estimated_completion_time=kwargs.get('estimated_completion_time'),
                    timestamp=time.time()
                )
                
                job.progress = progress
                
                # Call registered progress callback (for WebSocket updates)
                if job_id in self.progress_callbacks:
                    try:
                        self.progress_callbacks[job_id](progress)
                    except Exception as e:
                        logger.error(f"Error in progress callback for {job_id}: {e}")
            
            # Create simulation
            simulation = PhysarumSimulation(
                width=job.parameters.width,
                height=job.parameters.height,
                num_actors=job.parameters.actors,
                decay_rate=job.parameters.decay,
                view_radius=job.parameters.view_radius,
                view_distance=job.parameters.view_distance,
                speed=job.parameters.speed,
                initial_diameter=job.parameters.initial_diameter,
                death_probability=job.parameters.death_probability,
                spawn_probability=job.parameters.spawn_probability,
                diffusion_rate=job.parameters.diffusion_rate,
                direction_deviation=job.parameters.direction_deviation,
                image_path=None,  # Handle image data separately if needed
                speed_min=job.parameters.speed_min,
                speed_max=job.parameters.speed_max,
                spawn_speed_randomization=job.parameters.spawn_speed_randomization
            )
            
            # Create 3D model generator
            if job.parameters.smooth:
                generator = SmoothModel3DGenerator(
                    simulation=simulation,
                    layer_height=job.parameters.layer_height,
                    threshold=job.parameters.threshold,
                    smoothing_iterations=job.parameters.smoothing_iterations,
                    smoothing_type=job.parameters.smoothing_type.value,
                    taubin_lambda=job.parameters.taubin_lambda,
                    taubin_mu=job.parameters.taubin_mu,
                    preserve_features=job.parameters.preserve_features,
                    feature_angle=job.parameters.feature_angle,
                    background=job.parameters.background,
                    background_depth=job.parameters.background_depth,
                    background_margin=job.parameters.background_margin,
                    background_border=job.parameters.background_border,
                    border_height=job.parameters.border_height,
                    border_thickness=job.parameters.border_thickness
                )
            else:
                generator = Model3DGenerator(
                    simulation=simulation,
                    layer_height=job.parameters.layer_height,
                    threshold=job.parameters.threshold,
                    background=job.parameters.background,
                    background_depth=job.parameters.background_depth,
                    background_margin=job.parameters.background_margin,
                    background_border=job.parameters.background_border,
                    border_height=job.parameters.border_height,
                    border_thickness=job.parameters.border_thickness
                )
            
            # Run simulation with progress updates
            for step in range(job.parameters.steps):
                if job.cancel_requested:
                    raise InterruptedError("Simulation cancelled by user")
                
                simulation.step()
                
                # Capture layer at specified frequency
                if step % job.parameters.layer_frequency == 0:
                    generator.capture_layer()
                
                # Progress reporting
                if step % 20 == 0 or step == job.parameters.steps - 1:
                    trail_map = simulation.get_trail_map()
                    max_trail = np.max(trail_map)
                    mean_trail = np.mean(trail_map)
                    layers_captured = generator.get_layer_count()
                    actor_count = simulation.get_actor_count()
                    
                    # Estimate completion time
                    elapsed = time.time() - job.started_at
                    if step > 0:
                        estimated_total = elapsed * (job.parameters.steps / step)
                        estimated_remaining = max(0, estimated_total - elapsed)
                    else:
                        estimated_remaining = None
                    
                    progress_callback(
                        step, 
                        job.parameters.steps,
                        layers_captured=layers_captured,
                        actor_count=actor_count,
                        max_trail=max_trail,
                        mean_trail=mean_trail,
                        estimated_completion_time=estimated_remaining
                    )
            
            # Capture final layer
            generator.capture_layer()
            
            # Validate connectivity
            connectivity_valid = generator.validate_connectivity()
            
            # Generate preview image
            try:
                preview_generator = PreviewGenerator(width=800, height=800)
                preview_title = f"Physarum 3D Model - {job.parameters.steps} steps"
                preview_generator.generate_3d_preview_from_generator(
                    generator,
                    final_jpg_path,
                    threshold=job.parameters.threshold,
                    title=preview_title
                )
            except Exception as e:
                logger.warning(f"Could not generate preview for {job_id}: {e}")
            
            # Generate and save STL file
            generator.save_stl(final_stl_path)
            
            # Get file sizes and paths
            job.result_files = {
                "stl": final_stl_path,
                "json": final_json_path,
                "jpg": final_jpg_path
            }
            
            job.file_sizes = {}
            for file_type, file_path in job.result_files.items():
                if os.path.exists(file_path):
                    job.file_sizes[file_type] = os.path.getsize(file_path)
            
            # Get mesh quality metrics if requested and using smooth generator
            if job.parameters.mesh_quality and job.parameters.smooth and hasattr(generator, 'get_mesh_quality_metrics'):
                try:
                    metrics_dict = generator.get_mesh_quality_metrics()
                    if "error" not in metrics_dict:
                        job.mesh_quality = MeshQualityMetrics(**metrics_dict)
                except Exception as e:
                    logger.warning(f"Could not get mesh quality metrics for {job_id}: {e}")
            
            # Store simulation statistics
            job.statistics = {
                "layers_captured": generator.get_layer_count(),
                "final_actor_count": simulation.get_actor_count(),
                "connectivity_valid": connectivity_valid,
                "simulation_time": time.time() - job.started_at
            }
            
            # Mark as completed
            job.status = SimulationStatus.completed
            job.completed_at = time.time()
            
            logger.info(f"Simulation {job_id} completed successfully")
            
        except InterruptedError:
            job.status = SimulationStatus.cancelled
            job.completed_at = time.time()
            logger.info(f"Simulation {job_id} cancelled by user")
            
        except Exception as e:
            job.status = SimulationStatus.failed
            job.error_message = str(e)
            job.completed_at = time.time()
            logger.error(f"Simulation {job_id} failed: {e}", exc_info=True)
            raise
    
    def _start_next_queued_job(self):
        """Start the next queued job if any are waiting."""
        if len(self.active_jobs) >= self.max_concurrent_jobs:
            return
        
        # Find next pending job
        for job_id, job in self.jobs.items():
            if job.status == SimulationStatus.pending:
                self._start_job_task(job_id)
                break
    
    def get_job_status(self, job_id: str) -> Optional[SimulationJob]:
        """Get the current status of a job."""
        return self.jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running or pending job."""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        if job.status in [SimulationStatus.completed, SimulationStatus.failed, SimulationStatus.cancelled]:
            return False
        
        job.cancel_requested = True
        
        # If job is running, cancel the task
        if job_id in self.active_jobs:
            task = self.active_jobs[job_id]
            task.cancel()
        else:
            # Job is pending, mark as cancelled immediately
            job.status = SimulationStatus.cancelled
            job.completed_at = time.time()
        
        logger.info(f"Cancellation requested for job {job_id}")
        return True
    
    def register_progress_callback(self, job_id: str, callback: Callable[[ProgressUpdate], None]):
        """Register a callback function for progress updates."""
        self.progress_callbacks[job_id] = callback
    
    def unregister_progress_callback(self, job_id: str):
        """Unregister progress callback for a job."""
        if job_id in self.progress_callbacks:
            del self.progress_callbacks[job_id]
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs and their files."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if (job.status in [SimulationStatus.completed, SimulationStatus.failed, SimulationStatus.cancelled] 
                and job.completed_at 
                and current_time - job.completed_at > max_age_seconds):
                
                # Clean up result files
                for file_path in job.result_files.values():
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Could not remove file {file_path}: {e}")
                
                jobs_to_remove.append(job_id)
        
        # Remove job records
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            if job_id in self.progress_callbacks:
                del self.progress_callbacks[job_id]
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get overall job statistics."""
        status_counts = {}
        for status in SimulationStatus:
            status_counts[status.value] = 0
        
        for job in self.jobs.values():
            status_counts[job.status.value] += 1
        
        return {
            "total_jobs": len(self.jobs),
            "active_jobs": len(self.active_jobs),
            "status_counts": status_counts,
            "max_concurrent_jobs": self.max_concurrent_jobs
        }


# Global instance
simulation_manager = SimulationManager()