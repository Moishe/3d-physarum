# ABOUTME: Pydantic models for simulation parameters and API responses
# ABOUTME: Defines request/response schemas for the 3D Physarum simulation API

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum


class SmoothingType(str, Enum):
    """Smoothing algorithm types for smooth surface generation."""
    laplacian = "laplacian"
    taubin = "taubin"
    feature_preserving = "feature_preserving"
    boundary_outline = "boundary_outline"


class SimulationStatus(str, Enum):
    """Status of a simulation job."""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class SimulationParameters(BaseModel):
    """Parameters for starting a new simulation."""
    
    # Simulation parameters
    width: int = Field(default=100, ge=1, le=2000, description="Grid width in pixels")
    height: int = Field(default=100, ge=1, le=2000, description="Grid height in pixels")
    actors: int = Field(default=50, ge=1, le=10000, description="Number of Physarum actors")
    steps: int = Field(default=100, ge=1, le=10000, description="Number of simulation steps")
    decay: float = Field(default=0.01, ge=0.0, le=1.0, description="Trail decay rate")
    view_radius: int = Field(default=3, ge=0, le=20, description="Actor sensing radius")
    view_distance: int = Field(default=10, ge=0, le=50, description="Actor sensing distance")
    speed: float = Field(default=1.0, ge=0.0, le=10.0, description="Actor movement speed")
    speed_min: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Minimum speed for initial actors")
    speed_max: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Maximum speed for initial actors")
    spawn_speed_randomization: float = Field(default=0.2, ge=0.0, le=1.0, description="Factor for randomizing spawned actor speeds")
    initial_diameter: float = Field(default=20.0, ge=1.0, le=1000.0, description="Initial circle diameter for actor placement")
    death_probability: float = Field(default=0.001, ge=0.0, le=1.0, description="Age-based death probability per step")
    spawn_probability: float = Field(default=0.005, ge=0.0, le=1.0, description="Probability of spawning new actors")
    diffusion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Pheromone diffusion rate")
    direction_deviation: float = Field(default=1.57, ge=0.0, le=3.14159, description="Maximum direction deviation in radians")
    image: Optional[str] = Field(default=None, description="Base64 encoded JPEG image for initial actor placement")
    
    # 3D model parameters
    smooth: bool = Field(default=False, description="Use smooth surface generation (marching cubes)")
    layer_height: float = Field(default=1.0, ge=0.1, le=10.0, description="Height of each layer in 3D model")
    threshold: float = Field(default=0.1, ge=0.0, le=1.0, description="Minimum trail strength for 3D inclusion")
    layer_frequency: int = Field(default=5, ge=1, le=100, description="Capture layer every N steps")
    smoothing_iterations: int = Field(default=2, ge=0, le=20, description="Number of smoothing iterations")
    smoothing_type: SmoothingType = Field(default=SmoothingType.taubin, description="Type of smoothing algorithm")
    taubin_lambda: float = Field(default=0.5, gt=0.0, lt=1.0, description="Taubin smoothing lambda parameter")
    taubin_mu: float = Field(default=-0.52, gt=-1.0, lt=0.0, description="Taubin smoothing mu parameter")
    preserve_features: bool = Field(default=False, description="Preserve sharp features during smoothing")
    feature_angle: float = Field(default=60.0, gt=0.0, lt=180.0, description="Feature edge angle threshold in degrees")
    mesh_quality: bool = Field(default=False, description="Show detailed mesh quality metrics")
    background: bool = Field(default=False, description="Add a solid rectangular background")
    background_depth: float = Field(default=2.0, gt=0.0, le=50.0, description="Depth/thickness of the background layer")
    background_margin: float = Field(default=0.05, ge=0.0, le=1.0, description="Background margin as fraction of bounds")
    background_border: bool = Field(default=False, description="Add a raised border around the background edges")
    border_height: float = Field(default=1.0, gt=0.0, le=50.0, description="Height of the border walls")
    border_thickness: float = Field(default=0.5, gt=0.0, le=10.0, description="Thickness of the border walls")
    
    # Output parameters
    output: str = Field(default="physarum_3d_model.stl", description="Output STL filename")
    
    @validator('speed_min', 'speed_max')
    def validate_speeds(cls, v, values):
        """Validate speed min/max relationships."""
        if v is not None:
            if v <= 0:
                raise ValueError("Speed values must be positive")
            if 'speed_min' in values and 'speed_max' in values:
                if values.get('speed_min') is not None and v is not None:
                    if values['speed_min'] > v:
                        raise ValueError("Speed minimum must be less than or equal to speed maximum")
        return v


class SimulationRequest(BaseModel):
    """Request to start a new simulation."""
    parameters: SimulationParameters
    
    
class SimulationResponse(BaseModel):
    """Response when starting a new simulation."""
    job_id: str
    status: SimulationStatus
    message: str


class ProgressUpdate(BaseModel):
    """Real-time progress update for a simulation."""
    job_id: str
    step: int
    total_steps: int
    layers_captured: int
    actor_count: int
    max_trail: float
    mean_trail: float
    estimated_completion_time: Optional[float] = None
    timestamp: float


class SimulationStatusResponse(BaseModel):
    """Response for simulation status queries."""
    job_id: str
    status: SimulationStatus
    progress: Optional[ProgressUpdate] = None
    error_message: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class MeshQualityMetrics(BaseModel):
    """Mesh quality metrics for completed simulations."""
    vertex_count: int
    face_count: int
    volume: float
    surface_area: float
    is_watertight: bool
    is_winding_consistent: bool
    print_ready: bool
    issues: List[str]


class SimulationResult(BaseModel):
    """Result of a completed simulation."""
    job_id: str
    status: SimulationStatus
    parameters: SimulationParameters
    files: Dict[str, str]  # file_type -> relative_path
    statistics: Dict[str, Any]
    mesh_quality: Optional[MeshQualityMetrics] = None
    completed_at: float
    file_sizes: Dict[str, int]  # file_type -> size_in_bytes


class ErrorResponse(BaseModel):
    """Error response for API failures."""
    error: str
    message: str
    job_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None