# ABOUTME: 3D model generation with smooth surfaces using marching cubes algorithm
# ABOUTME: Replaces voxel-based approach with smooth surface extraction for organic 3D models

import numpy as np
from typing import List, Tuple, Optional
from stl import mesh
import trimesh
from skimage import measure
from scipy import ndimage
from physarum import PhysarumSimulation


class SmoothModel3DGenerator:
    """Generates smooth 3D models from Physarum simulation data using marching cubes."""
    
    def __init__(self, simulation: PhysarumSimulation, layer_height: float = 1.0,
                 threshold: float = 0.1, smoothing_iterations: int = 0,
                 smoothing_type: str = "laplacian", taubin_lambda: float = 0.5, 
                 taubin_mu: float = -0.52, preserve_features: bool = False,
                 feature_angle: float = 60.0):
        """Initialize the smooth 3D model generator.
        
        Args:
            simulation: The Physarum simulation to generate models from
            layer_height: Height of each simulation step in the Z-axis
            threshold: Minimum trail strength to include in 3D model
            smoothing_iterations: Number of smoothing iterations to apply
            smoothing_type: Type of smoothing ('laplacian', 'taubin', 'feature_preserving', 'boundary_outline')
            taubin_lambda: Lambda parameter for Taubin smoothing (shrinking factor)
            taubin_mu: Mu parameter for Taubin smoothing (anti-shrinking factor)
            preserve_features: Whether to preserve sharp features during smoothing
            feature_angle: Angle threshold (degrees) for feature preservation
        """
        self.simulation = simulation
        self.layer_height = layer_height
        self.threshold = threshold
        self.smoothing_iterations = smoothing_iterations
        self.smoothing_type = smoothing_type
        self.taubin_lambda = taubin_lambda
        self.taubin_mu = taubin_mu
        self.preserve_features = preserve_features
        self.feature_angle = np.radians(feature_angle)
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
        """Find connected components in a binary mask using scipy.
        
        Args:
            binary_mask: Binary mask to analyze
            
        Returns:
            Array with connected component labels
        """
        labels, _ = ndimage.label(binary_mask)
        return labels
    
    def _generate_volume(self) -> np.ndarray:
        """Generate 3D volume array from layer stack.
        
        Returns:
            3D volume array suitable for marching cubes
        """
        if not self.layers:
            raise ValueError("No layers captured. Call capture_layer() first.")
        
        # Create 3D volume array
        height, width = self.layers[0].shape
        depth = len(self.layers)
        volume = np.zeros((height, width, depth), dtype=np.float32)
        
        # Fill volume with layer data
        for z, layer_mask in enumerate(self.layers):
            volume[:, :, z] = layer_mask.astype(np.float32)
        
        # Apply some smoothing to the volume to reduce stepping artifacts
        if depth > 2:  # Only smooth if we have enough layers
            volume = ndimage.gaussian_filter(volume, sigma=0.5)
        
        return volume
    
    def generate_mesh(self) -> mesh.Mesh:
        """Generate smooth 3D mesh using marching cubes algorithm.
        
        Returns:
            STL mesh object with smooth surfaces
        """
        if not self.layers:
            raise ValueError("No layers captured. Call capture_layer() first.")
        
        # Generate 3D volume
        volume = self._generate_volume()
        
        # Use boundary outline method instead of marching cubes if requested
        if self.smoothing_type == "boundary_outline":
            tri_mesh = self._generate_boundary_outline_mesh(volume)
        else:
            # Apply marching cubes to extract isosurface
            try:
                vertices, faces, normals, values = measure.marching_cubes(
                    volume, 
                    level=0.5,  # Isosurface level
                    spacing=(1.0, 1.0, self.layer_height)  # Voxel spacing
                )
            except ValueError as e:
                # Fallback: if marching cubes fails, try with different level
                try:
                    vertices, faces, normals, values = measure.marching_cubes(
                        volume, 
                        level=0.1,
                        spacing=(1.0, 1.0, self.layer_height)
                    )
                except ValueError:
                    raise ValueError(f"Failed to generate mesh with marching cubes: {e}")
            
            # Create trimesh object for processing
            tri_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Apply smoothing if requested (boundary_outline doesn't use traditional smoothing)
        if self.smoothing_iterations > 0 and self.smoothing_type != "boundary_outline":
            if self.smoothing_type == "laplacian":
                tri_mesh = self._apply_laplacian_smoothing(tri_mesh, self.smoothing_iterations)
            elif self.smoothing_type == "taubin":
                tri_mesh = self._apply_taubin_smoothing(tri_mesh, self.smoothing_iterations)
            elif self.smoothing_type == "feature_preserving":
                tri_mesh = self._apply_feature_preserving_smoothing(tri_mesh, self.smoothing_iterations)
            else:
                raise ValueError(f"Unknown smoothing type: {self.smoothing_type}")
        
        # Validate and repair mesh
        tri_mesh = self._validate_and_repair_mesh(tri_mesh)
        
        # Convert to STL mesh format
        stl_mesh = mesh.Mesh(np.zeros(len(tri_mesh.faces), dtype=mesh.Mesh.dtype))
        for i, face in enumerate(tri_mesh.faces):
            stl_mesh.vectors[i] = tri_mesh.vertices[face]
        
        return stl_mesh
    
    def _generate_boundary_outline_mesh(self, volume: np.ndarray) -> trimesh.Trimesh:
        """Generate mesh using true contour-based boundary detection to eliminate blocky appearance.
        
        This method finds the contours of connected regions and creates smooth surfaces
        around them, rather than individual voxel faces, to eliminate pixelated appearance.
        
        Args:
            volume: 3D volume array with binary voxel data
            
        Returns:
            Trimesh object with smooth contour-based mesh
        """
        # Use marching cubes on a smoothed version to get genuinely smooth contours
        # First, apply Gaussian smoothing to eliminate voxel boundaries while preserving shape
        from scipy.ndimage import gaussian_filter
        
        # Pad the volume at top and bottom to ensure natural closure
        padded_volume = self._pad_volume_for_closure(volume)
        
        # Smooth the padded volume to create genuine curves instead of voxel boundaries  
        smoothed_volume = gaussian_filter(padded_volume.astype(float), sigma=1.2)
        
        # Determine appropriate threshold based on smoothed volume range
        max_value = np.max(smoothed_volume)
        min_value = np.min(smoothed_volume)
        
        # Use dynamic threshold: 40% of the range above minimum
        if max_value > min_value:
            dynamic_threshold = min_value + 0.4 * (max_value - min_value)
        else:
            dynamic_threshold = 0.5  # fallback
        
        # Apply marching cubes with dynamic threshold
        try:
            vertices, faces, normals, values = measure.marching_cubes(
                smoothed_volume,
                level=dynamic_threshold,
                spacing=(1.0, 1.0, self.layer_height)
            )
        except ValueError:
            # Fallback: try with less smoothing and different threshold
            try:
                smoothed_volume = gaussian_filter(volume.astype(float), sigma=0.8)
                max_value = np.max(smoothed_volume)
                min_value = np.min(smoothed_volume)
                fallback_threshold = min_value + 0.3 * (max_value - min_value)
                vertices, faces, normals, values = measure.marching_cubes(
                    smoothed_volume,
                    level=fallback_threshold,
                    spacing=(1.0, 1.0, self.layer_height)
                )
            except ValueError:
                # Last fallback: use original volume with standard threshold
                vertices, faces, normals, values = measure.marching_cubes(
                    volume,
                    level=0.5,
                    spacing=(1.0, 1.0, self.layer_height)
                )
        
        # Create initial mesh
        tri_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Apply additional smoothing to further reduce any remaining voxel artifacts
        tri_mesh = self._apply_contour_smoothing(tri_mesh, iterations=4)
        
        # Make the mesh watertight for 3D printing
        tri_mesh = self._make_mesh_watertight(tri_mesh, padded_volume)
        
        return tri_mesh
    
    def _apply_contour_smoothing(self, tri_mesh: trimesh.Trimesh, iterations: int) -> trimesh.Trimesh:
        """Apply specialized smoothing designed to eliminate voxel artifacts while preserving shape.
        
        Args:
            tri_mesh: Input trimesh object
            iterations: Number of smoothing iterations
            
        Returns:
            Smoothed trimesh object with reduced voxel artifacts
        """
        smoothed_mesh = tri_mesh.copy()
        
        for _ in range(iterations):
            # Build vertex adjacency using edges
            edges = smoothed_mesh.edges_unique
            n_vertices = len(smoothed_mesh.vertices)
            
            # Create adjacency list for each vertex
            vertex_neighbors = [[] for _ in range(n_vertices)]
            for edge in edges:
                vertex_neighbors[edge[0]].append(edge[1])
                vertex_neighbors[edge[1]].append(edge[0])
            
            # Apply smoothing with adaptive damping based on curvature
            damping = 0.3  # Higher damping for more aggressive smoothing
            new_vertices = smoothed_mesh.vertices.copy()
            
            for i, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    # Compute average position of neighbors
                    neighbor_positions = smoothed_mesh.vertices[neighbors]
                    average_neighbor = np.mean(neighbor_positions, axis=0)
                    
                    # Move vertex towards average of neighbors
                    new_vertices[i] = smoothed_mesh.vertices[i] + damping * (average_neighbor - smoothed_mesh.vertices[i])
            
            # Update mesh vertices
            smoothed_mesh.vertices = new_vertices
        
        return smoothed_mesh
    
    def _pad_volume_for_closure(self, volume: np.ndarray) -> np.ndarray:
        """Pad the volume at top and bottom to ensure marching cubes creates closed surfaces.
        
        Args:
            volume: Original 3D volume array
            
        Returns:
            Padded volume with empty layers at top and bottom for natural closure
        """
        height, width, depth = volume.shape
        
        # Create padded volume with 2 empty layers at bottom and top
        padded_depth = depth + 4
        padded_volume = np.zeros((height, width, padded_depth), dtype=volume.dtype)
        
        # Copy original volume to middle section
        padded_volume[:, :, 2:depth+2] = volume
        
        # Add thin base layer at the bottom to ensure connectivity
        # Use the projection of the first layer to create a thin foundation
        first_layer = volume[:, :, 0]
        if np.any(first_layer):
            # Create a thin foundation layer
            foundation = first_layer * 0.3  # 30% strength foundation
            padded_volume[:, :, 1] = foundation
        
        # Add thin cap layer at the top
        last_layer = volume[:, :, -1]
        if np.any(last_layer):
            # Create a thin cap layer
            cap = last_layer * 0.3  # 30% strength cap
            padded_volume[:, :, depth+2] = cap
        
        return padded_volume
    
    def _make_mesh_watertight(self, tri_mesh: trimesh.Trimesh, volume: np.ndarray) -> trimesh.Trimesh:
        """Make the mesh watertight by filling holes and ensuring proper closure.
        
        This ensures the model is closed and suitable for 3D printing with infill.
        
        Args:
            tri_mesh: Input trimesh object (from padded volume)
            volume: Padded volume for reference
            
        Returns:
            Watertight trimesh object suitable for 3D printing
        """
        watertight_mesh = tri_mesh.copy()
        
        # Apply aggressive hole filling and repair since we start with a better mesh
        for attempt in range(5):  # More attempts since we expect better results
            # Fill holes
            try:
                watertight_mesh.fill_holes()
            except:
                pass
            
            # Fix normals and winding
            watertight_mesh.fix_normals()
            
            # Remove degenerate and duplicate faces
            try:
                watertight_mesh.remove_degenerate_faces()
                watertight_mesh.remove_duplicate_faces()
            except:
                pass
            
            # Remove unreferenced vertices
            watertight_mesh.remove_unreferenced_vertices()
            
            # Check if we achieved watertight
            if watertight_mesh.is_watertight:
                break
                
            # If not watertight yet, try additional repairs
            if attempt < 4:  # Don't do this on the last attempt
                try:
                    # Try more aggressive smoothing to close small gaps
                    watertight_mesh = self._apply_contour_smoothing(watertight_mesh, iterations=1)
                except:
                    pass
        
        # Ensure positive volume (correct winding)
        if watertight_mesh.volume < 0:
            watertight_mesh.invert()
        
        # Final integrity check
        watertight_mesh = self._ensure_watertight_integrity(watertight_mesh)
        
        return watertight_mesh
    
    def _add_bottom_top_surfaces(self, tri_mesh: trimesh.Trimesh, volume: np.ndarray, min_z: float, max_z: float) -> trimesh.Trimesh:
        """Add bottom and top surfaces to seal the mesh.
        
        Args:
            tri_mesh: Input mesh
            volume: Original volume for determining shape
            min_z: Minimum Z coordinate
            max_z: Maximum Z coordinate
            
        Returns:
            Mesh with added bottom and top surfaces
        """
        # Get the 2D projection of the volume to determine the base shape
        binary_volume = volume > 0.5
        
        # Project volume to get bottom shape (any solid voxel in the stack)
        bottom_projection = np.any(binary_volume, axis=2)
        
        # Project volume to get top shape (solid voxels in top layers)
        top_layers = binary_volume[:, :, -3:]  # Use top 3 layers
        top_projection = np.any(top_layers, axis=2)
        
        new_vertices = tri_mesh.vertices.copy().tolist()
        new_faces = tri_mesh.faces.copy().tolist()
        vertex_count = len(new_vertices)
        
        # Add bottom surface - place it just below the minimum mesh point for better connection
        if np.any(bottom_projection):
            bottom_z = min_z - 0.01  # Very close to existing mesh
            bottom_vertices, bottom_faces = self._create_surface_from_projection(
                bottom_projection, bottom_z, vertex_count, is_bottom=True
            )
            new_vertices.extend(bottom_vertices)
            new_faces.extend(bottom_faces)
            vertex_count += len(bottom_vertices)
        
        # Add top surface - place it just above the maximum mesh point for better connection
        if np.any(top_projection):
            top_z = max_z + 0.01  # Very close to existing mesh
            top_vertices, top_faces = self._create_surface_from_projection(
                top_projection, top_z, vertex_count, is_bottom=False
            )
            new_vertices.extend(top_vertices)
            new_faces.extend(top_faces)
        
        # Create new mesh with added surfaces
        try:
            sealed_mesh = trimesh.Trimesh(vertices=np.array(new_vertices), faces=np.array(new_faces))
            return sealed_mesh
        except:
            # If mesh creation fails, return original mesh
            return tri_mesh
    
    def _create_surface_from_projection(self, projection: np.ndarray, z_level: float, vertex_offset: int, is_bottom: bool) -> tuple:
        """Create triangular surface from 2D projection.
        
        Args:
            projection: 2D boolean array
            z_level: Z coordinate for the surface
            vertex_offset: Starting vertex index
            is_bottom: True for bottom surface, False for top surface
            
        Returns:
            Tuple of (vertices, faces) for the surface
        """
        height, width = projection.shape
        vertices = []
        faces = []
        
        # Create a simple grid-based triangulation of the projection
        vertex_indices = {}
        vertex_idx = vertex_offset
        
        # Add vertices for all True pixels and their neighbors
        for y in range(height):
            for x in range(width):
                if projection[y, x]:
                    # Add corners of this cell
                    corners = [
                        (x, y), (x+1, y), (x+1, y+1), (x, y+1)
                    ]
                    for cx, cy in corners:
                        if (cx, cy) not in vertex_indices:
                            vertices.append([cx, cy, z_level])
                            vertex_indices[(cx, cy)] = vertex_idx
                            vertex_idx += 1
        
        # Create triangular faces for filled cells
        for y in range(height):
            for x in range(width):
                if projection[y, x]:
                    # Get the four corners of this cell
                    corners = [
                        (x, y), (x+1, y), (x+1, y+1), (x, y+1)
                    ]
                    
                    # Check if all corners exist
                    if all(corner in vertex_indices for corner in corners):
                        v0 = vertex_indices[(x, y)]
                        v1 = vertex_indices[(x+1, y)]
                        v2 = vertex_indices[(x+1, y+1)]
                        v3 = vertex_indices[(x, y+1)]
                        
                        # Create two triangles for this cell
                        if is_bottom:
                            # Bottom surface (clockwise from below)
                            faces.append([v0, v2, v1])
                            faces.append([v0, v3, v2])
                        else:
                            # Top surface (counter-clockwise from above)
                            faces.append([v0, v1, v2])
                            faces.append([v0, v2, v3])
        
        return vertices, faces
    
    def _ensure_watertight_integrity(self, tri_mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Final validation and repair to ensure watertight integrity.
        
        Args:
            tri_mesh: Input mesh
            
        Returns:
            Validated and repaired mesh
        """
        repaired_mesh = tri_mesh.copy()
        
        # Remove any degenerate or duplicate faces
        try:
            repaired_mesh.remove_degenerate_faces()
            repaired_mesh.remove_duplicate_faces()
        except:
            pass
        
        # Remove unreferenced vertices
        repaired_mesh.remove_unreferenced_vertices()
        
        # If still not watertight, try more aggressive hole filling
        if not repaired_mesh.is_watertight:
            try:
                # Try to fill holes again
                repaired_mesh.fill_holes()
                
                # If still not watertight, try convex hull as last resort
                if not repaired_mesh.is_watertight and repaired_mesh.vertices.shape[0] > 4:
                    # Only use convex hull if we have enough vertices and it's still not watertight
                    # This is a last resort that may change the shape significantly
                    pass  # Skip convex hull for now to preserve shape
                    
            except:
                pass
        
        # Ensure proper normals
        repaired_mesh.fix_normals()
        
        return repaired_mesh
    
    def _find_boundary_voxels(self, binary_volume: np.ndarray) -> np.ndarray:
        """Find all voxels that are on the boundary (have at least one face exposed to air).
        
        Args:
            binary_volume: 3D binary array representing solid voxels
            
        Returns:
            3D boolean array marking boundary voxels
        """
        height, width, depth = binary_volume.shape
        boundary = np.zeros_like(binary_volume, dtype=bool)
        
        for z in range(depth):
            for y in range(height):
                for x in range(width):
                    if binary_volume[y, x, z]:
                        # Check if any of the 6 neighbors is empty (air)
                        is_boundary = False
                        
                        # Check all 6 directions
                        neighbors = [
                            (x-1, y, z), (x+1, y, z),  # left, right
                            (x, y-1, z), (x, y+1, z),  # back, front  
                            (x, y, z-1), (x, y, z+1),  # bottom, top
                        ]
                        
                        for nx, ny, nz in neighbors:
                            # If neighbor is outside bounds or empty, this is a boundary voxel
                            if (nx < 0 or nx >= width or 
                                ny < 0 or ny >= height or 
                                nz < 0 or nz >= depth or 
                                not binary_volume[ny, nx, nz]):
                                is_boundary = True
                                break
                        
                        boundary[y, x, z] = is_boundary
        
        return boundary
    
    def _get_exposed_faces(self, binary_volume: np.ndarray, x: int, y: int, z: int) -> list:
        """Get list of faces that are exposed to air for a boundary voxel.
        
        Args:
            binary_volume: 3D binary array representing solid voxels
            x, y, z: Coordinates of the voxel
            
        Returns:
            List of face names that are exposed ('left', 'right', 'back', 'front', 'bottom', 'top')
        """
        height, width, depth = binary_volume.shape
        exposed = []
        
        # Check each of the 6 faces
        face_checks = [
            ('left', x-1, y, z),
            ('right', x+1, y, z), 
            ('back', x, y-1, z),
            ('front', x, y+1, z),
            ('bottom', x, y, z-1),
            ('top', x, y, z+1),
        ]
        
        for face_name, nx, ny, nz in face_checks:
            # Face is exposed if neighbor is outside bounds or empty
            if (nx < 0 or nx >= width or 
                ny < 0 or ny >= height or 
                nz < 0 or nz >= depth or 
                not binary_volume[ny, nx, nz]):
                exposed.append(face_name)
        
        return exposed
    
    def _create_boundary_voxel_faces(self, x: int, y: int, z: int, exposed_faces: list, layer_height: float) -> list:
        """Create triangular faces for exposed faces of a boundary voxel.
        
        Args:
            x, y, z: Voxel coordinates
            exposed_faces: List of face names that are exposed
            layer_height: Height scaling for Z coordinate
            
        Returns:
            List of triangular faces as numpy arrays
        """
        triangles = []
        
        # Define the 8 vertices of the voxel cube with proper Z scaling
        z_bottom = z * layer_height
        z_top = z_bottom + layer_height
        
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
        
        # Define faces and their triangulation
        face_triangles = {
            'bottom': [
                [vertices[0], vertices[1], vertices[2]],
                [vertices[0], vertices[2], vertices[3]]
            ],
            'top': [
                [vertices[4], vertices[6], vertices[5]], 
                [vertices[4], vertices[7], vertices[6]]
            ],
            'front': [
                [vertices[3], vertices[2], vertices[6]],
                [vertices[3], vertices[6], vertices[7]]
            ],
            'back': [
                [vertices[0], vertices[4], vertices[5]],
                [vertices[0], vertices[5], vertices[1]]
            ],
            'right': [
                [vertices[1], vertices[5], vertices[6]],
                [vertices[1], vertices[6], vertices[2]]
            ],
            'left': [
                [vertices[0], vertices[3], vertices[7]],
                [vertices[0], vertices[7], vertices[4]]
            ]
        }
        
        # Add triangles for exposed faces only
        for face_name in exposed_faces:
            if face_name in face_triangles:
                for triangle_vertices in face_triangles[face_name]:
                    triangles.append(np.array(triangle_vertices))
        
        return triangles
    
    def _apply_laplacian_smoothing(self, tri_mesh: trimesh.Trimesh, iterations: int) -> trimesh.Trimesh:
        """Apply Laplacian smoothing to the mesh.
        
        Args:
            tri_mesh: Input trimesh object
            iterations: Number of smoothing iterations
            
        Returns:
            Smoothed trimesh object
        """
        # Use simple Laplacian smoothing for better compatibility
        smoothed_mesh = tri_mesh.copy()
        
        for _ in range(iterations):
            # Build vertex adjacency matrix using edges
            edges = smoothed_mesh.edges_unique
            n_vertices = len(smoothed_mesh.vertices)
            
            # Create adjacency list for each vertex
            vertex_neighbors = [[] for _ in range(n_vertices)]
            for edge in edges:
                vertex_neighbors[edge[0]].append(edge[1])
                vertex_neighbors[edge[1]].append(edge[0])
            
            # Apply Laplacian smoothing with small damping factor
            damping = 0.1
            new_vertices = smoothed_mesh.vertices.copy()
            
            for i, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    # Compute average position of neighbors
                    neighbor_positions = smoothed_mesh.vertices[neighbors]
                    average_neighbor = np.mean(neighbor_positions, axis=0)
                    
                    # Move vertex towards average of neighbors
                    new_vertices[i] = smoothed_mesh.vertices[i] + damping * (average_neighbor - smoothed_mesh.vertices[i])
            
            # Update mesh vertices
            smoothed_mesh.vertices = new_vertices
        
        return smoothed_mesh
    
    def _apply_taubin_smoothing(self, tri_mesh: trimesh.Trimesh, iterations: int) -> trimesh.Trimesh:
        """Apply Taubin smoothing to prevent volume loss.
        
        Taubin smoothing applies two passes per iteration:
        1. Laplacian smoothing with positive lambda (shrinking)
        2. Laplacian smoothing with negative mu (anti-shrinking)
        
        Args:
            tri_mesh: Input trimesh object
            iterations: Number of smoothing iterations
            
        Returns:
            Smoothed trimesh object with minimal volume loss
        """
        smoothed_mesh = tri_mesh.copy()
        
        for _ in range(iterations):
            # Build vertex adjacency for both passes
            edges = smoothed_mesh.edges_unique
            n_vertices = len(smoothed_mesh.vertices)
            
            # Create adjacency list for each vertex
            vertex_neighbors = [[] for _ in range(n_vertices)]
            for edge in edges:
                vertex_neighbors[edge[0]].append(edge[1])
                vertex_neighbors[edge[1]].append(edge[0])
            
            # Pass 1: Laplacian smoothing with lambda (shrinking)
            new_vertices = smoothed_mesh.vertices.copy()
            for i, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    neighbor_positions = smoothed_mesh.vertices[neighbors]
                    average_neighbor = np.mean(neighbor_positions, axis=0)
                    new_vertices[i] = smoothed_mesh.vertices[i] + self.taubin_lambda * (average_neighbor - smoothed_mesh.vertices[i])
            
            smoothed_mesh.vertices = new_vertices
            
            # Pass 2: Laplacian smoothing with mu (anti-shrinking)
            new_vertices = smoothed_mesh.vertices.copy()
            for i, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    neighbor_positions = smoothed_mesh.vertices[neighbors]
                    average_neighbor = np.mean(neighbor_positions, axis=0)
                    new_vertices[i] = smoothed_mesh.vertices[i] + self.taubin_mu * (average_neighbor - smoothed_mesh.vertices[i])
            
            smoothed_mesh.vertices = new_vertices
        
        return smoothed_mesh
    
    def _apply_feature_preserving_smoothing(self, tri_mesh: trimesh.Trimesh, iterations: int) -> trimesh.Trimesh:
        """Apply feature-preserving smoothing that maintains sharp edges and corners.
        
        Args:
            tri_mesh: Input trimesh object
            iterations: Number of smoothing iterations
            
        Returns:
            Smoothed trimesh object with preserved features
        """
        smoothed_mesh = tri_mesh.copy()
        
        # Identify feature edges based on dihedral angle
        feature_edges = self._identify_feature_edges(smoothed_mesh)
        
        for _ in range(iterations):
            edges = smoothed_mesh.edges_unique
            n_vertices = len(smoothed_mesh.vertices)
            
            # Create adjacency list for each vertex
            vertex_neighbors = [[] for _ in range(n_vertices)]
            for edge in edges:
                vertex_neighbors[edge[0]].append(edge[1])
                vertex_neighbors[edge[1]].append(edge[0])
            
            # Apply smoothing with feature preservation
            damping = 0.1
            new_vertices = smoothed_mesh.vertices.copy()
            
            for i, neighbors in enumerate(vertex_neighbors):
                if len(neighbors) > 0:
                    # Check if this vertex is on a feature edge
                    is_feature_vertex = self._is_feature_vertex(i, feature_edges)
                    
                    if not is_feature_vertex or not self.preserve_features:
                        # Apply normal smoothing
                        neighbor_positions = smoothed_mesh.vertices[neighbors]
                        average_neighbor = np.mean(neighbor_positions, axis=0)
                        new_vertices[i] = smoothed_mesh.vertices[i] + damping * (average_neighbor - smoothed_mesh.vertices[i])
                    # If it's a feature vertex and preserve_features is True, don't smooth
            
            smoothed_mesh.vertices = new_vertices
        
        return smoothed_mesh
    
    def _identify_feature_edges(self, tri_mesh: trimesh.Trimesh) -> set:
        """Identify feature edges based on dihedral angle between adjacent faces.
        
        Args:
            tri_mesh: Input trimesh object
            
        Returns:
            Set of edge tuples that are considered feature edges
        """
        feature_edges = set()
        
        try:
            # Get face adjacency information
            face_adjacency = tri_mesh.face_adjacency
            face_adjacency_angles = tri_mesh.face_adjacency_angles
            
            # Find edges with large dihedral angles (sharp features)
            for i, angle in enumerate(face_adjacency_angles):
                if angle > self.feature_angle:
                    # Get the edge between adjacent faces
                    face1, face2 = face_adjacency[i]
                    # Find shared edge between faces
                    shared_vertices = set(tri_mesh.faces[face1]) & set(tri_mesh.faces[face2])
                    if len(shared_vertices) == 2:
                        edge = tuple(sorted(shared_vertices))
                        feature_edges.add(edge)
        except:
            # Fallback: if face adjacency fails, assume no feature edges
            pass
        
        return feature_edges
    
    def _is_feature_vertex(self, vertex_idx: int, feature_edges: set) -> bool:
        """Check if a vertex is part of any feature edge.
        
        Args:
            vertex_idx: Index of vertex to check
            feature_edges: Set of feature edge tuples
            
        Returns:
            True if vertex is on a feature edge
        """
        for edge in feature_edges:
            if vertex_idx in edge:
                return True
        return False
    
    def _validate_and_repair_mesh(self, tri_mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Validate and repair mesh for 3D printing compatibility.
        
        Args:
            tri_mesh: Input trimesh object
            
        Returns:
            Validated and repaired trimesh object
        """
        # Make a copy to avoid modifying the original
        repaired_mesh = tri_mesh.copy()
        
        # 1. Remove degenerate faces (faces with duplicate vertices)
        try:
            # Use new API if available
            if hasattr(repaired_mesh, 'nondegenerate_faces'):
                repaired_mesh.update_faces(repaired_mesh.nondegenerate_faces())
            else:
                repaired_mesh.remove_degenerate_faces()
        except:
            pass  # Skip if method doesn't exist or fails
        
        # 2. Remove duplicate faces
        try:
            # Use new API if available
            if hasattr(repaired_mesh, 'unique_faces'):
                repaired_mesh.update_faces(repaired_mesh.unique_faces())
            else:
                repaired_mesh.remove_duplicate_faces()
        except:
            pass  # Skip if method doesn't exist or fails
        
        # 3. Fix vertex winding order and normals
        repaired_mesh.fix_normals()
        
        # 4. Remove unreferenced vertices
        repaired_mesh.remove_unreferenced_vertices()
        
        # 5. Check for and repair manifold issues
        if not repaired_mesh.is_watertight:
            # Try basic manifold repair
            try:
                repaired_mesh.fill_holes()
            except:
                # If fill_holes fails, continue with current mesh
                pass
        
        # 6. Validate final mesh integrity
        repaired_mesh = self._ensure_mesh_integrity(repaired_mesh)
        
        return repaired_mesh
    
    def _ensure_mesh_integrity(self, tri_mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Ensure mesh has basic integrity for 3D printing.
        
        Args:
            tri_mesh: Input trimesh object
            
        Returns:
            Mesh with ensured integrity
        """
        # Remove any faces with invalid vertex indices
        max_vertex_index = len(tri_mesh.vertices) - 1
        valid_faces = []
        for face in tri_mesh.faces:
            if all(0 <= idx <= max_vertex_index for idx in face):
                # Also check that face has three unique vertices
                if len(set(face)) == 3:
                    valid_faces.append(face)
        
        if len(valid_faces) < len(tri_mesh.faces):
            tri_mesh = trimesh.Trimesh(vertices=tri_mesh.vertices, faces=np.array(valid_faces))
        
        # Ensure mesh has reasonable volume
        if tri_mesh.volume <= 0:
            # If volume is negative or zero, try fixing normals again
            tri_mesh.invert()
            tri_mesh.fix_normals()
        
        return tri_mesh
    
    def get_mesh_quality_metrics(self) -> dict:
        """Get quality metrics for the generated mesh.
        
        Returns:
            Dictionary with mesh quality metrics
        """
        if not self.layers:
            return {"error": "No layers captured"}
        
        try:
            # Generate mesh for analysis
            tri_mesh = self._generate_mesh_for_analysis()
            
            metrics = {
                "vertex_count": len(tri_mesh.vertices),
                "face_count": len(tri_mesh.faces),
                "volume": tri_mesh.volume,
                "surface_area": tri_mesh.area,
                "is_watertight": tri_mesh.is_watertight,
                "is_winding_consistent": tri_mesh.is_winding_consistent,
                "euler_number": tri_mesh.euler_number,
                "bounds": tri_mesh.bounds.tolist(),
                "center_mass": tri_mesh.center_mass.tolist()
            }
            
            # Check for common issues
            issues = []
            if not tri_mesh.is_watertight:
                issues.append("Not watertight - may have holes")
            if not tri_mesh.is_winding_consistent:
                issues.append("Inconsistent winding order")
            if tri_mesh.volume <= 0:
                issues.append("Invalid volume")
            if len(tri_mesh.vertices) == 0:
                issues.append("No vertices")
            if len(tri_mesh.faces) == 0:
                issues.append("No faces")
            
            metrics["issues"] = issues
            metrics["print_ready"] = len(issues) == 0
            
            return metrics
            
        except Exception as e:
            return {"error": f"Failed to analyze mesh: {str(e)}"}
    
    def _generate_mesh_for_analysis(self) -> trimesh.Trimesh:
        """Generate mesh for quality analysis without STL conversion.
        
        Returns:
            Trimesh object for analysis
        """
        # Generate 3D volume
        volume = self._generate_volume()
        
        # Use boundary outline method instead of marching cubes if requested
        if self.smoothing_type == "boundary_outline":
            tri_mesh = self._generate_boundary_outline_mesh(volume)
        else:
            # Apply marching cubes
            vertices, faces, normals, values = measure.marching_cubes(
                volume, 
                level=0.5,
                spacing=(1.0, 1.0, self.layer_height)
            )
            
            # Create trimesh object
            tri_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            
            # Apply smoothing if requested
            if self.smoothing_iterations > 0:
                if self.smoothing_type == "laplacian":
                    tri_mesh = self._apply_laplacian_smoothing(tri_mesh, self.smoothing_iterations)
                elif self.smoothing_type == "taubin":
                    tri_mesh = self._apply_taubin_smoothing(tri_mesh, self.smoothing_iterations)
                elif self.smoothing_type == "feature_preserving":
                    tri_mesh = self._apply_feature_preserving_smoothing(tri_mesh, self.smoothing_iterations)
        
        # Validate and repair
        tri_mesh = self._validate_and_repair_mesh(tri_mesh)
        
        return tri_mesh
    
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
        """Save the smooth 3D model as an STL file.
        
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


def generate_smooth_3d_model_from_simulation(width: int, height: int, num_actors: int, 
                                           decay_rate: float, steps: int, 
                                           layer_height: float = 1.0, 
                                           threshold: float = 0.1,
                                           smoothing_iterations: int = 2,
                                           smoothing_type: str = "taubin",
                                           taubin_lambda: float = 0.5,
                                           taubin_mu: float = -0.52,
                                           preserve_features: bool = False,
                                           feature_angle: float = 60.0) -> SmoothModel3DGenerator:
    """Generate a smooth 3D model from a Physarum simulation.
    
    Args:
        width: Simulation grid width
        height: Simulation grid height
        num_actors: Number of Physarum actors
        decay_rate: Trail decay rate
        steps: Number of simulation steps
        layer_height: Height of each layer in 3D model
        threshold: Minimum trail strength for inclusion
        smoothing_iterations: Number of smoothing iterations to apply
        smoothing_type: Type of smoothing ('laplacian', 'taubin', 'feature_preserving', 'boundary_outline')
        taubin_lambda: Lambda parameter for Taubin smoothing
        taubin_mu: Mu parameter for Taubin smoothing
        preserve_features: Whether to preserve sharp features
        feature_angle: Angle threshold for feature preservation
        
    Returns:
        SmoothModel3DGenerator with captured layers
    """
    # Create and run simulation
    sim = PhysarumSimulation(width, height, num_actors, decay_rate)
    
    # Create smooth 3D model generator
    generator = SmoothModel3DGenerator(sim, layer_height, threshold, 
                                     smoothing_iterations, smoothing_type, 
                                     taubin_lambda, taubin_mu, preserve_features, 
                                     feature_angle)
    
    # Run simulation and capture layers
    for step in range(steps):
        sim.step()
        
        # Capture layer every few steps to avoid too many layers
        if step % 5 == 0:  # Capture every 5th step
            generator.capture_layer()
    
    # Capture final layer
    generator.capture_layer()
    
    return generator