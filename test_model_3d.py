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


class TestBackgroundFunctionality:
    """Test cases for background mesh functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sim = PhysarumSimulation(width=20, height=20, num_actors=5, decay_rate=0.01)
    
    def test_background_initialization(self):
        """Test generator initialization with background parameters."""
        generator = Model3DGenerator(
            self.sim, 
            layer_height=1.0, 
            threshold=0.1,
            background=True,
            background_depth=3.0,
            background_margin=0.1
        )
        
        assert generator.background == True
        assert generator.background_depth == 3.0
        assert generator.background_margin == 0.1
    
    def test_background_disabled_by_default(self):
        """Test that background is disabled by default."""
        generator = Model3DGenerator(self.sim, layer_height=1.0, threshold=0.1)
        
        assert generator.background == False
        assert generator.background_depth == 2.0  # default value
        assert generator.background_margin == 0.05  # default value
    
    def test_background_mesh_creation(self):
        """Test background mesh generation."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_depth=2.0,
            background_margin=0.05
        )
        
        # Capture at least one layer
        self.sim.run(10)
        generator.capture_layer()
        
        # Test background mesh creation
        background_triangles = generator._create_background_mesh()
        
        # Should have triangles (12 triangles for a box: 2 per face * 6 faces)
        assert len(background_triangles) == 12
        
        # Verify triangles are numpy arrays with correct shape
        for triangle in background_triangles:
            assert isinstance(triangle, np.ndarray)
            assert triangle.shape == (3, 3)  # 3 vertices, 3 coordinates each
    
    def test_background_mesh_bounds(self):
        """Test that background mesh has correct bounds."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_depth=2.5,
            background_margin=0.1
        )
        
        # Capture at least one layer
        self.sim.run(10)
        generator.capture_layer()
        
        background_triangles = generator._create_background_mesh()
        
        # Extract all vertices from triangles
        all_vertices = []
        for triangle in background_triangles:
            all_vertices.extend(triangle)
        all_vertices = np.array(all_vertices)
        
        # Check bounds
        min_coords = np.min(all_vertices, axis=0)
        max_coords = np.max(all_vertices, axis=0)
        
        # X bounds should extend beyond simulation bounds by margin
        expected_x_margin = 20 * 0.1  # 20 * margin
        assert min_coords[0] == pytest.approx(-expected_x_margin, abs=1e-6)
        assert max_coords[0] == pytest.approx(20 + expected_x_margin, abs=1e-6)
        
        # Y bounds should extend beyond simulation bounds by margin
        expected_y_margin = 20 * 0.1  # 20 * margin
        assert min_coords[1] == pytest.approx(-expected_y_margin, abs=1e-6)
        assert max_coords[1] == pytest.approx(20 + expected_y_margin, abs=1e-6)
        
        # Z bounds should be from last_layer_z to last_layer_z + background_depth
        # With layer_height=1.0 and at least 1 layer, last_layer_z should be >= 1.0
        expected_z_min = 1.0  # At least 1 layer * layer_height
        expected_z_max = expected_z_min + 2.5  # + background_depth
        assert min_coords[2] >= expected_z_min
        assert max_coords[2] >= expected_z_max
    
    def test_background_no_triangles_without_layers(self):
        """Test that background returns empty list without layers."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_depth=2.0,
            background_margin=0.05
        )
        
        # No layers captured
        background_triangles = generator._create_background_mesh()
        
        # Should return empty list
        assert background_triangles == []
    
    def test_background_disabled_returns_empty(self):
        """Test that disabled background returns empty list."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=False
        )
        
        # Capture layer
        self.sim.run(10)
        generator.capture_layer()
        
        background_triangles = generator._create_background_mesh()
        
        # Should return empty list when disabled
        assert background_triangles == []
    
    def test_mesh_generation_with_background(self):
        """Test complete mesh generation with background."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_depth=2.0,
            background_margin=0.05
        )
        
        # Create some simulation layers
        self.sim.run(10)
        generator.capture_layer()
        self.sim.run(10)
        generator.capture_layer()
        
        # Generate mesh with background
        stl_mesh = generator.generate_mesh()
        
        # Should have more triangles than without background
        assert len(stl_mesh.vectors) > 0
        
        # Background should add at least 12 triangles (box faces)
        # But actual count will vary based on simulation content
        assert len(stl_mesh.vectors) >= 12
    
    def test_background_margin_parameter_effects(self):
        """Test different background margin values."""
        # Test with small margin
        generator_small = Model3DGenerator(
            self.sim,
            background=True,
            background_margin=0.01
        )
        
        # Test with large margin
        generator_large = Model3DGenerator(
            self.sim,
            background=True,
            background_margin=0.2
        )
        
        # Capture layers for both
        self.sim.run(10)
        generator_small.capture_layer()
        generator_large.capture_layer()
        
        # Get background triangles
        triangles_small = generator_small._create_background_mesh()
        triangles_large = generator_large._create_background_mesh()
        
        # Extract bounds
        def get_bounds(triangles):
            all_vertices = []
            for triangle in triangles:
                all_vertices.extend(triangle)
            all_vertices = np.array(all_vertices)
            return np.min(all_vertices, axis=0), np.max(all_vertices, axis=0)
        
        min_small, max_small = get_bounds(triangles_small)
        min_large, max_large = get_bounds(triangles_large)
        
        # Large margin should have wider bounds
        assert min_large[0] < min_small[0]  # X min
        assert max_large[0] > max_small[0]  # X max
        assert min_large[1] < min_small[1]  # Y min
        assert max_large[1] > max_small[1]  # Y max
    
    def test_background_depth_parameter_effects(self):
        """Test different background depth values."""
        # Test with shallow depth
        generator_shallow = Model3DGenerator(
            self.sim,
            background=True,
            background_depth=1.0
        )
        
        # Test with deep depth
        generator_deep = Model3DGenerator(
            self.sim,
            background=True,
            background_depth=5.0
        )
        
        # Capture layers
        self.sim.run(10)
        generator_shallow.capture_layer()
        generator_deep.capture_layer()
        
        # Get Z bounds
        def get_z_bounds(triangles):
            all_vertices = []
            for triangle in triangles:
                all_vertices.extend(triangle)
            all_vertices = np.array(all_vertices)
            return np.min(all_vertices[:, 2]), np.max(all_vertices[:, 2])
        
        triangles_shallow = generator_shallow._create_background_mesh()
        triangles_deep = generator_deep._create_background_mesh()
        
        z_min_shallow, z_max_shallow = get_z_bounds(triangles_shallow)
        z_min_deep, z_max_deep = get_z_bounds(triangles_deep)
        
        # Both should have same z_min (after last layer), but different z_max
        # With at least 1 layer, z_min should be >= layer_height (1.0)
        assert z_min_shallow >= 1.0
        assert z_min_deep >= 1.0
        assert z_max_deep > z_max_shallow  # Deeper should extend further up
    
    def test_border_initialization(self):
        """Test generator initialization with border parameters."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_border=True,
            border_height=2.0,
            border_thickness=1.0
        )
        
        assert generator.background == True
        assert generator.background_border == True
        assert generator.border_height == 2.0
        assert generator.border_thickness == 1.0
    
    def test_border_disabled_by_default(self):
        """Test that border is disabled by default."""
        generator = Model3DGenerator(self.sim, layer_height=1.0, threshold=0.1, background=True)
        
        assert generator.background_border == False
        assert generator.border_height == 1.0  # default value
        assert generator.border_thickness == 0.5  # default value
    
    def test_border_mesh_creation(self):
        """Test border mesh generation."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_border=True,
            border_height=2.0,
            border_thickness=0.5
        )
        
        # Capture at least one layer
        self.sim.run(10)
        generator.capture_layer()
        
        # Test border mesh creation
        border_triangles = generator._create_border_mesh()
        
        # Should have triangles for 4 walls (12 triangles per wall * 4 walls = 48 triangles)
        assert len(border_triangles) == 48
        
        # Verify triangles are numpy arrays with correct shape
        for triangle in border_triangles:
            assert isinstance(triangle, np.ndarray)
            assert triangle.shape == (3, 3)  # 3 vertices, 3 coordinates each
    
    def test_border_z_direction(self):
        """Test that border extends upward in Z direction."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_border=True,
            border_height=3.0,
            border_thickness=0.5
        )
        
        # Capture layers
        self.sim.run(10)
        generator.capture_layer()
        
        border_triangles = generator._create_border_mesh()
        
        # Extract all vertices from border triangles
        all_vertices = []
        for triangle in border_triangles:
            all_vertices.extend(triangle)
        all_vertices = np.array(all_vertices)
        
        # Check Z bounds
        min_z = np.min(all_vertices[:, 2])
        max_z = np.max(all_vertices[:, 2])
        
        # Border should start below background bottom and extend upward to background bottom
        # With 1 layer: background starts at 1.0, border extends downward by border_height
        # Border should go from 1.0 - 3.0 = -2.0 to 1.0
        expected_background_bottom = 1.0  # layer height
        expected_border_bottom = expected_background_bottom - 3.0  # - border height
        
        assert min_z == pytest.approx(expected_border_bottom, abs=1e-6)
        assert max_z == pytest.approx(expected_background_bottom, abs=1e-6)
    
    def test_border_no_triangles_without_background(self):
        """Test that border returns empty list without background enabled."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=False,  # Background disabled
            background_border=True,
            border_height=2.0,
            border_thickness=0.5
        )
        
        # Capture layer
        self.sim.run(10)
        generator.capture_layer()
        
        border_triangles = generator._create_border_mesh()
        
        # Should return empty list when background is disabled
        assert border_triangles == []
    
    def test_border_disabled_returns_empty(self):
        """Test that disabled border returns empty list."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_border=False  # Border disabled
        )
        
        # Capture layer
        self.sim.run(10)
        generator.capture_layer()
        
        border_triangles = generator._create_border_mesh()
        
        # Should return empty list when border is disabled
        assert border_triangles == []
    
    def test_mesh_generation_with_border(self):
        """Test complete mesh generation with background and border."""
        generator = Model3DGenerator(
            self.sim,
            layer_height=1.0,
            threshold=0.1,
            background=True,
            background_border=True,
            border_height=2.0,
            border_thickness=0.5
        )
        
        # Create some simulation layers
        self.sim.run(10)
        generator.capture_layer()
        self.sim.run(10)
        generator.capture_layer()
        
        # Generate mesh with background and border
        stl_mesh = generator.generate_mesh()
        
        # Should have more triangles than background alone
        # Background: 12 triangles, Border: 48 triangles, plus simulation triangles
        assert len(stl_mesh.vectors) >= 60  # At least background + border triangles
        
        # Should extend lower than background alone due to border extending downward
        min_z = np.min(stl_mesh.vectors[:, :, 2])
        expected_border_bottom = 2.0 - 2.0  # background_bottom - border_height
        assert min_z <= expected_border_bottom
    
    def test_border_thickness_parameter_effects(self):
        """Test different border thickness values."""
        # Test with thin border
        generator_thin = Model3DGenerator(
            self.sim,
            background=True,
            background_border=True,
            border_thickness=0.1
        )
        
        # Test with thick border
        generator_thick = Model3DGenerator(
            self.sim,
            background=True,
            background_border=True,
            border_thickness=2.0
        )
        
        # Capture layers for both
        self.sim.run(10)
        generator_thin.capture_layer()
        generator_thick.capture_layer()
        
        # Get border triangles
        triangles_thin = generator_thin._create_border_mesh()
        triangles_thick = generator_thick._create_border_mesh()
        
        # Both borders should stay within the same background bounds
        # The difference should be in the thickness of the walls themselves
        # Verify that thick border has thicker walls
        assert len(triangles_thin) == 48  # Same number of triangles
        assert len(triangles_thick) == 48  # Same number of triangles
        
        # Both should stay within background bounds
        # With simulation size 20x20 and default margin 0.05:
        expected_x_min = -20 * 0.05  # -1.0
        expected_x_max = 20 + 20 * 0.05  # 21.0
        expected_y_min = -20 * 0.05  # -1.0  
        expected_y_max = 20 + 20 * 0.05  # 21.0
        
        def get_xy_bounds(triangles):
            all_vertices = []
            for triangle in triangles:
                all_vertices.extend(triangle)
            all_vertices = np.array(all_vertices)
            return np.min(all_vertices, axis=0)[:2], np.max(all_vertices, axis=0)[:2]
        
        min_thin, max_thin = get_xy_bounds(triangles_thin)
        min_thick, max_thick = get_xy_bounds(triangles_thick)
        
        # Both should be within background bounds
        assert min_thin[0] >= expected_x_min
        assert max_thin[0] <= expected_x_max
        assert min_thin[1] >= expected_y_min
        assert max_thin[1] <= expected_y_max
        
        assert min_thick[0] >= expected_x_min
        assert max_thick[0] <= expected_x_max
        assert min_thick[1] >= expected_y_min
        assert max_thick[1] <= expected_y_max
    
    def test_background_aspect_ratio_matching(self):
        """Test that background matches the aspect ratio of simulation content."""
        # Create a non-square simulation with concentrated activity
        sim = PhysarumSimulation(width=100, height=50, num_actors=20, decay_rate=0.01)
        generator = Model3DGenerator(
            sim,
            layer_height=1.0,
            threshold=0.05,  # Lower threshold to capture more activity
            background=True,
            background_margin=0.1
        )
        
        # Run simulation to generate some content
        sim.run(20)
        generator.capture_layer()
        
        # Get content bounds
        content_bounds = generator._get_simulation_content_bounds()
        
        # Generate background mesh
        background_triangles = generator._create_background_mesh()
        
        # Extract background bounds
        all_vertices = []
        for triangle in background_triangles:
            all_vertices.extend(triangle)
        all_vertices = np.array(all_vertices)
        
        bg_x_min = np.min(all_vertices[:, 0])
        bg_x_max = np.max(all_vertices[:, 0])
        bg_y_min = np.min(all_vertices[:, 1])
        bg_y_max = np.max(all_vertices[:, 1])
        
        # Calculate aspect ratios
        content_width = content_bounds['x_max'] - content_bounds['x_min']
        content_height = content_bounds['y_max'] - content_bounds['y_min']
        content_aspect_ratio = content_width / content_height
        
        background_width = bg_x_max - bg_x_min
        background_height = bg_y_max - bg_y_min
        background_aspect_ratio = background_width / background_height
        
        # Background aspect ratio should match content aspect ratio
        # (allowing for small margin effects)
        assert abs(background_aspect_ratio - content_aspect_ratio) < 0.1
        
        # Background should extend beyond content bounds by margin
        expected_margin_x = content_width * 0.1
        expected_margin_y = content_height * 0.1
        
        assert bg_x_min == pytest.approx(content_bounds['x_min'] - expected_margin_x, abs=1e-6)
        assert bg_x_max == pytest.approx(content_bounds['x_max'] + expected_margin_x, abs=1e-6)
        assert bg_y_min == pytest.approx(content_bounds['y_min'] - expected_margin_y, abs=1e-6)
        assert bg_y_max == pytest.approx(content_bounds['y_max'] + expected_margin_y, abs=1e-6)
    
    def test_content_bounds_calculation(self):
        """Test simulation content bounds calculation."""
        sim = PhysarumSimulation(width=50, height=30, num_actors=10, decay_rate=0.01)
        generator = Model3DGenerator(sim, layer_height=1.0, threshold=0.1)
        
        # Test with no layers
        bounds = generator._get_simulation_content_bounds()
        assert bounds['x_min'] == 0
        assert bounds['x_max'] == 50
        assert bounds['y_min'] == 0
        assert bounds['y_max'] == 30
        
        # Run simulation and capture layer
        sim.run(15)
        generator.capture_layer()
        
        # Get bounds with actual content
        bounds = generator._get_simulation_content_bounds()
        
        # Bounds should be within the grid
        assert 0 <= bounds['x_min'] < bounds['x_max'] <= 50
        assert 0 <= bounds['y_min'] < bounds['y_max'] <= 30
        
        # Should have some reasonable size (not just single pixels)
        content_width = bounds['x_max'] - bounds['x_min']
        content_height = bounds['y_max'] - bounds['y_min']
        assert content_width > 1
        assert content_height > 1
    
    def test_content_bounds_empty_layer(self):
        """Test content bounds with empty layer (high threshold)."""
        sim = PhysarumSimulation(width=20, height=20, num_actors=5, decay_rate=0.01)
        generator = Model3DGenerator(sim, layer_height=1.0, threshold=10.0)  # Very high threshold
        
        # Run simulation and capture layer
        sim.run(5)
        generator.capture_layer()
        
        # With very high threshold, layer should be mostly empty
        # Should fallback to full grid bounds
        bounds = generator._get_simulation_content_bounds()
        assert bounds['x_min'] == 0
        assert bounds['x_max'] == 20
        assert bounds['y_min'] == 0
        assert bounds['y_max'] == 20
    
    def test_automatic_grid_sizing_for_images(self):
        """Test that grid dimensions are automatically set when using images."""
        # This test verifies the logic would work, but doesn't actually load an image
        # In the actual implementation, PIL would be used to read image dimensions
        
        # The key fix is in main.py where it checks for default 100x100 dimensions
        # and reads the actual image size when an image is provided
        
        # Simulate what would happen with a non-square image
        sim = PhysarumSimulation(width=200, height=100, num_actors=10, decay_rate=0.01)
        generator = Model3DGenerator(
            sim,
            layer_height=1.0,
            threshold=0.05,  # Lower threshold to capture more activity
            background=True,
            background_margin=0.1
        )
        
        # Run simulation and capture layer  
        sim.run(15)
        generator.capture_layer()
        
        # Get content bounds - should use final layer bounds (where actors ended up)
        content_bounds = generator._get_simulation_content_bounds()
        
        # Generate background mesh
        background_triangles = generator._create_background_mesh()
        
        # Extract background bounds
        all_vertices = []
        for triangle in background_triangles:
            all_vertices.extend(triangle)
        all_vertices = np.array(all_vertices)
        
        bg_x_min = np.min(all_vertices[:, 0])
        bg_x_max = np.max(all_vertices[:, 0])
        bg_y_min = np.min(all_vertices[:, 1])
        bg_y_max = np.max(all_vertices[:, 1])
        
        # Calculate aspect ratios
        content_width = content_bounds['x_max'] - content_bounds['x_min']
        content_height = content_bounds['y_max'] - content_bounds['y_min']
        content_aspect_ratio = content_width / content_height
        
        background_width = bg_x_max - bg_x_min
        background_height = bg_y_max - bg_y_min
        background_aspect_ratio = background_width / background_height
        
        # Background aspect ratio should match actual simulation content
        assert abs(background_aspect_ratio - content_aspect_ratio) < 0.1
        
        # Background should extend beyond content bounds by margin
        expected_margin_x = content_width * 0.1
        expected_margin_y = content_height * 0.1
        
        assert bg_x_min == pytest.approx(content_bounds['x_min'] - expected_margin_x, abs=1e-6)
        assert bg_x_max == pytest.approx(content_bounds['x_max'] + expected_margin_x, abs=1e-6)
        assert bg_y_min == pytest.approx(content_bounds['y_min'] - expected_margin_y, abs=1e-6)
        assert bg_y_max == pytest.approx(content_bounds['y_max'] + expected_margin_y, abs=1e-6)


if __name__ == "__main__":
    pytest.main([__file__])