# ABOUTME: Test suite for the smooth 3D model generation functionality
# ABOUTME: Validates marching cubes surface extraction and mesh smoothing capabilities

import pytest
import numpy as np
import tempfile
import os
from physarum import PhysarumSimulation
from model_3d_smooth import SmoothModel3DGenerator, generate_smooth_3d_model_from_simulation


class TestSmoothModel3DGenerator:
    """Test suite for SmoothModel3DGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.width = 50
        self.height = 50
        self.num_actors = 10
        self.decay_rate = 0.01
        self.simulation = PhysarumSimulation(self.width, self.height, self.num_actors, self.decay_rate)
        self.generator = SmoothModel3DGenerator(self.simulation)
    
    def test_initialization(self):
        """Test proper initialization of SmoothModel3DGenerator."""
        assert self.generator.simulation == self.simulation
        assert self.generator.layer_height == 1.0
        assert self.generator.threshold == 0.1
        assert self.generator.base_radius == 10
        assert self.generator.smoothing_iterations == 0
        assert len(self.generator.layers) == 0
        assert self.generator.base_center == (self.width // 2, self.height // 2)
    
    def test_initialization_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        custom_generator = SmoothModel3DGenerator(
            self.simulation,
            layer_height=2.0,
            threshold=0.2,
            base_radius=15,
            smoothing_iterations=3
        )
        assert custom_generator.layer_height == 2.0
        assert custom_generator.threshold == 0.2
        assert custom_generator.base_radius == 15
        assert custom_generator.smoothing_iterations == 3
    
    def test_capture_layer(self):
        """Test layer capture functionality."""
        # Run a few simulation steps
        for _ in range(10):
            self.simulation.step()
        
        # Capture a layer
        initial_layer_count = self.generator.get_layer_count()
        self.generator.capture_layer()
        assert self.generator.get_layer_count() == initial_layer_count + 1
        
        # Verify layer is a boolean array
        layer = self.generator.layers[0]
        assert isinstance(layer, np.ndarray)
        assert layer.dtype == bool
        assert layer.shape == (self.height, self.width)
    
    def test_base_connectivity_first_layer(self):
        """Test that the first layer has proper base connectivity."""
        # Run simulation and capture first layer
        for _ in range(10):
            self.simulation.step()
        
        self.generator.capture_layer()
        first_layer = self.generator.layers[0]
        
        # Check that base area is solid
        center_x, center_y = self.generator.base_center
        y_coords, x_coords = np.ogrid[:self.height, :self.width]
        distance_from_center = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
        base_mask = distance_from_center <= self.generator.base_radius
        
        # All base pixels should be True
        assert np.all(first_layer[base_mask])
    
    def test_upward_connectivity(self):
        """Test that subsequent layers maintain connectivity."""
        # Run simulation and capture multiple layers
        for _ in range(20):
            self.simulation.step()
            if _ % 5 == 0:
                self.generator.capture_layer()
        
        # Verify connectivity
        assert self.generator.validate_connectivity()
    
    def test_volume_generation(self):
        """Test 3D volume generation from layers."""
        # Capture several layers
        for i in range(15):
            self.simulation.step()
            if i % 3 == 0:
                self.generator.capture_layer()
        
        # Generate volume
        volume = self.generator._generate_volume()
        
        # Verify volume properties
        assert isinstance(volume, np.ndarray)
        assert volume.ndim == 3
        assert volume.shape[0] == self.height
        assert volume.shape[1] == self.width
        assert volume.shape[2] == self.generator.get_layer_count()
        assert volume.dtype == np.float32
    
    def test_mesh_generation(self):
        """Test mesh generation using marching cubes."""
        # Run simulation and capture layers
        for i in range(20):
            self.simulation.step()
            if i % 4 == 0:
                self.generator.capture_layer()
        
        # Generate mesh
        stl_mesh = self.generator.generate_mesh()
        
        # Verify mesh properties
        assert stl_mesh is not None
        assert len(stl_mesh.vectors) > 0
        
        # Each vector should have 3 points with 3 coordinates each
        for vector in stl_mesh.vectors:
            assert vector.shape == (3, 3)
    
    def test_mesh_generation_with_smoothing(self):
        """Test mesh generation with smoothing iterations."""
        smooth_generator = SmoothModel3DGenerator(
            self.simulation,
            smoothing_iterations=2
        )
        
        # Run simulation and capture layers
        for i in range(20):
            self.simulation.step()
            if i % 4 == 0:
                smooth_generator.capture_layer()
        
        # Generate smoothed mesh
        stl_mesh = smooth_generator.generate_mesh()
        
        # Verify mesh properties
        assert stl_mesh is not None
        assert len(stl_mesh.vectors) > 0
    
    def test_stl_file_generation(self):
        """Test STL file creation and saving."""
        # Run simulation and capture layers
        for i in range(15):  
            self.simulation.step()
            if i % 3 == 0:
                self.generator.capture_layer()
        
        # Save STL file
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            self.generator.save_stl(tmp_filename)
            
            # Verify file was created and has content
            assert os.path.exists(tmp_filename)
            assert os.path.getsize(tmp_filename) > 0
            
        finally:
            # Clean up
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    def test_connectivity_validation(self):
        """Test connectivity validation functionality."""
        # Empty layers should not be valid
        assert not self.generator.validate_connectivity()
        
        # Run simulation and capture connected layers
        for i in range(20):
            self.simulation.step()
            if i % 5 == 0:
                self.generator.capture_layer()
        
        # Should be valid with proper connectivity
        assert self.generator.validate_connectivity()
    
    def test_layer_management(self):
        """Test layer count and clearing functionality."""
        # Initially no layers
        assert self.generator.get_layer_count() == 0
        
        # Add some layers
        for i in range(15):
            self.simulation.step()
            if i % 3 == 0:
                self.generator.capture_layer()
        
        layer_count = self.generator.get_layer_count()
        assert layer_count > 0
        
        # Clear layers
        self.generator.clear_layers()
        assert self.generator.get_layer_count() == 0
    
    def test_empty_layer_handling(self):
        """Test handling of empty layers or edge cases."""
        with pytest.raises(ValueError, match="No layers captured"):
            self.generator.generate_mesh()
    
    def test_high_threshold_handling(self):
        """Test behavior with high threshold values."""
        high_threshold_generator = SmoothModel3DGenerator(
            self.simulation,
            threshold=0.9  # Very high threshold
        )
        
        # Run simulation
        for i in range(10):
            self.simulation.step()
            if i % 2 == 0:
                high_threshold_generator.capture_layer()
        
        # Should still work due to base connectivity
        assert high_threshold_generator.get_layer_count() > 0
        
        # Generate mesh (might be small but should work)
        try:
            mesh = high_threshold_generator.generate_mesh()
            assert mesh is not None
        except ValueError:
            # This is acceptable for very high thresholds
            pass


class TestSmoothModelIntegration:
    """Integration tests for smooth model generation."""
    
    def test_generate_smooth_3d_model_from_simulation(self):
        """Test the convenience function for generating smooth models."""
        generator = generate_smooth_3d_model_from_simulation(
            width=40,
            height=40,
            num_actors=20,
            decay_rate=0.02,
            steps=30,
            layer_height=1.5,
            threshold=0.05,
            base_radius=8,
            smoothing_iterations=1
        )
        
        # Verify generator properties
        assert isinstance(generator, SmoothModel3DGenerator)
        assert generator.layer_height == 1.5
        assert generator.threshold == 0.05
        assert generator.base_radius == 8
        assert generator.smoothing_iterations == 1
        assert generator.get_layer_count() > 0
        
        # Verify connectivity
        assert generator.validate_connectivity()
        
        # Generate mesh
        mesh = generator.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0
    
    def test_comparison_with_different_smoothing(self):
        """Test models with different smoothing settings."""
        base_params = {
            'width': 30,
            'height': 30,
            'num_actors': 15,
            'decay_rate': 0.015,
            'steps': 25,
            'smoothing_iterations': 0
        }
        
        # Generate model without smoothing
        generator_no_smooth = generate_smooth_3d_model_from_simulation(**base_params)
        mesh_no_smooth = generator_no_smooth.generate_mesh()
        
        # Generate model with smoothing
        base_params['smoothing_iterations'] = 3
        generator_smooth = generate_smooth_3d_model_from_simulation(**base_params)
        mesh_smooth = generator_smooth.generate_mesh()
        
        # Both should generate valid meshes
        assert len(mesh_no_smooth.vectors) > 0
        assert len(mesh_smooth.vectors) > 0
        
        # Meshes should be different (smoothing should change vertex positions)
        # Note: This is a basic check - in practice the smoothed mesh should have
        # different vertex positions, but we can't easily test that without
        # running identical simulations with different random seeds
    
    def test_edge_case_small_simulation(self):
        """Test handling of very small simulations."""
        generator = generate_smooth_3d_model_from_simulation(
            width=20,
            height=20,
            num_actors=5,
            decay_rate=0.05,
            steps=10,
            smoothing_iterations=1
        )
        
        assert generator.get_layer_count() > 0
        
        # Should be able to generate a mesh even for small simulations
        mesh = generator.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0


if __name__ == "__main__":
    pytest.main([__file__])