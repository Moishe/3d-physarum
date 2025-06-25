# ABOUTME: Preview image generation for 3D Physarum models
# ABOUTME: Creates 2D visualizations from simulation data for quick model previews

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional, Tuple
import os


class PreviewGenerator:
    """Generates preview images from Physarum simulation data."""
    
    def __init__(self, width: int = 800, height: int = 800, 
                 background_color: Tuple[int, int, int] = (20, 20, 30),
                 trail_color: Tuple[int, int, int] = (255, 120, 60)):
        """Initialize the preview generator.
        
        Args:
            width: Output image width in pixels
            height: Output image height in pixels
            background_color: RGB color for the background
            trail_color: RGB color for the trails
        """
        self.output_width = width
        self.output_height = height
        self.background_color = background_color
        self.trail_color = trail_color
    
    def generate_preview(self, trail_map: np.ndarray, 
                        output_path: str,
                        threshold: float = 0.1,
                        title: Optional[str] = None) -> None:
        """Generate a preview image from trail map data.
        
        Args:
            trail_map: 2D numpy array of trail intensities
            output_path: Path to save the preview image
            threshold: Minimum trail intensity to show
            title: Optional title to add to the image
        """
        # Normalize trail map to 0-1 range
        trail_normalized = np.clip(trail_map, 0, None)
        if np.max(trail_normalized) > 0:
            trail_normalized = trail_normalized / np.max(trail_normalized)
        
        # Apply threshold
        trail_thresholded = np.where(trail_normalized > threshold, trail_normalized, 0)
        
        # Create base image
        img = Image.new('RGB', (self.output_width, self.output_height), self.background_color)
        
        # Scale trail map to output dimensions
        trail_resized = self._resize_trail_map(trail_thresholded)
        
        # Apply trail visualization
        self._apply_trail_visualization(img, trail_resized)
        
        # Add subtle enhancement
        img = self._enhance_image(img)
        
        # Add title if provided
        if title:
            img = self._add_title(img, title)
        
        # Save the image
        img.save(output_path, 'JPEG', quality=90, optimize=True)
    
    def _resize_trail_map(self, trail_map: np.ndarray) -> np.ndarray:
        """Resize trail map to match output dimensions."""
        from scipy.ndimage import zoom
        
        height, width = trail_map.shape
        scale_y = self.output_height / height
        scale_x = self.output_width / width
        
        # Use the smaller scale to maintain aspect ratio and center
        scale = min(scale_x, scale_y)
        
        # Resize with anti-aliasing
        resized = zoom(trail_map, scale, order=1)
        
        # Center the resized image
        resized_h, resized_w = resized.shape
        start_y = (self.output_height - resized_h) // 2
        start_x = (self.output_width - resized_w) // 2
        
        result = np.zeros((self.output_height, self.output_width))
        end_y = min(start_y + resized_h, self.output_height)
        end_x = min(start_x + resized_w, self.output_width)
        result[start_y:end_y, start_x:end_x] = resized[:end_y-start_y, :end_x-start_x]
        
        return result
    
    def _apply_trail_visualization(self, img: Image.Image, trail_map: np.ndarray) -> None:
        """Apply trail visualization to the image."""
        # Convert to numpy array for processing
        img_array = np.array(img)
        
        # Create color mapping
        for y in range(trail_map.shape[0]):
            for x in range(trail_map.shape[1]):
                intensity = trail_map[y, x]
                if intensity > 0:
                    # Blend trail color with background based on intensity
                    alpha = intensity ** 0.7  # Gamma correction for better visibility
                    
                    # Calculate blended color
                    bg_r, bg_g, bg_b = self.background_color
                    trail_r, trail_g, trail_b = self.trail_color
                    
                    blended_r = int(bg_r * (1 - alpha) + trail_r * alpha)
                    blended_g = int(bg_g * (1 - alpha) + trail_g * alpha)
                    blended_b = int(bg_b * (1 - alpha) + trail_b * alpha)
                    
                    img_array[y, x] = [blended_r, blended_g, blended_b]
        
        # Convert back to PIL Image
        enhanced_img = Image.fromarray(img_array.astype(np.uint8))
        img.paste(enhanced_img)
    
    def _enhance_image(self, img: Image.Image) -> Image.Image:
        """Apply subtle enhancement to improve visual appeal."""
        # Apply slight gaussian blur for anti-aliasing
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Slight sharpening to counteract blur
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=10, threshold=2))
        
        return img
    
    def _add_title(self, img: Image.Image, title: str) -> Image.Image:
        """Add a title to the image."""
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except (OSError, IOError):
                font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position text at top center with padding
        x = (self.output_width - text_width) // 2
        y = 20
        
        # Draw text with outline for better visibility
        outline_color = (0, 0, 0)
        text_color = (255, 255, 255)
        
        # Draw outline
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), title, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((x, y), title, font=font, fill=text_color)
        
        return img
    
    def generate_preview_from_simulation(self, simulation, output_path: str, 
                                       threshold: float = 0.1,
                                       title: Optional[str] = None) -> None:
        """Generate preview directly from a Physarum simulation.
        
        Args:
            simulation: PhysarumSimulation instance
            output_path: Path to save the preview image
            threshold: Minimum trail intensity to show
            title: Optional title to add to the image
        """
        trail_map = simulation.get_trail_map()
        self.generate_preview(trail_map, output_path, threshold, title)