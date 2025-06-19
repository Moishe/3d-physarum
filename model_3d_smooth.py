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
                 threshold: float = 0.1, base_radius: int = 10, smoothing_iterations: int = 0,
                 smoothing_type: str = "laplacian", taubin_lambda: float = 0.5, 
                 taubin_mu: float = -0.52, preserve_features: bool = False,
                 feature_angle: float = 60.0):
        """Initialize the smooth 3D model generator.
        
        Args:
            simulation: The Physarum simulation to generate models from
            layer_height: Height of each simulation step in the Z-axis
            threshold: Minimum trail strength to include in 3D model
            base_radius: Radius of the central base constraint
            smoothing_iterations: Number of smoothing iterations to apply
            smoothing_type: Type of smoothing ('laplacian', 'taubin', 'feature_preserving')
            taubin_lambda: Lambda parameter for Taubin smoothing (shrinking factor)
            taubin_mu: Mu parameter for Taubin smoothing (anti-shrinking factor)
            preserve_features: Whether to preserve sharp features during smoothing
            feature_angle: Angle threshold (degrees) for feature preservation
        """
        self.simulation = simulation
        self.layer_height = layer_height
        self.threshold = threshold
        self.base_radius = base_radius
        self.smoothing_iterations = smoothing_iterations
        self.smoothing_type = smoothing_type
        self.taubin_lambda = taubin_lambda
        self.taubin_mu = taubin_mu
        self.preserve_features = preserve_features
        self.feature_angle = np.radians(feature_angle)
        self.layers = []  # Store simulation frames as layers
        self.base_center = (simulation.grid.width // 2, simulation.grid.height // 2)
        
    def capture_layer(self) -> None:
        """Capture current simulation state as a 3D layer."""
        # Get current trail map
        trail_map = self.simulation.get_trail_map()
        
        # Apply threshold to create binary mask
        layer_mask = trail_map > self.threshold
        
        # Ensure base connectivity if this is the first layer
        if len(self.layers) == 0:
            layer_mask = self._ensure_base_connectivity(layer_mask)
        else:
            # For subsequent layers, ensure connectivity to previous layer
            layer_mask = self._ensure_upward_connectivity(layer_mask)
        
        self.layers.append(layer_mask)
    
    def _ensure_base_connectivity(self, layer_mask: np.ndarray) -> np.ndarray:
        """Ensure the first layer has a solid base at the center.
        
        Args:
            layer_mask: Binary mask of the current layer
            
        Returns:
            Modified layer mask with base connectivity
        """
        modified_mask = layer_mask.copy()
        center_x, center_y = self.base_center
        
        # Create circular base area
        y_coords, x_coords = np.ogrid[:layer_mask.shape[0], :layer_mask.shape[1]]
        distance_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        base_mask = distance_from_center <= self.base_radius
        
        # Ensure base area is solid
        modified_mask[base_mask] = True
        
        return modified_mask
    
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
        
        # Apply smoothing if requested
        if self.smoothing_iterations > 0:
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
                                           base_radius: int = 10,
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
        base_radius: Radius of the base constraint
        smoothing_iterations: Number of smoothing iterations to apply
        smoothing_type: Type of smoothing ('laplacian', 'taubin', 'feature_preserving')
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
    generator = SmoothModel3DGenerator(sim, layer_height, threshold, base_radius, 
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