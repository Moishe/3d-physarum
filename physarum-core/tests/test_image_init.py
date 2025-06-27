# ABOUTME: Tests for image-based actor initialization functionality
# ABOUTME: Covers image loading, sizing, centering, and black pixel detection

import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from physarum_core.simulation import PhysarumSimulation


class TestImageInitialization:
    """Test image-based actor initialization."""
    
    def create_test_image(self, width: int, height: int, black_pixels: list, format='JPEG') -> str:
        """Create a test image with specified black pixels.
        
        Args:
            width: Image width
            height: Image height
            black_pixels: List of (x, y) coordinates for black pixels
            format: Image format ('JPEG' or 'PNG')
            
        Returns:
            Path to the created temporary image file
        """
        # Create white image
        img_array = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Set black pixels - use pure black (0,0,0) for better JPEG compression
        for x, y in black_pixels:
            if 0 <= x < width and 0 <= y < height:
                img_array[y, x] = [0, 0, 0]  # Pure black
        
        # Save as temporary image
        image = Image.fromarray(img_array)
        suffix = '.jpg' if format == 'JPEG' else '.png'
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        
        if format == 'JPEG':
            # Use high quality to minimize compression artifacts
            image.save(temp_file.name, 'JPEG', quality=95)
        else:
            image.save(temp_file.name, 'PNG')
        temp_file.close()
        
        return temp_file.name
    
    def test_simple_image_loading(self):
        """Test basic image loading with exact grid size match."""
        # Create 10x10 image with 3 black pixels
        black_pixels = [(2, 3), (5, 7), (8, 1)]
        image_path = self.create_test_image(10, 10, black_pixels)
        
        try:
            # Create simulation with matching grid size
            sim = PhysarumSimulation(
                width=10, height=10, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # Should have exactly 3 actors (one per black pixel)
            assert len(sim.actors) == 3
            
            # Check actor positions match black pixel locations (with Y-coordinate flipped)
            actor_positions = [(int(actor.x), int(actor.y)) for actor in sim.actors]
            # Y-coordinates are flipped from image space to simulation space
            expected_positions = [(x, 9 - y) for x, y in black_pixels]  # 9 = height - 1
            for pos in expected_positions:
                assert pos in actor_positions
                
        finally:
            os.unlink(image_path)
    
    def test_image_smaller_than_grid(self):
        """Test image smaller than grid - should be centered."""
        # Create 6x4 image with black pixels - use PNG for precision
        black_pixels = [(1, 1), (3, 2), (5, 3)]
        image_path = self.create_test_image(6, 4, black_pixels, format='PNG')
        
        try:
            # Create simulation with larger grid (10x8)
            sim = PhysarumSimulation(
                width=10, height=8, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # Should have 3 actors
            assert len(sim.actors) == 3
            
            # Actors should be offset by centering calculation with Y-coordinate flipping
            # Image is 6x4, grid is 10x8
            # Offset: ((10-6)//2, (8-4)//2) = (2, 2)
            # Y-coordinates are flipped: (image_height - 1 - y) = (4 - 1 - y) = (3 - y)
            expected_positions = [(x + 2, (3 - y) + 2) for x, y in black_pixels]
            actor_positions = [(int(actor.x), int(actor.y)) for actor in sim.actors]
            
            for pos in expected_positions:
                assert pos in actor_positions
                
        finally:
            os.unlink(image_path)
    
    def test_image_larger_than_grid(self):
        """Test image larger than grid - should use center crop."""
        # Create 12x10 image with black pixels
        black_pixels = [(2, 2), (6, 5), (9, 7)]  # These should be in center crop
        image_path = self.create_test_image(12, 10, black_pixels)
        
        try:
            # Create simulation with smaller grid (8x6)
            sim = PhysarumSimulation(
                width=8, height=6, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # Should have 3 actors if all black pixels are in the center crop
            # Center crop: from (2, 2) to (10, 8) for 8x6 grid
            assert len(sim.actors) == 3
            
            # Actors should be offset by crop calculation with Y-coordinate flipping
            # Crop starts at ((12-8)//2, (10-6)//2) = (2, 2) 
            # Y-coordinates are flipped in the 6-high cropped section: (5 - (y - 2)) = (7 - y)
            expected_positions = [(x - 2, 7 - y) for x, y in black_pixels]
            actor_positions = [(int(actor.x), int(actor.y)) for actor in sim.actors]
            
            for pos in expected_positions:
                assert pos in actor_positions
                
        finally:
            os.unlink(image_path)
    
    def test_black_pixel_detection(self):
        """Test detection of black pixels with different thresholds - using PNG for precision."""
        # Create image with pixels of different darkness levels
        img_array = np.ones((5, 5, 3), dtype=np.uint8) * 255
        
        # Set pixels with different RGB values
        img_array[1, 1] = [0, 0, 0]      # Pure black - should be detected
        img_array[2, 2] = [15, 15, 15]   # Dark gray - should be detected
        img_array[3, 3] = [16, 16, 16]   # Light gray - should NOT be detected
        img_array[4, 4] = [10, 20, 5]    # Mixed, max > 16 - should NOT be detected
        img_array[0, 4] = [5, 10, 15]    # Mixed, all < 16 - should be detected
        
        image = Image.fromarray(img_array)
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        image.save(temp_file.name, 'PNG')
        temp_file.close()
        
        try:
            sim = PhysarumSimulation(
                width=5, height=5, num_actors=50, decay_rate=0.01,
                image_path=temp_file.name
            )
            
            # Should detect 3 black pixels: (1,1), (2,2), (4,0) with Y-coordinate flipped
            assert len(sim.actors) == 3
            
            actor_positions = {(int(actor.x), int(actor.y)) for actor in sim.actors}
            # Y-coordinates are flipped in the 5-high image: (4 - y) 
            expected_positions = {(1, 3), (2, 2), (4, 4)}  # (1,4-1), (2,4-2), (4,4-0)
            
            assert actor_positions == expected_positions
            
        finally:
            os.unlink(temp_file.name)
    
    def test_jpeg_black_pixel_detection(self):
        """Test that JPEG black pixels are detected despite compression artifacts."""
        # Use very dark pixels that should survive JPEG compression
        black_pixels = [(1, 1), (3, 3), (2, 4)]
        image_path = self.create_test_image(5, 5, black_pixels, format='JPEG')
        
        try:
            sim = PhysarumSimulation(
                width=5, height=5, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # Should detect some black pixels (may not be exact due to JPEG compression)
            assert len(sim.actors) >= 2  # At least most black pixels should be detected
            
        finally:
            os.unlink(image_path)
    
    def test_empty_image(self):
        """Test image with no black pixels."""
        # Create all-white image
        image_path = self.create_test_image(5, 5, [])
        
        try:
            sim = PhysarumSimulation(
                width=5, height=5, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # Should have no actors
            assert len(sim.actors) == 0
            
        finally:
            os.unlink(image_path)
    
    def test_all_black_image(self):
        """Test image with all black pixels."""
        # Create all-black image (3x3)
        black_pixels = [(x, y) for x in range(3) for y in range(3)]
        image_path = self.create_test_image(3, 3, black_pixels)
        
        try:
            sim = PhysarumSimulation(
                width=3, height=3, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # Should have 9 actors (3x3)
            assert len(sim.actors) == 9
            
            # All positions should be covered
            actor_positions = {(int(actor.x), int(actor.y)) for actor in sim.actors}
            expected_positions = {(x, y) for x in range(3) for y in range(3)}
            
            assert actor_positions == expected_positions
            
        finally:
            os.unlink(image_path)
    
    def test_invalid_image_path(self):
        """Test handling of invalid image path."""
        with pytest.raises(ValueError, match="Failed to load image"):
            PhysarumSimulation(
                width=10, height=10, num_actors=50, decay_rate=0.01,
                image_path="nonexistent_image.jpg"
            )
    
    def test_actor_random_orientation(self):
        """Test that actors created from image have random orientations."""
        # Create image with multiple black pixels
        black_pixels = [(1, 1), (2, 2), (3, 3), (4, 4)]
        image_path = self.create_test_image(6, 6, black_pixels)
        
        try:
            # Set random seed for reproducibility
            import random
            random.seed(42)
            
            sim = PhysarumSimulation(
                width=6, height=6, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # Check that actors have different orientations
            angles = [actor.angle for actor in sim.actors]
            assert len(set(angles)) > 1  # Should have different angles
            
            # All angles should be in valid range [0, 2π)
            for angle in angles:
                assert 0 <= angle < 2 * np.pi
                
        finally:
            os.unlink(image_path)
    
    def test_num_actors_ignored_with_image(self):
        """Test that num_actors parameter is ignored when image is provided."""
        black_pixels = [(2, 2), (4, 4)]
        image_path = self.create_test_image(6, 6, black_pixels)
        
        try:
            # Set num_actors to different value than black pixels
            sim = PhysarumSimulation(
                width=6, height=6, num_actors=100, decay_rate=0.01,
                image_path=image_path
            )
            
            # Should have 2 actors (from image), not 100
            assert len(sim.actors) == 2
            
        finally:
            os.unlink(image_path)
    
    def test_grid_bounds_checking(self):
        """Test that actors are properly positioned within grid bounds."""
        # Create image larger than grid to test bounds
        black_pixels = [(0, 0), (1, 1), (2, 2)]
        image_path = self.create_test_image(5, 5, black_pixels)
        
        try:
            sim = PhysarumSimulation(
                width=3, height=3, num_actors=50, decay_rate=0.01,
                image_path=image_path
            )
            
            # All actors should be within grid bounds
            for actor in sim.actors:
                assert 0 <= actor.x < 3
                assert 0 <= actor.y < 3
                
        finally:
            os.unlink(image_path)