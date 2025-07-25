# ABOUTME: 3D model generation from Physarum simulation data using time-layered approach
# ABOUTME: Converts 2D simulation frames to 3D mesh structures with connectivity validation

import numpy as np
from typing import List, Tuple, Optional, Set
from stl import mesh
import math
from physarum import PhysarumSimulation


class Model3DGenerator:
    """Generates 3D models from Physarum simulation data."""
    
    def __init__(self, simulation: PhysarumSimulation, layer_height: float = 1.0,
                 threshold: float = 0.1, background: bool = False, 
                 background_depth: float = 2.0, background_margin: float = 0.05,
                 background_border: bool = False, border_height: float = 1.0,
                 border_thickness: float = 0.5):
        """Initialize the 3D model generator.
        
        Args:
            simulation: The Physarum simulation to generate models from
            layer_height: Height of each simulation step in the Z-axis
            threshold: Minimum trail strength to include in 3D model
            background: Whether to add a solid rectangular background
            background_depth: Depth/thickness of the background layer
            background_margin: Background margin as fraction of simulation bounds
            background_border: Whether to add a raised border around background edges
            border_height: Height of the border walls above the background
            border_thickness: Thickness of the border walls
        """
        self.simulation = simulation
        self.layer_height = layer_height
        self.threshold = threshold
        self.background = background
        self.background_depth = background_depth
        self.background_margin = background_margin
        self.background_border = background_border
        self.border_height = border_height
        self.border_thickness = border_thickness
        self.layers = []  # Store simulation frames as layers
        
    def capture_layer(self) -> None:
        """Capture current simulation state as a 3D layer."""
        # Get current trail map
        trail_map = self.simulation.get_trail_map()
        
        # Apply threshold to create binary mask
        layer_mask = trail_map > self.threshold
        
        # For subsequent layers, ensure connectivity to previous layer
        if len(self.layers) > 0:
            layer_mask = self._ensure_upward_connectivity(layer_mask)
        
        self.layers.append(layer_mask)
    
    
    def _ensure_upward_connectivity(self, layer_mask: np.ndarray) -> np.ndarray:
        """Ensure current layer connects to the previous layer (upward growth only).
        
        Args:
            layer_mask: Binary mask of the current layer
            
        Returns:
            Modified layer mask ensuring connectivity
        """
        if len(self.layers) == 0:
            return layer_mask
        
        previous_layer = self.layers[-1]
        modified_mask = layer_mask.copy()
        
        # Find connected components in current layer
        connected_components = self._find_connected_components(modified_mask)
        
        # Keep only components that connect to the previous layer
        valid_components = set()
        for component_id in np.unique(connected_components):
            if component_id == 0:  # Skip background
                continue
            
            # Check if this component overlaps with previous layer
            component_mask = connected_components == component_id
            if np.any(component_mask & previous_layer):
                valid_components.add(component_id)
        
        # Create final mask with only valid components
        final_mask = np.zeros_like(modified_mask, dtype=bool)
        for component_id in valid_components:
            final_mask |= (connected_components == component_id)
        
        return final_mask
    
    def _find_connected_components(self, binary_mask: np.ndarray) -> np.ndarray:
        """Find connected components in a binary mask using flood fill.
        
        Args:
            binary_mask: Binary mask to analyze
            
        Returns:
            Array with connected component labels
        """
        labels = np.zeros_like(binary_mask, dtype=int)
        current_label = 1
        
        for y in range(binary_mask.shape[0]):
            for x in range(binary_mask.shape[1]):
                if binary_mask[y, x] and labels[y, x] == 0:
                    # Start flood fill from this point
                    self._flood_fill(binary_mask, labels, x, y, current_label)
                    current_label += 1
        
        return labels
    
    def _flood_fill(self, binary_mask: np.ndarray, labels: np.ndarray, 
                   start_x: int, start_y: int, label: int) -> None:
        """Perform flood fill to label connected components.
        
        Args:
            binary_mask: Binary mask to fill
            labels: Label array to fill
            start_x: Starting x coordinate
            start_y: Starting y coordinate
            label: Label to assign
        """
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            
            # Check bounds
            if x < 0 or x >= binary_mask.shape[1] or y < 0 or y >= binary_mask.shape[0]:
                continue
            
            # Check if already labeled or not part of mask
            if labels[y, x] != 0 or not binary_mask[y, x]:
                continue
            
            # Label this pixel
            labels[y, x] = label
            
            # Add neighbors to stack
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    
    def generate_mesh(self) -> mesh.Mesh:
        """Generate 3D mesh from captured layers using voxel-based approach.
        
        Returns:
            STL mesh object
        """
        if not self.layers:
            raise ValueError("No layers captured. Call capture_layer() first.")
        
        triangles = []
        
        # Add background mesh if enabled
        if self.background:
            background_triangles = self._create_background_mesh()
            triangles.extend(background_triangles)
            
            # Add border if enabled
            if self.background_border:
                border_triangles = self._create_border_mesh()
                triangles.extend(border_triangles)
        
        # Generate triangular faces for each voxel
        for layer_idx, layer_mask in enumerate(self.layers):
            z_bottom = layer_idx * self.layer_height
            z_top = z_bottom + self.layer_height
            
            # For each solid voxel, create faces
            for y in range(layer_mask.shape[0]):
                for x in range(layer_mask.shape[1]):
                    if layer_mask[y, x]:
                        # Create faces for this voxel
                        voxel_triangles = self._create_voxel_faces(x, y, z_bottom, z_top, layer_mask)
                        triangles.extend(voxel_triangles)
        
        if not triangles:
            raise ValueError("No valid faces generated from layers")
        
        # Create STL mesh
        stl_mesh = mesh.Mesh(np.zeros(len(triangles), dtype=mesh.Mesh.dtype))
        for i, triangle in enumerate(triangles):
            stl_mesh.vectors[i] = triangle
        
        return stl_mesh
    
    def _create_voxel_faces(self, x: int, y: int, z_bottom: float, z_top: float, 
                           layer_mask: np.ndarray) -> List[np.ndarray]:
        """Create triangular faces for a single voxel.
        
        Args:
            x: X coordinate of voxel
            y: Y coordinate of voxel  
            z_bottom: Bottom Z coordinate
            z_top: Top Z coordinate
            layer_mask: Current layer mask for neighbor checking
            
        Returns:
            List of triangular faces as numpy arrays
        """
        triangles = []
        
        # Define the 8 vertices of the voxel cube
        vertices = [
            [x, y, z_bottom],       # 0: bottom-left-back
            [x+1, y, z_bottom],     # 1: bottom-right-back  
            [x+1, y+1, z_bottom],   # 2: bottom-right-front
            [x, y+1, z_bottom],     # 3: bottom-left-front
            [x, y, z_top],          # 4: top-left-back
            [x+1, y, z_top],        # 5: top-right-back
            [x+1, y+1, z_top],      # 6: top-right-front
            [x, y+1, z_top],        # 7: top-left-front
        ]
        
        # Define faces as pairs of triangles (each face = 2 triangles)
        # Only add exterior faces (faces not adjacent to other solid voxels)
        
        # Bottom face (always add for first layer)
        if z_bottom == 0:
            triangles.extend([
                np.array([vertices[0], vertices[1], vertices[2]]),
                np.array([vertices[0], vertices[2], vertices[3]])
            ])
        
        # Top face (always add for last layer)
        triangles.extend([
            np.array([vertices[4], vertices[6], vertices[5]]),
            np.array([vertices[4], vertices[7], vertices[6]])
        ])
        
        # Side faces (only if no neighbor in that direction)
        height, width = layer_mask.shape
        
        # Front face (y+1 direction)
        if y + 1 >= height or not layer_mask[y + 1, x]:
            triangles.extend([
                np.array([vertices[3], vertices[2], vertices[6]]),
                np.array([vertices[3], vertices[6], vertices[7]])
            ])
        
        # Back face (y-1 direction)  
        if y - 1 < 0 or not layer_mask[y - 1, x]:
            triangles.extend([
                np.array([vertices[0], vertices[4], vertices[5]]),
                np.array([vertices[0], vertices[5], vertices[1]])
            ])
        
        # Right face (x+1 direction)
        if x + 1 >= width or not layer_mask[y, x + 1]:
            triangles.extend([
                np.array([vertices[1], vertices[5], vertices[6]]),
                np.array([vertices[1], vertices[6], vertices[2]])
            ])
        
        # Left face (x-1 direction)
        if x - 1 < 0 or not layer_mask[y, x - 1]:
            triangles.extend([
                np.array([vertices[0], vertices[3], vertices[7]]),
                np.array([vertices[0], vertices[7], vertices[4]])
            ])
        
        return triangles
    
    def _create_background_mesh(self) -> List[np.ndarray]:
        """Create triangular faces for the background rectangular solid.
        
        Returns:
            List of triangular faces as numpy arrays
        """
        if not self.background or not self.layers:
            return []
        
        # Calculate bounds based on actual simulation content
        content_bounds = self._get_simulation_content_bounds()
        
        # Apply margin to content bounds
        content_width = content_bounds['x_max'] - content_bounds['x_min']
        content_height = content_bounds['y_max'] - content_bounds['y_min']
        margin_x = content_width * self.background_margin
        margin_y = content_height * self.background_margin
        
        # Background extends beyond content bounds by margin
        x_min = content_bounds['x_min'] - margin_x
        x_max = content_bounds['x_max'] + margin_x
        y_min = content_bounds['y_min'] - margin_y
        y_max = content_bounds['y_max'] + margin_y
        
        # Background sits above all layers (after the last layer)
        last_layer_z = len(self.layers) * self.layer_height
        z_min = last_layer_z
        z_max = last_layer_z + self.background_depth
        
        # Define the 8 vertices of the background box
        vertices = [
            [x_min, y_min, z_min],  # 0: bottom-left-back
            [x_max, y_min, z_min],  # 1: bottom-right-back
            [x_max, y_max, z_min],  # 2: bottom-right-front
            [x_min, y_max, z_min],  # 3: bottom-left-front
            [x_min, y_min, z_max],  # 4: top-left-back
            [x_max, y_min, z_max],  # 5: top-right-back
            [x_max, y_max, z_max],  # 6: top-right-front
            [x_min, y_max, z_max],  # 7: top-left-front
        ]
        
        triangles = []
        
        # Bottom face (z = z_min)
        triangles.extend([
            np.array([vertices[0], vertices[1], vertices[2]]),
            np.array([vertices[0], vertices[2], vertices[3]])
        ])
        
        # Top face (z = z_max) - this connects to the simulation
        triangles.extend([
            np.array([vertices[4], vertices[6], vertices[5]]),
            np.array([vertices[4], vertices[7], vertices[6]])
        ])
        
        # Front face (y = y_max)
        triangles.extend([
            np.array([vertices[3], vertices[2], vertices[6]]),
            np.array([vertices[3], vertices[6], vertices[7]])
        ])
        
        # Back face (y = y_min)
        triangles.extend([
            np.array([vertices[0], vertices[4], vertices[5]]),
            np.array([vertices[0], vertices[5], vertices[1]])
        ])
        
        # Right face (x = x_max)
        triangles.extend([
            np.array([vertices[1], vertices[5], vertices[6]]),
            np.array([vertices[1], vertices[6], vertices[2]])
        ])
        
        # Left face (x = x_min)
        triangles.extend([
            np.array([vertices[0], vertices[3], vertices[7]]),
            np.array([vertices[0], vertices[7], vertices[4]])
        ])
        
        return triangles
    
    def _create_border_mesh(self) -> List[np.ndarray]:
        """Create triangular faces for the border walls around the background.
        
        Returns:
            List of triangular faces as numpy arrays
        """
        if not self.background or not self.background_border or not self.layers:
            return []
        
        # Calculate bounds based on actual simulation content
        content_bounds = self._get_simulation_content_bounds()
        
        # Apply margin to content bounds
        content_width = content_bounds['x_max'] - content_bounds['x_min']
        content_height = content_bounds['y_max'] - content_bounds['y_min']
        margin_x = content_width * self.background_margin
        margin_y = content_height * self.background_margin
        
        # Background outer bounds match content aspect ratio
        x_min = content_bounds['x_min'] - margin_x
        x_max = content_bounds['x_max'] + margin_x
        y_min = content_bounds['y_min'] - margin_y
        y_max = content_bounds['y_max'] + margin_y
        
        # Background sits above all layers
        last_layer_z = len(self.layers) * self.layer_height
        background_bottom = last_layer_z
        background_top = last_layer_z + self.background_depth
        border_bottom = background_bottom - self.border_height
        
        triangles = []
        
        # Create four border walls around the background
        # Each wall is a rectangular prism
        
        # Front wall (y = y_max side) - inset from edge by border_thickness
        triangles.extend(self._create_border_wall(
            x_min, x_max, y_max - self.border_thickness, y_max,
            border_bottom, background_bottom
        ))
        
        # Back wall (y = y_min side) - inset from edge by border_thickness
        triangles.extend(self._create_border_wall(
            x_min, x_max, y_min, y_min + self.border_thickness,
            border_bottom, background_bottom
        ))
        
        # Right wall (x = x_max side) - inset from edge by border_thickness
        triangles.extend(self._create_border_wall(
            x_max - self.border_thickness, x_max, y_min + self.border_thickness, y_max - self.border_thickness,
            border_bottom, background_bottom
        ))
        
        # Left wall (x = x_min side) - inset from edge by border_thickness
        triangles.extend(self._create_border_wall(
            x_min, x_min + self.border_thickness, y_min + self.border_thickness, y_max - self.border_thickness,
            border_bottom, background_bottom
        ))
        
        return triangles
    
    def _create_border_wall(self, x_min: float, x_max: float, y_min: float, y_max: float,
                           z_min: float, z_max: float) -> List[np.ndarray]:
        """Create triangular faces for a single border wall.
        
        Args:
            x_min, x_max: X bounds of the wall
            y_min, y_max: Y bounds of the wall
            z_min, z_max: Z bounds of the wall
            
        Returns:
            List of triangular faces as numpy arrays
        """
        # Define the 8 vertices of the wall box
        vertices = [
            [x_min, y_min, z_min],  # 0: bottom-left-back
            [x_max, y_min, z_min],  # 1: bottom-right-back
            [x_max, y_max, z_min],  # 2: bottom-right-front
            [x_min, y_max, z_min],  # 3: bottom-left-front
            [x_min, y_min, z_max],  # 4: top-left-back
            [x_max, y_min, z_max],  # 5: top-right-back
            [x_max, y_max, z_max],  # 6: top-right-front
            [x_min, y_max, z_max],  # 7: top-left-front
        ]
        
        triangles = []
        
        # Bottom face (z = z_min)
        triangles.extend([
            np.array([vertices[0], vertices[1], vertices[2]]),
            np.array([vertices[0], vertices[2], vertices[3]])
        ])
        
        # Top face (z = z_max) - connected to background
        triangles.extend([
            np.array([vertices[4], vertices[6], vertices[5]]),
            np.array([vertices[4], vertices[7], vertices[6]])
        ])
        
        # Front face (y = y_max)
        triangles.extend([
            np.array([vertices[3], vertices[2], vertices[6]]),
            np.array([vertices[3], vertices[6], vertices[7]])
        ])
        
        # Back face (y = y_min)
        triangles.extend([
            np.array([vertices[0], vertices[4], vertices[5]]),
            np.array([vertices[0], vertices[5], vertices[1]])
        ])
        
        # Right face (x = x_max)
        triangles.extend([
            np.array([vertices[1], vertices[5], vertices[6]]),
            np.array([vertices[1], vertices[6], vertices[2]])
        ])
        
        # Left face (x = x_min)
        triangles.extend([
            np.array([vertices[0], vertices[3], vertices[7]]),
            np.array([vertices[0], vertices[7], vertices[4]])
        ])
        
        return triangles
    
    def _get_simulation_content_bounds(self) -> dict:
        """Get the bounding box of actual simulation content from the last layer.
        
        Returns:
            Dictionary with x_min, x_max, y_min, y_max bounds of active content
        """
        if not self.layers:
            # Fallback to full grid if no layers
            return {
                'x_min': 0,
                'x_max': self.simulation.grid.width,
                'y_min': 0,
                'y_max': self.simulation.grid.height
            }
        
        # Use the last layer to determine content bounds
        last_layer = self.layers[-1]
        
        # Find all positions with active content
        active_positions = np.where(last_layer)
        
        if len(active_positions[0]) == 0:
            # No active content, fallback to full grid
            return {
                'x_min': 0,
                'x_max': self.simulation.grid.width,
                'y_min': 0,
                'y_max': self.simulation.grid.height
            }
        
        # Get bounds of active content
        y_positions = active_positions[0]  # Row indices
        x_positions = active_positions[1]  # Column indices
        
        # Convert to actual coordinates (add 1 to max for inclusive bound)
        return {
            'x_min': float(np.min(x_positions)),
            'x_max': float(np.max(x_positions) + 1),
            'y_min': float(np.min(y_positions)),
            'y_max': float(np.max(y_positions) + 1)
        }
    
    def validate_connectivity(self) -> bool:
        """Validate that the 3D model has proper connectivity.
        
        Returns:
            True if model is properly connected, False otherwise
        """
        if not self.layers:
            return False
        
        # Check that each layer (except first) connects to previous layer
        for i in range(1, len(self.layers)):
            current_layer = self.layers[i]
            previous_layer = self.layers[i-1]
            
            # Find connected components in current layer
            components = self._find_connected_components(current_layer)
            
            # Check that all components connect to previous layer
            for component_id in np.unique(components):
                if component_id == 0:  # Skip background
                    continue
                
                component_mask = components == component_id
                if not np.any(component_mask & previous_layer):
                    return False  # Disconnected component found
        
        return True
    
    def save_stl(self, filename: str) -> None:
        """Save the 3D model as an STL file.
        
        Args:
            filename: Output filename for STL file
        """
        stl_mesh = self.generate_mesh()
        stl_mesh.save(filename)
    
    def get_layer_count(self) -> int:
        """Get the number of captured layers.
        
        Returns:
            Number of layers
        """
        return len(self.layers)
    
    def clear_layers(self) -> None:
        """Clear all captured layers."""
        self.layers.clear()


def generate_3d_model_from_simulation(width: int, height: int, num_actors: int, 
                                    decay_rate: float, steps: int, 
                                    layer_height: float = 1.0, 
                                    threshold: float = 0.1) -> Model3DGenerator:
    """Generate a 3D model from a Physarum simulation.
    
    Args:
        width: Simulation grid width
        height: Simulation grid height
        num_actors: Number of Physarum actors
        decay_rate: Trail decay rate
        steps: Number of simulation steps
        layer_height: Height of each layer in 3D model
        threshold: Minimum trail strength for inclusion
        
    Returns:
        Model3DGenerator with captured layers
    """
    # Create and run simulation
    sim = PhysarumSimulation(width, height, num_actors, decay_rate)
    
    # Create 3D model generator
    generator = Model3DGenerator(sim, layer_height, threshold)
    
    # Run simulation and capture layers
    for step in range(steps):
        sim.step()
        
        # Capture layer every few steps to avoid too many layers
        if step % 5 == 0:  # Capture every 5th step
            generator.capture_layer()
    
    # Capture final layer
    generator.capture_layer()
    
    return generator