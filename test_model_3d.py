# ABOUTME: Comprehensive tests for 3D model generation from Physarum simulation data
# ABOUTME: Tests layer capture, connectivity validation, mesh generation, and STL output

import pytest
import numpy as np
import os
import tempfile
from model_3d import Model3DGenerator, generate_3d_model_from_simulation
from physarum import PhysarumSimulation


class TestModel3DGenerator:
    """Test cases for Model3DGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sim = PhysarumSimulation(width=50, height=50, num_actors=10, decay_rate=0.01)
        self.generator = Model3DGenerator(self.sim, layer_height=1.0, threshold=0.1)
    
    def test_initialization(self):
        """Test Model3DGenerator initialization."""
        assert self.generator.simulation == self.sim
        assert self.generator.layer_height == 1.0
        assert self.generator.threshold == 0.1
        assert len(self.generator.layers) == 0
    
    def test_capture_layer_first_layer(self):
        """Test capturing the first layer uses only simulation data."""
        # Run simulation for a few steps
        self.sim.run(10)
        
        # Capture first layer
        self.generator.capture_layer()
        
        assert len(self.generator.layers) == 1
        first_layer = self.generator.layers[0]
        
        # Verify layer is based on simulation threshold, not artificial base
        trail_map = self.sim.get_trail_map()
        expected_layer = trail_map > self.generator.threshold
        
        assert np.array_equal(first_layer, expected_layer), "First layer should match simulation data above threshold"
    
    def test_capture_multiple_layers(self):
        """Test capturing multiple layers."""
        # Run simulation and capture layers
        for i in range(3):
            self.sim.run(5)
            self.generator.capture_layer()
        
        assert len(self.generator.layers) == 3
        
        # Verify all layers are boolean arrays with correct shape
        for layer in self.generator.layers:
            assert layer.dtype == bool
            assert layer.shape == (50, 50)
    
    def test_find_connected_components(self):
        """Test connected component finding."""
        # Create a test binary mask with known components
        test_mask = np.zeros((10, 10), dtype=bool)
        
        # Component 1: top-left corner
        test_mask[0:3, 0:3] = True
        
        # Component 2: bottom-right corner (disconnected)
        test_mask[7:10, 7:10] = True
        
        components = self.generator._find_connected_components(test_mask)
        
        # Should have exactly 2 components (plus background)
        unique_labels = np.unique(components)
        assert len(unique_labels) == 3  # 0 (background), 1, 2
        assert 0 in unique_labels  # Background
        
        # Verify components are properly separated
        component1_mask = components == 1
        component2_mask = components == 2
        
        # Components should not overlap
        assert not np.any(component1_mask & component2_mask)
        
        # Each component should contain the expected pixels
        assert np.sum(component1_mask) == 9  # 3x3 area
        assert np.sum(component2_mask) == 9  # 3x3 area
    
    def test_upward_connectivity_validation(self):
        """Test that upward connectivity is enforced."""
        # Create first layer from simulation
        self.sim.run(5)
        self.generator.capture_layer()
        first_layer = self.generator.layers[0]
        
        # Manually create a second layer with disconnected components
        second_layer = np.zeros((50, 50), dtype=bool)
        
        # Find some area that exists in the first layer to create a connected component
        first_layer_indices = np.where(first_layer)
        if len(first_layer_indices[0]) > 0:
            # Add connected component overlapping with first layer
            y_idx, x_idx = first_layer_indices[0][0], first_layer_indices[1][0]
            second_layer[y_idx:y_idx+3, x_idx:x_idx+3] = True
        
        # Add disconnected component far from any existing structure
        second_layer[5:8, 5:8] = True
        
        # Test connectivity enforcement
        validated_layer = self.generator._ensure_upward_connectivity(second_layer)
        
        # Only the connected component should remain
        if len(first_layer_indices[0]) > 0:
            y_idx, x_idx = first_layer_indices[0][0], first_layer_indices[1][0]
            assert np.any(validated_layer[y_idx:y_idx+3, x_idx:x_idx+3])
        assert not np.any(validated_layer[5:8, 5:8])
    
    def test_validate_connectivity_valid_model(self):
        """Test connectivity validation for a valid model."""
        # Create a valid model with connected layers
        center_x, center_y = 25, 25  # Center of 50x50 grid
        
        # First layer
        first_layer = np.zeros((50, 50), dtype=bool)
        first_layer[center_y-5:center_y+6, center_x-5:center_x+6] = True
        self.generator.layers.append(first_layer)
        
        # Second layer - smaller area overlapping with first
        second_layer = np.zeros((50, 50), dtype=bool)
        second_layer[center_y-3:center_y+4, center_x-3:center_x+4] = True
        self.generator.layers.append(second_layer)
        
        # Validation should pass
        assert self.generator.validate_connectivity() == True
    
    def test_validate_connectivity_invalid_model(self):
        """Test connectivity validation for an invalid model."""
        # Create an invalid model with disconnected layers
        center_x, center_y = 25, 25  # Center of 50x50 grid
        
        # First layer
        first_layer = np.zeros((50, 50), dtype=bool)
        first_layer[center_y-5:center_y+6, center_x-5:center_x+6] = True
        self.generator.layers.append(first_layer)
        
        # Second layer - disconnected from first
        second_layer = np.zeros((50, 50), dtype=bool)
        second_layer[5:8, 5:8] = True  # Far from first layer
        self.generator.layers.append(second_layer)
        
        # Validation should fail
        assert self.generator.validate_connectivity() == False
    
    def test_mesh_generation_basic(self):
        """Test basic mesh generation functionality."""
        # Create simple layers for testing
        self.sim.run(10)
        self.generator.capture_layer()
        self.sim.run(10)
        self.generator.capture_layer()
        
        # Generate mesh
        stl_mesh = self.generator.generate_mesh()
        
        # Verify mesh has been created
        assert stl_mesh is not None
        assert len(stl_mesh.vectors) > 0
        
        # Verify mesh has proper 3D structure
        for triangle in stl_mesh.vectors:
            assert triangle.shape == (3, 3)  # 3 vertices, 3 coordinates each
    
    def test_mesh_generation_no_layers(self):
        """Test mesh generation fails with no layers."""
        with pytest.raises(ValueError, match="No layers captured"):
            self.generator.generate_mesh()
    
    def test_save_stl_file(self):
        """Test STL file saving."""
        # Create layers
        self.sim.run(10)
        self.generator.capture_layer()
        self.sim.run(10)
        self.generator.capture_layer()
        
        # Save STL to temporary file
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        try:
            self.generator.save_stl(temp_filename)
            
            # Verify file was created and has content
            assert os.path.exists(temp_filename)
            assert os.path.getsize(temp_filename) > 0
            
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_layer_management(self):
        """Test layer counting and clearing."""
        # Initially no layers
        assert self.generator.get_layer_count() == 0
        
        # Add some layers
        for i in range(3):
            self.sim.run(5)
            self.generator.capture_layer()
        
        assert self.generator.get_layer_count() == 3
        
        # Clear layers
        self.generator.clear_layers()
        assert self.generator.get_layer_count() == 0
        assert len(self.generator.layers) == 0


class TestGenerateFunction:
    """Test cases for the generate_3d_model_from_simulation function."""
    
    def test_generate_3d_model_basic(self):
        """Test the high-level 3D model generation function."""
        generator = generate_3d_model_from_simulation(
            width=30, height=30, num_actors=5, decay_rate=0.02,
            steps=25, layer_height=1.5, threshold=0.05
        )
        
        # Verify generator was created properly
        assert isinstance(generator, Model3DGenerator)
        assert generator.layer_height == 1.5
        assert generator.threshold == 0.05
        
        # Should have captured multiple layers (every 5th step + final)
        expected_layers = (25 // 5) + 1  # 5 + 1 = 6 layers
        assert generator.get_layer_count() == expected_layers
        
        # Should have valid connectivity
        assert generator.validate_connectivity() == True
    
    def test_generate_3d_model_parameters(self):
        """Test various parameter combinations."""
        # Test with different parameters
        generator = generate_3d_model_from_simulation(
            width=20, height=20, num_actors=3, decay_rate=0.01,
            steps=15, layer_height=0.5, threshold=0.2
        )
        
        assert generator.simulation.grid.width == 20
        assert generator.simulation.grid.height == 20
        assert len(generator.simulation.actors) == 3
        assert generator.simulation.decay_rate == 0.01
        assert generator.layer_height == 0.5
        assert generator.threshold == 0.2
    
    def test_generate_empty_simulation(self):
        """Test generation with minimal parameters."""
        generator = generate_3d_model_from_simulation(
            width=10, height=10, num_actors=1, decay_rate=0.1,
            steps=5, layer_height=1.0, threshold=0.01
        )
        
        # Should still create valid generator
        assert isinstance(generator, Model3DGenerator)
        assert generator.get_layer_count() > 0


class TestParameterValidation:
    """Test parameter validation and edge cases."""
    
    def test_invalid_simulation_parameters(self):
        """Test Model3DGenerator with invalid simulation parameters."""
        # These should be caught by PhysarumSimulation validation
        with pytest.raises(ValueError):
            PhysarumSimulation(width=-1, height=50, num_actors=10, decay_rate=0.01)
        
        with pytest.raises(ValueError):
            PhysarumSimulation(width=50, height=50, num_actors=0, decay_rate=0.01)
        
        with pytest.raises(ValueError):
            PhysarumSimulation(width=50, height=50, num_actors=10, decay_rate=1.5)
    
    def test_edge_case_parameters(self):
        """Test edge case parameters."""
        # Very small grid
        sim = PhysarumSimulation(width=5, height=5, num_actors=1, decay_rate=0.01)
        generator = Model3DGenerator(sim, layer_height=0.1, threshold=0.01)
        
        # Should work without errors
        sim.run(5)
        generator.capture_layer()
        assert generator.get_layer_count() == 1
        
        # Very high threshold (should result in mostly empty layers)
        generator_high_threshold = Model3DGenerator(
            sim, layer_height=1.0, threshold=10.0
        )
        generator_high_threshold.capture_layer()
        
        # With very high threshold, layer might be mostly empty
        first_layer = generator_high_threshold.layers[0]
        # Layer should be based purely on simulation data above threshold


if __name__ == "__main__":
    pytest.main([__file__])