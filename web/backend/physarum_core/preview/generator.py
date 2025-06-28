# ABOUTME: Preview image generation for 3D Physarum models
# ABOUTME: Creates 2D visualizations from simulation data for quick model previews

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional, Tuple, List
import os
import math


class PreviewGenerator:
    """Generates preview images from Physarum simulation data."""
    
    def __init__(self, width: int = 800, height: int = 800, 
                 background_color: Tuple[int, int, int] = (30, 30, 30),
                 trail_color: Tuple[int, int, int] = (220, 220, 220)):
        """Initialize the preview generator.
        
        Args:
            width: Output image width in pixels
            height: Output image height in pixels
            background_color: RGB color for the background (dark gray)
            trail_color: RGB color for the trails (light gray)
        """
        self.output_width = width
        self.output_height = height
        self.background_color = background_color
        self.trail_color = trail_color
        
        # 3D visualization parameters
        self.iso_angle = math.radians(30)  # Isometric angle for 3D effect
        self.depth_scale = 0.5  # Depth scaling factor for 3D layers
    
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
    
    def generate_3d_preview_from_generator(self, model_generator, output_path: str,
                                         threshold: float = 0.1,
                                         title: Optional[str] = None) -> None:
        """Generate a 3D-looking preview from a 3D model generator's layer data.
        
        Args:
            model_generator: Model3DGenerator or SmoothModel3DGenerator instance
            output_path: Path to save the preview image
            threshold: Minimum trail intensity to show
            title: Optional title to add to the image
        """
        if not hasattr(model_generator, 'layers') or not model_generator.layers:
            # Fallback to 2D preview if no layer data available
            trail_map = model_generator.simulation.get_trail_map()
            self.generate_preview(trail_map, output_path, threshold, title)
            return
        
        # Generate 3D isometric preview from layer stack
        self._generate_3d_isometric_preview(model_generator.layers, output_path, 
                                          getattr(model_generator, 'layer_height', 1.0),
                                          threshold, title)
    
    def _generate_3d_isometric_preview(self, layers: List[np.ndarray], output_path: str,
                                     layer_height: float, threshold: float = 0.1,
                                     title: Optional[str] = None) -> None:
        """Generate a 3D isometric preview from layer stack data.
        
        Args:
            layers: List of 2D boolean arrays representing each layer
            output_path: Path to save the preview image
            layer_height: Height of each layer in the 3D model
            threshold: Minimum trail intensity to show (unused for boolean layers)
            title: Optional title to add to the image
        """
        if not layers:
            return
        
        # Create base image with larger canvas for 3D projection
        img = Image.new('RGB', (self.output_width, self.output_height), self.background_color)
        
        # Calculate 3D projection parameters
        layer_count = len(layers)
        
        # Process layers from bottom to top for proper depth ordering
        for layer_idx, layer_mask in enumerate(layers):
            if not np.any(layer_mask):
                continue  # Skip empty layers
            
            # Calculate depth-based color intensity (darker for deeper layers)
            depth_ratio = layer_idx / max(1, layer_count - 1)  # 0 (bottom) to 1 (top)
            intensity = 0.3 + 0.7 * depth_ratio  # Range from 30% to 100% intensity
            
            # Calculate layer color with depth shading
            layer_r = int(self.background_color[0] + (self.trail_color[0] - self.background_color[0]) * intensity)
            layer_g = int(self.background_color[1] + (self.trail_color[1] - self.background_color[1]) * intensity)
            layer_b = int(self.background_color[2] + (self.trail_color[2] - self.background_color[2]) * intensity)
            layer_color = (layer_r, layer_g, layer_b)
            
            # Apply 3D isometric transformation to this layer
            self._render_3d_layer(img, layer_mask, layer_idx, layer_count, layer_color)
        
        # Apply enhancement
        img = self._enhance_image(img)
        
        # Add title if provided
        if title:
            img = self._add_title(img, title)
        
        # Save the image
        img.save(output_path, 'JPEG', quality=90, optimize=True)
    
    def _render_3d_layer(self, img: Image.Image, layer_mask: np.ndarray, 
                        layer_idx: int, total_layers: int, layer_color: Tuple[int, int, int]) -> None:
        """Render a single layer with 3D isometric projection.
        
        Args:
            img: PIL Image to draw on
            layer_mask: 2D boolean array for this layer
            layer_idx: Index of this layer (0 = bottom)
            total_layers: Total number of layers
            layer_color: RGB color for this layer
        """
        img_array = np.array(img)
        height, width = layer_mask.shape
        
        # Calculate 3D offset for this layer (isometric projection)
        # Higher layers are offset up and to the right
        depth_progress = layer_idx / max(1, total_layers - 1)
        x_offset = int(depth_progress * 40)  # Horizontal offset for depth
        y_offset = int(depth_progress * 20)  # Vertical offset for depth
        
        # Scale layer to fit in output image with room for 3D offsets
        scale_x = (self.output_width - 60) / width   # Leave room for 3D offsets
        scale_y = (self.output_height - 60) / height
        scale = min(scale_x, scale_y) * 0.8  # Additional margin for better appearance
        
        # Center the scaled layer
        start_x = int((self.output_width - width * scale) / 2) + x_offset
        start_y = int((self.output_height - height * scale) / 2) - y_offset
        
        # Render each solid voxel in this layer
        for y in range(height):
            for x in range(width):
                if layer_mask[y, x]:
                    # Calculate screen position
                    screen_x = int(start_x + x * scale)
                    screen_y = int(start_y + y * scale)
                    
                    # Draw a small rectangle for each voxel with proper bounds checking
                    voxel_size = max(1, int(scale))
                    self._draw_voxel_rect(img_array, screen_x, screen_y, voxel_size, layer_color)
        
        # Update the image
        updated_img = Image.fromarray(img_array.astype(np.uint8))
        img.paste(updated_img)
    
    def _draw_voxel_rect(self, img_array: np.ndarray, x: int, y: int, 
                        size: int, color: Tuple[int, int, int]) -> None:
        """Draw a small rectangle representing a voxel.
        
        Args:
            img_array: Numpy array of the image
            x, y: Top-left position of the rectangle
            size: Size of the rectangle
            color: RGB color tuple
        """
        height, width = img_array.shape[:2]
        
        # Ensure coordinates are within bounds
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(width, x + size)
        y2 = min(height, y + size)
        
        if x1 < x2 and y1 < y2:
            img_array[y1:y2, x1:x2] = color