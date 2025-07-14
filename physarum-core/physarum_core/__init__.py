# ABOUTME: Core simulation package entry point
# ABOUTME: Exposes main simulation and model generation classes for easy import

from .simulation import PhysarumSimulation, PhysarumActor, PhysarumGrid
from .models.model_3d import Model3DGenerator, generate_3d_model_from_simulation
from .models.model_3d_smooth import SmoothModel3DGenerator, generate_smooth_3d_model_from_simulation
# from .output.manager import OutputManager  # TODO: OutputManager not implemented yet
from .preview.generator import PreviewGenerator

__all__ = [
    'PhysarumSimulation',
    'PhysarumActor', 
    'PhysarumGrid',
    'Model3DGenerator',
    'generate_3d_model_from_simulation',
    'SmoothModel3DGenerator', 
    'generate_smooth_3d_model_from_simulation',
    # 'OutputManager',  # TODO: OutputManager not implemented yet
    'PreviewGenerator'
]