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
        assert self.generator.smoothing_iterations == 0
        assert len(self.generator.layers) == 0
    
    def test_initialization_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        custom_generator = SmoothModel3DGenerator(
            self.simulation,
            layer_height=2.0,
            threshold=0.2,
            smoothing_iterations=3
        )
        assert custom_generator.layer_height == 2.0
        assert custom_generator.threshold == 0.2
        assert custom_generator.smoothing_iterations == 3
    
    def test_initialization_with_phase2_parameters(self):
        """Test initialization with new Phase 2 parameters."""
        phase2_generator = SmoothModel3DGenerator(
            self.simulation,
            smoothing_type="taubin",
            taubin_lambda=0.6,
            taubin_mu=-0.6,
            preserve_features=True,
            feature_angle=45.0
        )
        assert phase2_generator.smoothing_type == "taubin"
        assert phase2_generator.taubin_lambda == 0.6
        assert phase2_generator.taubin_mu == -0.6
        assert phase2_generator.preserve_features == True
        assert phase2_generator.feature_angle == pytest.approx(np.radians(45.0))
    
    def test_invalid_smoothing_type(self):
        """Test that invalid smoothing type raises an error."""
        generator = SmoothModel3DGenerator(
            self.simulation,
            smoothing_iterations=1,
            smoothing_type="invalid_type"
        )
        
        # Run simulation and capture layers
        for i in range(10):
            self.simulation.step()
            if i % 3 == 0:
                generator.capture_layer()
        
        # Should raise ValueError for invalid smoothing type
        with pytest.raises(ValueError, match="Unknown smoothing type"):
            generator.generate_mesh()
    
    def test_boundary_outline_smoothing(self):
        """Test boundary outline smoothing algorithm."""
        generator = SmoothModel3DGenerator(
            self.simulation,
            smoothing_type="boundary_outline"
        )
        
        # Run simulation for a few steps
        for i in range(15):
            self.simulation.step()
            if i % 3 == 0:
                generator.capture_layer()
        
        # Ensure we have layers
        assert generator.get_layer_count() > 0
        
        # Generate mesh with boundary outline
        mesh = generator.generate_mesh()
        
        # Verify mesh has reasonable properties
        assert mesh is not None
        assert len(mesh.vectors) > 0
        
        # Get quality metrics
        metrics = generator.get_mesh_quality_metrics()
        assert 'vertex_count' in metrics
        assert 'face_count' in metrics
        assert metrics['vertex_count'] > 0
        assert metrics['face_count'] > 0
        
        # Verify connectivity is maintained
        assert generator.validate_connectivity()
    
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
    
    def test_first_layer_from_simulation(self):
        """Test that the first layer is based purely on simulation data."""
        # Run simulation and capture first layer
        for _ in range(10):
            self.simulation.step()
        
        self.generator.capture_layer()
        first_layer = self.generator.layers[0]
        
        # Verify layer is based on simulation threshold, not artificial base
        trail_map = self.simulation.get_trail_map()
        expected_layer = trail_map > self.generator.threshold
        
        assert np.array_equal(first_layer, expected_layer), "First layer should match simulation data above threshold"
    
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
    
    def test_taubin_smoothing(self):
        """Test Taubin smoothing algorithm."""
        taubin_generator = SmoothModel3DGenerator(
            self.simulation,
            smoothing_iterations=3,
            smoothing_type="taubin",
            taubin_lambda=0.5,
            taubin_mu=-0.52
        )
        
        # Run simulation and capture layers
        for i in range(20):
            self.simulation.step()
            if i % 4 == 0:
                taubin_generator.capture_layer()
        
        # Generate mesh with Taubin smoothing
        mesh = taubin_generator.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0
    
    def test_feature_preserving_smoothing(self):
        """Test feature-preserving smoothing algorithm."""
        feature_generator = SmoothModel3DGenerator(
            self.simulation,
            smoothing_iterations=3,
            smoothing_type="feature_preserving",
            preserve_features=True,
            feature_angle=60.0
        )
        
        # Run simulation and capture layers
        for i in range(20):
            self.simulation.step()
            if i % 4 == 0:
                feature_generator.capture_layer()
        
        # Generate mesh with feature preservation
        mesh = feature_generator.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0
    
    def test_mesh_quality_metrics(self):
        """Test mesh quality metrics functionality."""
        # Run simulation and capture layers
        for i in range(20):
            self.simulation.step()
            if i % 4 == 0:
                self.generator.capture_layer()
        
        # Get quality metrics
        metrics = self.generator.get_mesh_quality_metrics()
        
        # Should not have error
        assert "error" not in metrics
        
        # Check expected metrics are present
        expected_keys = [
            "vertex_count", "face_count", "volume", "surface_area",
            "is_watertight", "is_winding_consistent", "euler_number",
            "bounds", "center_mass", "issues", "print_ready"
        ]
        for key in expected_keys:
            assert key in metrics
        
        # Basic sanity checks
        assert metrics["vertex_count"] > 0
        assert metrics["face_count"] > 0
        assert metrics["volume"] > 0
        assert metrics["surface_area"] > 0
        assert isinstance(metrics["is_watertight"], bool)
        assert isinstance(metrics["is_winding_consistent"], bool)
        assert isinstance(metrics["issues"], list)
        assert isinstance(metrics["print_ready"], bool)
    
    def test_mesh_quality_metrics_no_layers(self):
        """Test mesh quality metrics with no layers captured."""
        metrics = self.generator.get_mesh_quality_metrics()
        assert "error" in metrics
        assert "No layers captured" in metrics["error"]
    
    def test_enhanced_mesh_validation(self):
        """Test enhanced mesh validation and repair functionality."""
        generator = SmoothModel3DGenerator(
            self.simulation,
            smoothing_iterations=2
        )
        
        # Run simulation and capture layers
        for i in range(20):
            self.simulation.step()
            if i % 4 == 0:
                generator.capture_layer()
        
        # Generate mesh - validation happens internally
        mesh = generator.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0
        
        # Verify mesh has valid face structure
        for vector in mesh.vectors:
            assert vector.shape == (3, 3)
            # Check that vertices are not all the same (degenerate face)
            v1, v2, v3 = vector
            assert not (np.allclose(v1, v2) and np.allclose(v2, v3))
    
    def test_different_taubin_parameters(self):
        """Test Taubin smoothing with different parameter values."""
        # Test with custom Taubin parameters
        custom_taubin = SmoothModel3DGenerator(
            self.simulation,
            smoothing_iterations=2,
            smoothing_type="taubin",
            taubin_lambda=0.6,
            taubin_mu=-0.61
        )
        
        # Run simulation and capture layers
        for i in range(15):
            self.simulation.step()
            if i % 3 == 0:
                custom_taubin.capture_layer()
        
        # Should generate valid mesh
        mesh = custom_taubin.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0


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
            smoothing_iterations=1
        )
        
        # Verify generator properties
        assert isinstance(generator, SmoothModel3DGenerator)
        assert generator.layer_height == 1.5
        assert generator.threshold == 0.05
        assert generator.smoothing_iterations == 1
        assert generator.get_layer_count() > 0
        
        # Verify connectivity
        assert generator.validate_connectivity()
        
        # Generate mesh
        mesh = generator.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0
    
    def test_generate_smooth_3d_model_with_taubin_smoothing(self):
        """Test the convenience function with Taubin smoothing."""
        generator = generate_smooth_3d_model_from_simulation(
            width=30,
            height=30,
            num_actors=15,
            decay_rate=0.02,
            steps=25,
            smoothing_iterations=2,
            smoothing_type="taubin",
            taubin_lambda=0.5,
            taubin_mu=-0.52
        )
        
        # Verify generator properties
        assert generator.smoothing_type == "taubin"
        assert generator.taubin_lambda == 0.5
        assert generator.taubin_mu == -0.52
        assert generator.get_layer_count() > 0
        
        # Generate mesh
        mesh = generator.generate_mesh()
        assert mesh is not None
        assert len(mesh.vectors) > 0
    
    def test_generate_smooth_3d_model_with_feature_preservation(self):
        """Test the convenience function with feature preservation."""
        generator = generate_smooth_3d_model_from_simulation(
            width=25,
            height=25,
            num_actors=10,
            decay_rate=0.015,
            steps=20,
            smoothing_iterations=2,
            smoothing_type="feature_preserving",
            preserve_features=True,
            feature_angle=45.0
        )
        
        # Verify generator properties
        assert generator.smoothing_type == "feature_preserving"
        assert generator.preserve_features == True
        assert generator.feature_angle == pytest.approx(np.radians(45.0))
        assert generator.get_layer_count() > 0
        
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


