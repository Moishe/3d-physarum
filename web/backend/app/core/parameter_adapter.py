# ABOUTME: Converts web API parameters to main.py argument format and validates them
# ABOUTME: Ensures compatibility between web interface and existing CLI simulation code

from argparse import Namespace
from typing import List, Optional
from ..models.simulation import SimulationParameters


class ParameterAdapter:
    """Converts web parameters to main.py format and applies validation."""
    
    @staticmethod
    def web_to_args(parameters: SimulationParameters, job_id: Optional[str] = None) -> Namespace:
        """Convert web parameters to argparse Namespace format used by main.py."""
        
        # Create args namespace with all parameters
        args = Namespace()
        
        # Simulation parameters
        args.width = parameters.width
        args.height = parameters.height
        args.actors = parameters.actors
        args.steps = parameters.steps
        args.decay = parameters.decay
        args.view_radius = parameters.view_radius
        args.view_distance = parameters.view_distance
        args.speed = parameters.speed
        args.speed_min = parameters.speed_min
        args.speed_max = parameters.speed_max
        args.spawn_speed_randomization = parameters.spawn_speed_randomization
        args.initial_diameter = parameters.initial_diameter
        args.death_probability = parameters.death_probability
        args.spawn_probability = parameters.spawn_probability
        args.diffusion_rate = parameters.diffusion_rate
        args.direction_deviation = parameters.direction_deviation
        args.image = None  # Image handling would need special processing
        
        # 3D model parameters
        args.smooth = parameters.smooth
        args.layer_height = parameters.layer_height
        args.threshold = parameters.threshold
        args.layer_frequency = parameters.layer_frequency
        args.smoothing_iterations = parameters.smoothing_iterations
        args.smoothing_type = parameters.smoothing_type.value
        args.taubin_lambda = parameters.taubin_lambda
        args.taubin_mu = parameters.taubin_mu
        args.preserve_features = parameters.preserve_features
        args.feature_angle = parameters.feature_angle
        args.mesh_quality = parameters.mesh_quality
        args.background = parameters.background
        args.background_depth = parameters.background_depth
        args.background_margin = parameters.background_margin
        args.background_border = parameters.background_border
        args.border_height = parameters.border_height
        args.border_thickness = parameters.border_thickness
        
        # Output parameters
        if job_id:
            # Use job_id as the base filename
            if parameters.output.endswith('.stl'):
                base_name = parameters.output[:-4]
            else:
                base_name = parameters.output
            args.output = f"{job_id}.stl"
        else:
            args.output = parameters.output
        
        # Control flags
        args.quiet = True  # Always quiet for web API
        args.verbose = False
        
        return args
    
    @staticmethod
    def validate_web_parameters(parameters: SimulationParameters) -> List[str]:
        """Validate web parameters using comprehensive validation logic."""
        # Use direct validation instead of importing from main.py to avoid dependency issues
        return ParameterAdapter._manual_validation(parameters)
    
    @staticmethod
    def _manual_validation(parameters: SimulationParameters) -> List[str]:
        """Manual validation of parameters as fallback."""
        errors = []
        
        # Grid dimensions
        if parameters.width <= 0:
            errors.append("Width must be positive")
        if parameters.height <= 0:
            errors.append("Height must be positive")
        
        # Actor parameters - only require positive actors if no image is provided
        if parameters.image is None and parameters.actors <= 0:
            errors.append("Number of actors must be positive when no image is provided")
        if parameters.steps <= 0:
            errors.append("Number of steps must be positive")
        
        # Rates and distances
        if parameters.decay < 0 or parameters.decay > 1:
            errors.append("Decay rate must be between 0.0 and 1.0")
        if parameters.view_radius < 0:
            errors.append("View radius must be non-negative")
        if parameters.view_distance < 0:
            errors.append("View distance must be non-negative")
        if parameters.speed < 0:
            errors.append("Speed must be non-negative")
        
        # Speed min/max validation
        if parameters.speed_min is not None and parameters.speed_min <= 0:
            errors.append("Speed minimum must be positive")
        if parameters.speed_max is not None and parameters.speed_max <= 0:
            errors.append("Speed maximum must be positive")
        if (parameters.speed_min is not None and parameters.speed_max is not None 
            and parameters.speed_min > parameters.speed_max):
            errors.append("Speed minimum must be less than or equal to speed maximum")
        
        if parameters.spawn_speed_randomization < 0 or parameters.spawn_speed_randomization > 1:
            errors.append("Spawn speed randomization must be between 0.0 and 1.0")
        
        # 3D model parameters
        if parameters.layer_height <= 0:
            errors.append("Layer height must be positive")
        if parameters.threshold < 0:
            errors.append("Threshold must be non-negative")
        if parameters.layer_frequency <= 0:
            errors.append("Layer frequency must be positive")
        if parameters.smoothing_iterations < 0:
            errors.append("Smoothing iterations must be non-negative")
        if parameters.taubin_lambda <= 0 or parameters.taubin_lambda >= 1:
            errors.append("Taubin lambda must be between 0 and 1 (exclusive)")
        if parameters.taubin_mu >= 0 or parameters.taubin_mu <= -1:
            errors.append("Taubin mu must be between -1 and 0 (exclusive)")
        if parameters.feature_angle <= 0 or parameters.feature_angle >= 180:
            errors.append("Feature angle must be between 0 and 180 degrees")
        
        # Background parameters
        if parameters.background_depth <= 0:
            errors.append("Background depth must be positive")
        if parameters.background_margin < 0 or parameters.background_margin > 1:
            errors.append("Background margin must be between 0.0 and 1.0")
        if parameters.border_height <= 0:
            errors.append("Border height must be positive")
        if parameters.border_thickness <= 0:
            errors.append("Border thickness must be positive")
        
        # Lifecycle parameters
        if parameters.initial_diameter <= 0:
            errors.append("Initial diameter must be positive")
        if parameters.death_probability < 0 or parameters.death_probability > 1:
            errors.append("Death probability must be between 0.0 and 1.0")
        if parameters.spawn_probability < 0 or parameters.spawn_probability > 1:
            errors.append("Spawn probability must be between 0.0 and 1.0")
        if parameters.diffusion_rate < 0 or parameters.diffusion_rate > 1:
            errors.append("Diffusion rate must be between 0.0 and 1.0")
        if parameters.direction_deviation < 0 or parameters.direction_deviation > 3.14159:
            errors.append("Direction deviation must be between 0.0 and π (3.14159) radians")
        
        # Output validation
        if not parameters.output.endswith('.stl'):
            errors.append("Output filename must end with .stl")
        
        return errors
    
    @staticmethod
    def estimate_complexity(parameters: SimulationParameters) -> dict:
        """Estimate the computational complexity and expected runtime."""
        
        # Calculate basic complexity factors
        grid_size = parameters.width * parameters.height
        total_operations = grid_size * parameters.actors * parameters.steps
        
        # Estimate memory usage (rough approximation)
        base_memory_mb = (grid_size * 4) / (1024 * 1024)  # Float32 trail map
        actor_memory_mb = (parameters.actors * 32) / (1024 * 1024)  # Actor structs
        layer_memory_mb = (grid_size * parameters.steps // parameters.layer_frequency * 4) / (1024 * 1024)
        
        total_memory_mb = base_memory_mb + actor_memory_mb + layer_memory_mb
        
        # Estimate runtime (very rough, based on empirical observations)
        base_time_per_operation = 1e-6  # seconds per basic operation
        complexity_multiplier = 1.0
        
        if parameters.smooth:
            complexity_multiplier *= 2.0  # Marching cubes is more expensive
        if parameters.smoothing_iterations > 0:
            complexity_multiplier *= (1.0 + parameters.smoothing_iterations * 0.5)
        if parameters.diffusion_rate > 0:
            complexity_multiplier *= 1.5  # Diffusion adds overhead
        
        estimated_seconds = total_operations * base_time_per_operation * complexity_multiplier
        
        # Categorize complexity
        if estimated_seconds < 30:
            complexity_level = "low"
        elif estimated_seconds < 300:  # 5 minutes
            complexity_level = "medium"
        elif estimated_seconds < 1800:  # 30 minutes
            complexity_level = "high"
        else:
            complexity_level = "very_high"
        
        return {
            "complexity_level": complexity_level,
            "estimated_runtime_seconds": estimated_seconds,
            "estimated_memory_mb": total_memory_mb,
            "grid_operations": total_operations,
            "complexity_factors": {
                "grid_size": grid_size,
                "actor_count": parameters.actors,
                "step_count": parameters.steps,
                "uses_smooth": parameters.smooth,
                "smoothing_iterations": parameters.smoothing_iterations,
                "has_diffusion": parameters.diffusion_rate > 0
            }
        }