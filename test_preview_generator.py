# ABOUTME: Tests for the preview image generation system
# ABOUTME: Verifies preview image creation from simulation data

import unittest
import tempfile
import os
import shutil
import numpy as np
from PIL import Image
from unittest.mock import Mock
from preview_generator import PreviewGenerator


class TestPreviewGenerator(unittest.TestCase):
    """Test cases for PreviewGenerator functionality."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.preview_generator = PreviewGenerator(width=400, height=400)
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_basic_preview_generation(self):
        """Test basic preview image generation from trail map."""
        # Create a simple test trail map
        trail_map = np.zeros((50, 50))
        trail_map[20:30, 20:30] = 1.0  # Create a square of trails
        trail_map[10:15, 35:40] = 0.5  # Create a smaller, dimmer square
        
        output_path = os.path.join(self.test_dir, "test_preview.jpg")
        
        # Generate preview
        self.preview_generator.generate_preview(trail_map, output_path, threshold=0.1)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Verify it's a valid image
        with Image.open(output_path) as img:
            self.assertEqual(img.format, 'JPEG')
            self.assertEqual(img.size, (400, 400))
            self.assertEqual(img.mode, 'RGB')
    
    def test_preview_with_title(self):
        """Test preview generation with title."""
        trail_map = np.random.rand(30, 30) * 0.8
        output_path = os.path.join(self.test_dir, "test_preview_title.jpg")
        
        # Generate preview with title
        self.preview_generator.generate_preview(
            trail_map, 
            output_path, 
            threshold=0.1,
            title="Test Model"
        )
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Load and verify image
        with Image.open(output_path) as img:
            self.assertEqual(img.format, 'JPEG')
            self.assertEqual(img.size, (400, 400))
    
    def test_threshold_filtering(self):
        """Test that threshold properly filters out low values."""
        # Create trail map with specific values
        trail_map = np.full((20, 20), 0.05)  # Below threshold
        trail_map[10:15, 10:15] = 0.8  # Above threshold
        
        output_path = os.path.join(self.test_dir, "test_threshold.jpg")
        
        # Generate with threshold 0.1
        self.preview_generator.generate_preview(trail_map, output_path, threshold=0.1)
        
        # Should create valid image (testing it doesn't crash with mostly-empty data)
        self.assertTrue(os.path.exists(output_path))
        
        with Image.open(output_path) as img:
            self.assertEqual(img.format, 'JPEG')
    
    def test_empty_trail_map(self):
        """Test handling of empty trail map."""
        trail_map = np.zeros((10, 10))
        output_path = os.path.join(self.test_dir, "test_empty.jpg")
        
        # Should not crash with empty data
        self.preview_generator.generate_preview(trail_map, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        with Image.open(output_path) as img:
            self.assertEqual(img.format, 'JPEG')
    
    def test_preview_from_simulation(self):
        """Test preview generation from mock simulation."""
        # Create mock simulation
        mock_simulation = Mock()
        mock_trail_map = np.random.rand(25, 25) * 0.9
        mock_simulation.get_trail_map.return_value = mock_trail_map
        
        output_path = os.path.join(self.test_dir, "test_simulation.jpg")
        
        # Generate preview from simulation
        self.preview_generator.generate_preview_from_simulation(
            mock_simulation,
            output_path,
            threshold=0.2,
            title="Mock Simulation"
        )
        
        # Verify simulation method was called
        mock_simulation.get_trail_map.assert_called_once()
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path))
        
        with Image.open(output_path) as img:
            self.assertEqual(img.format, 'JPEG')
            self.assertEqual(img.size, (400, 400))
    
    def test_custom_colors(self):
        """Test preview generation with custom colors."""
        custom_generator = PreviewGenerator(
            width=200, 
            height=200,
            background_color=(10, 20, 30),
            trail_color=(200, 100, 50)
        )
        
        trail_map = np.random.rand(15, 15) * 0.7
        output_path = os.path.join(self.test_dir, "test_custom_colors.jpg")
        
        custom_generator.generate_preview(trail_map, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        with Image.open(output_path) as img:
            self.assertEqual(img.size, (200, 200))
    
    def test_aspect_ratio_preservation(self):
        """Test that aspect ratio is preserved when scaling."""
        # Create a rectangular trail map
        trail_map = np.ones((10, 30))  # 1:3 aspect ratio
        output_path = os.path.join(self.test_dir, "test_aspect.jpg")
        
        self.preview_generator.generate_preview(trail_map, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        with Image.open(output_path) as img:
            # Should still be square output but trail should be centered
            self.assertEqual(img.size, (400, 400))


if __name__ == '__main__':
    unittest.main()