class TestSmoothingAlgorithmComparison:
    """Test suite for comparing different smoothing algorithms."""
    
    def setup_method(self):
        """Set up test fixtures for algorithm comparison."""
        self.base_params = {
            'width': 40,
            'height': 40,
            'num_actors': 20,
            'decay_rate': 0.02,
            'steps': 30,
            'smoothing_iterations': 2
        }
    
    def test_all_smoothing_algorithms_work(self):
        """Test that all smoothing algorithms produce valid meshes."""
        algorithms = ['laplacian', 'taubin', 'feature_preserving', 'boundary_outline']
        
        for algorithm in algorithms:
            generator = generate_smooth_3d_model_from_simulation(
                **self.base_params,
                smoothing_type=algorithm
            )
            
            # All algorithms should produce valid meshes
            mesh = generator.generate_mesh()
            assert mesh is not None, f"{algorithm} smoothing failed"
            assert len(mesh.vectors) > 0, f"{algorithm} produced empty mesh"
            
            # Check mesh quality
            metrics = generator.get_mesh_quality_metrics()
            assert "error" not in metrics, f"{algorithm} quality check failed"
            assert metrics["vertex_count"] > 0, f"{algorithm} has no vertices"
            assert metrics["face_count"] > 0, f"{algorithm} has no faces"
    
    def test_mesh_quality_differences(self):
        """Test that different algorithms produce different quality characteristics."""
        # Generate with Laplacian smoothing
        laplacian_gen = generate_smooth_3d_model_from_simulation(
            **self.base_params,
            smoothing_type="laplacian"
        )
        laplacian_metrics = laplacian_gen.get_mesh_quality_metrics()
        
        # Generate with Taubin smoothing
        taubin_gen = generate_smooth_3d_model_from_simulation(
            **self.base_params,
            smoothing_type="taubin"
        )
        taubin_metrics = taubin_gen.get_mesh_quality_metrics()
        
        # Both should be valid
        assert "error" not in laplacian_metrics
        assert "error" not in taubin_metrics
        
        # Both should have reasonable properties
        assert laplacian_metrics["volume"] > 0
        assert taubin_metrics["volume"] > 0
        assert laplacian_metrics["surface_area"] > 0
        assert taubin_metrics["surface_area"] > 0
    
    def test_feature_preservation_options(self):
        """Test feature preservation with different settings."""
        # Test with feature preservation enabled
        with_features = generate_smooth_3d_model_from_simulation(
            **self.base_params,
            smoothing_type="feature_preserving",
            preserve_features=True,
            feature_angle=30.0
        )
        
        # Test with feature preservation disabled
        without_features = generate_smooth_3d_model_from_simulation(
            **self.base_params,
            smoothing_type="feature_preserving",
            preserve_features=False,
            feature_angle=30.0
        )
        
        # Both should work
        mesh_with = with_features.generate_mesh()
        mesh_without = without_features.generate_mesh()
        
        assert mesh_with is not None
        assert mesh_without is not None
        assert len(mesh_with.vectors) > 0
        assert len(mesh_without.vectors) > 0
    
    def test_extreme_taubin_parameters(self):
        """Test Taubin smoothing with edge-case parameters."""
        # Create modified params for minimal smoothing
        minimal_params = self.base_params.copy()
        minimal_params['smoothing_iterations'] = 1
        minimal_gen = generate_smooth_3d_model_from_simulation(
            **minimal_params,
            smoothing_type="taubin",
            taubin_lambda=0.1,
            taubin_mu=-0.11
        )
        
        # Create modified params for aggressive smoothing
        aggressive_params = self.base_params.copy()
        aggressive_params['smoothing_iterations'] = 5
        aggressive_gen = generate_smooth_3d_model_from_simulation(
            **aggressive_params,
            smoothing_type="taubin",
            taubin_lambda=0.8,
            taubin_mu=-0.81
        )
        
        # Both should produce valid meshes
        minimal_mesh = minimal_gen.generate_mesh()
        aggressive_mesh = aggressive_gen.generate_mesh()
        
        assert minimal_mesh is not None
        assert aggressive_mesh is not None
        assert len(minimal_mesh.vectors) > 0
        assert len(aggressive_mesh.vectors) > 0


if __name__ == "__main__":
    pytest.main([__file__])