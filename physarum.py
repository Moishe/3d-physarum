# ABOUTME: Core Physarum simulation engine with grid-based slime mold simulation
# ABOUTME: Implements actors/agents with sensing, movement, and trail deposition mechanics

import numpy as np
from typing import Tuple, List, Optional
import random
import math
from PIL import Image
from scipy.ndimage import convolve


class PhysarumGrid:
    """Grid-based environment for Physarum simulation with trail mechanics."""
    
    def __init__(self, width: int, height: int):
        """Initialize the simulation grid.
        
        Args:
            width: Grid width in pixels
            height: Grid height in pixels
        """
        self.width = width
        self.height = height
        self.trail_map = np.zeros((height, width), dtype=np.float32)
    
    def deposit_trail(self, x: int, y: int, amount: float) -> None:
        """Deposit trail substance at the given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            amount: Amount of trail to deposit
        """
        # Check bounds
        if 0 <= x < self.width and 0 <= y < self.height:
            self.trail_map[y, x] += amount
    
    def apply_decay(self, decay_rate: float) -> None:
        """Apply decay to all trail values on the grid.
        
        Args:
            decay_rate: Rate of decay (0.0 to 1.0)
        """
        self.trail_map *= (1.0 - decay_rate)
    
    def apply_diffusion(self, diffusion_rate: float) -> None:
        """Apply pheromone diffusion to spread trails to neighboring cells.
        
        Diffusion decreases trail intensity but increases their radius.
        Total pheromone is conserved during the diffusion process.
        
        Args:
            diffusion_rate: Rate of diffusion (0.0 to 1.0)
        """
        if diffusion_rate <= 0.0:
            return
            
        # Use the original algorithm but with numpy operations for better performance
        original_map = self.trail_map.copy()
        
        # Create index arrays for vectorized neighbor processing
        y_indices, x_indices = np.nonzero(original_map > 0)
        
        if len(y_indices) == 0:
            return
            
        # For each cell with pheromone, calculate diffusion
        for i in range(len(y_indices)):
            y, x = y_indices[i], x_indices[i]
            if original_map[y, x] > 0:
                # Amount to diffuse from this cell
                to_diffuse = original_map[y, x] * diffusion_rate
                
                # Find valid neighbors
                neighbors = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue  # Skip center
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            neighbors.append((ny, nx))
                
                if neighbors:
                    # Distribute diffused amount equally among valid neighbors
                    per_neighbor = to_diffuse / len(neighbors)
                    for ny, nx in neighbors:
                        self.trail_map[ny, nx] += per_neighbor
                
                # Remove diffused amount from original cell
                self.trail_map[y, x] -= to_diffuse
    
    def get_trail_strength(self, x: int, y: int) -> float:
        """Get trail strength at the given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Trail strength at the position (0.0 if out of bounds)
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.trail_map[y, x]
        return 0.0


class PhysarumActor:
    """Individual Physarum agent that moves, senses, and deposits trails."""
    
    def __init__(self, x: float, y: float, angle: float, view_radius: int, view_distance: int, speed: float = 1.0):
        """Initialize a Physarum actor.
        
        Args:
            x: Starting X position
            y: Starting Y position
            angle: Starting direction in radians
            view_radius: Radius of sensing area
            view_distance: Distance ahead for sensing
            speed: Individual movement speed for this actor
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.view_radius = view_radius
        self.view_distance = view_distance
        self.speed = speed  # Individual speed for this actor
        self.turn_speed = 0.1  # How fast the actor can turn
        self.trail_deposit_amount = 1.0  # Amount of trail deposited per step
        self.age = 0  # Age in simulation steps
    
    def move(self, speed: float = None) -> None:
        """Move the actor forward based on its current angle.
        
        Args:
            speed: Movement speed (uses actor's individual speed if None)
        """
        actual_speed = speed if speed is not None else self.speed
        self.x += math.cos(self.angle) * actual_speed
        self.y += math.sin(self.angle) * actual_speed
    
    def sense_environment(self, grid: PhysarumGrid) -> Tuple[float, float, float]:
        """Sense trail strength in three directions: left, center, right.
        
        Args:
            grid: The simulation grid to sense
            
        Returns:
            Tuple of (left_sense, center_sense, right_sense) values
        """
        sensor_angle_offset = 0.4  # Angle offset for left/right sensors
        
        # Calculate sensor positions
        center_x = self.x + math.cos(self.angle) * self.view_distance
        center_y = self.y + math.sin(self.angle) * self.view_distance
        
        left_angle = self.angle - sensor_angle_offset
        left_x = self.x + math.cos(left_angle) * self.view_distance
        left_y = self.y + math.sin(left_angle) * self.view_distance
        
        right_angle = self.angle + sensor_angle_offset
        right_x = self.x + math.cos(right_angle) * self.view_distance
        right_y = self.y + math.sin(right_angle) * self.view_distance
        
        # Sample trail strength in circular areas around each sensor
        left_sense = self._sample_circular_area(grid, left_x, left_y)
        center_sense = self._sample_circular_area(grid, center_x, center_y)
        right_sense = self._sample_circular_area(grid, right_x, right_y)
        
        return left_sense, center_sense, right_sense
    
    def _sample_circular_area(self, grid: PhysarumGrid, center_x: float, center_y: float) -> float:
        """Sample trail strength in a circular area around a point.
        
        Args:
            grid: The simulation grid
            center_x: Center X coordinate
            center_y: Center Y coordinate
            
        Returns:
            Average trail strength in the circular area
        """
        total_strength = 0.0
        sample_count = 0
        
        # Sample points in a circle
        for dx in range(-self.view_radius, self.view_radius + 1):
            for dy in range(-self.view_radius, self.view_radius + 1):
                if dx * dx + dy * dy <= self.view_radius * self.view_radius:
                    sample_x = int(center_x + dx)
                    sample_y = int(center_y + dy)
                    total_strength += grid.get_trail_strength(sample_x, sample_y)
                    sample_count += 1
        
        return total_strength / max(sample_count, 1)
    
    def steer(self, left_sense: float, center_sense: float, right_sense: float) -> None:
        """Update the actor's direction based on sensor inputs.
        
        Args:
            left_sense: Strength sensed on the left
            center_sense: Strength sensed in the center
            right_sense: Strength sensed on the right
        """
        # Simple steering logic: turn towards stronger signal
        if center_sense >= left_sense and center_sense >= right_sense:
            # Continue straight (small random variation)
            self.angle += (random.random() - 0.5) * 0.1
        elif left_sense > right_sense:
            # Turn left
            self.angle -= self.turn_speed
        else:
            # Turn right
            self.angle += self.turn_speed
        
        # Keep angle in valid range
        self.angle = self.angle % (2 * math.pi)
    
    def wrap_position(self, grid_width: int, grid_height: int) -> None:
        """Wrap actor position around grid boundaries.
        
        Args:
            grid_width: Width of the simulation grid
            grid_height: Height of the simulation grid
        """
        self.x = self.x % grid_width
        self.y = self.y % grid_height
    
    def deposit_trail(self, grid: PhysarumGrid) -> None:
        """Deposit trail at the actor's current position.
        
        Args:
            grid: The simulation grid
        """
        grid.deposit_trail(int(self.x), int(self.y), self.trail_deposit_amount)
    
    def age_step(self) -> None:
        """Increment the actor's age by one step."""
        self.age += 1
    
    def should_die(self, death_probability: float) -> bool:
        """Determine if actor should die based on age and death probability.
        
        Args:
            death_probability: Base death probability per step
            
        Returns:
            True if the actor should die
        """
        # Age-based death probability: older actors have higher chance of death
        age_factor = 1.0 + (self.age * 0.001)  # Gradual increase with age
        effective_death_prob = death_probability * age_factor
        return random.random() < effective_death_prob


class PhysarumSimulation:
    """Main simulation engine that orchestrates grid and actors."""
    
    def __init__(self, width: int, height: int, num_actors: int, decay_rate: float, 
                 view_radius: int = 3, view_distance: int = 10, speed: float = 1.0,
                 initial_diameter: float = 20.0, death_probability: float = 0.001,
                 spawn_probability: float = 0.005, diffusion_rate: float = 0.0,
                 direction_deviation: float = 1.57, image_path: Optional[str] = None,
                 speed_min: float = None, speed_max: float = None, 
                 spawn_speed_randomization: float = 0.2):
        """Initialize the Physarum simulation.
        
        Args:
            width: Grid width
            height: Grid height
            num_actors: Number of actors to create (ignored if image_path is provided)
            decay_rate: Trail decay rate (0.0 to 1.0)
            view_radius: Sensor radius for actors
            view_distance: Sensor distance for actors
            speed: Movement speed for actors (used as base or when min/max not specified)
            initial_diameter: Diameter of initial circular actor placement
            death_probability: Base probability of actor death per step
            spawn_probability: Probability of spawning new actors per step
            diffusion_rate: Rate of pheromone diffusion (0.0 to 1.0)
            direction_deviation: Maximum direction deviation for spawned actors in radians
            image_path: Path to JPEG image for initial actor placement (overrides num_actors)
            speed_min: Minimum speed for initial actors (defaults to speed if None)
            speed_max: Maximum speed for initial actors (defaults to speed if None)
            spawn_speed_randomization: Factor for randomizing spawned actor speeds (0.0 to 1.0)
        """
        # Validate parameters
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
        if image_path is None and num_actors <= 0:
            raise ValueError("Number of actors must be positive when no image is provided")
        if decay_rate < 0 or decay_rate > 1:
            raise ValueError("Decay rate must be between 0 and 1")
        if diffusion_rate < 0 or diffusion_rate > 1:
            raise ValueError("Diffusion rate must be between 0 and 1")
        if direction_deviation < 0 or direction_deviation > 3.14159:
            raise ValueError("Direction deviation must be between 0 and π radians")
        
        # Set speed defaults and validate
        self.speed_min = speed_min if speed_min is not None else speed
        self.speed_max = speed_max if speed_max is not None else speed
        if self.speed_min > self.speed_max:
            raise ValueError("speed_min must be less than or equal to speed_max")
        if self.speed_min <= 0 or self.speed_max <= 0:
            raise ValueError("Speed values must be positive")
        if spawn_speed_randomization < 0 or spawn_speed_randomization > 1:
            raise ValueError("spawn_speed_randomization must be between 0 and 1")
        
        self.grid = PhysarumGrid(width, height)
        self.decay_rate = decay_rate
        self.diffusion_rate = diffusion_rate
        self.speed = speed
        self.spawn_speed_randomization = spawn_speed_randomization
        self.death_probability = death_probability
        self.spawn_probability = spawn_probability
        self.direction_deviation = direction_deviation
        self.view_radius = view_radius
        self.view_distance = view_distance
        self.actors = []
        
        # Vectorized actor properties
        self.actor_positions = None  # Shape: (N, 2) - x, y coordinates
        self.actor_angles = None     # Shape: (N,) - angle in radians
        self.actor_ages = None       # Shape: (N,) - age in steps
        self.actor_speeds = None     # Shape: (N,) - individual actor speeds
        self.num_actors = 0
        
        # Create sampling kernels for sensing
        self._create_sensing_kernels()
        
        # Create actors based on image or circular pattern
        if image_path:
            self._create_actors_from_image(image_path, width, height)
        else:
            self._create_initial_actors(num_actors, initial_diameter, width, height)
        
        # Convert actors to vectorized format
        self._vectorize_actors()
    
    def _create_sensing_kernels(self) -> None:
        """Create pre-computed kernels for circular sampling."""
        # Create circular mask for sensing
        size = 2 * self.view_radius + 1
        center = self.view_radius
        y, x = np.ogrid[:size, :size]
        mask = (x - center)**2 + (y - center)**2 <= self.view_radius**2
        
        # Store as normalized kernel
        self.sensing_kernel = mask.astype(np.float32)
        kernel_sum = np.sum(self.sensing_kernel)
        if kernel_sum > 0:
            self.sensing_kernel /= kernel_sum
    
    def _generate_random_speed(self) -> float:
        """Generate a random speed between speed_min and speed_max."""
        return random.uniform(self.speed_min, self.speed_max)
    
    def _vectorize_actors(self) -> None:
        """Convert individual actors to vectorized numpy arrays."""
        if not self.actors:
            self.num_actors = 0
            self.actor_positions = np.empty((0, 2), dtype=np.float32)
            self.actor_angles = np.empty(0, dtype=np.float32)
            self.actor_ages = np.empty(0, dtype=np.int32)
            self.actor_speeds = np.empty(0, dtype=np.float32)
            return
            
        self.num_actors = len(self.actors)
        self.actor_positions = np.array([[actor.x, actor.y] for actor in self.actors], dtype=np.float32)
        self.actor_angles = np.array([actor.angle for actor in self.actors], dtype=np.float32)
        self.actor_ages = np.array([actor.age for actor in self.actors], dtype=np.int32)
        self.actor_speeds = np.array([actor.speed for actor in self.actors], dtype=np.float32)
    
    def _sync_actors_from_arrays(self) -> None:
        """Sync individual actor objects from vectorized arrays for backward compatibility."""
        # Update existing actors from vectorized data
        for i, actor in enumerate(self.actors):
            if i < len(self.actor_positions):
                actor.x = float(self.actor_positions[i, 0])
                actor.y = float(self.actor_positions[i, 1])
                actor.angle = float(self.actor_angles[i])
                actor.age = int(self.actor_ages[i])
                actor.speed = float(self.actor_speeds[i])
        
        # Handle case where vectorized arrays have more actors (from spawning)
        while len(self.actors) < self.num_actors:
            idx = len(self.actors)
            new_actor = PhysarumActor(
                float(self.actor_positions[idx, 0]),
                float(self.actor_positions[idx, 1]),
                float(self.actor_angles[idx]),
                self.view_radius,
                self.view_distance,
                float(self.actor_speeds[idx])
            )
            new_actor.age = int(self.actor_ages[idx])
            self.actors.append(new_actor)
        
        # Handle case where vectorized arrays have fewer actors (from deaths)
        while len(self.actors) > self.num_actors:
            self.actors.pop()
    
    def _create_initial_actors(self, num_actors: int, diameter: float, width: int, height: int) -> None:
        """Create initial actors arranged in a circle.
        
        Args:
            num_actors: Number of actors to create
            diameter: Diameter of the circle for placement
            width: Grid width
            height: Grid height
        """
        center_x = width / 2.0
        center_y = height / 2.0
        radius = diameter / 2.0
        
        # Calculate how many actors can fit around the circle
        actors_to_place = min(num_actors, max(1, int(math.pi * diameter)))
        
        for i in range(actors_to_place):
            # Place actors around the circle
            angle = (2 * math.pi * i) / actors_to_place
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # Random orientation and speed
            actor_angle = random.uniform(0, 2 * math.pi)
            actor_speed = self._generate_random_speed()
            actor = PhysarumActor(x, y, actor_angle, self.view_radius, self.view_distance, actor_speed)
            self.actors.append(actor)
        
        # If we need more actors than fit on the circle, place them randomly within the circle
        for _ in range(num_actors - actors_to_place):
            # Random position within the circle
            r = radius * math.sqrt(random.random())
            theta = random.uniform(0, 2 * math.pi)
            x = center_x + r * math.cos(theta)
            y = center_y + r * math.sin(theta)
            
            # Random orientation and speed
            actor_angle = random.uniform(0, 2 * math.pi)
            actor_speed = self._generate_random_speed()
            actor = PhysarumActor(x, y, actor_angle, self.view_radius, self.view_distance, actor_speed)
            self.actors.append(actor)
    
    def _create_actors_from_image(self, image_path: str, width: int, height: int) -> None:
        """Create actors from black pixels in an image.
        
        Args:
            image_path: Path to the image file (JPEG, PNG, etc.)
            width: Target grid width
            height: Target grid height
        """
        try:
            # Load and convert image to RGB
            image = Image.open(image_path).convert('RGB')
            img_array = np.array(image)
            
            # Get image dimensions
            img_height, img_width = img_array.shape[:2]
            
            # Calculate the region to use based on width/height constraints
            if width < img_width or height < img_height:
                # Use center crop if target is smaller than image
                start_x = max(0, (img_width - width) // 2)
                start_y = max(0, (img_height - height) // 2)
                end_x = min(img_width, start_x + width)
                end_y = min(img_height, start_y + height)
                
                # Extract the center region
                cropped_img = img_array[start_y:end_y, start_x:end_x]
            else:
                # Image is smaller than target, will be centered in grid
                cropped_img = img_array
            
            # Calculate offset for centering smaller images in larger grids
            offset_x = max(0, (width - cropped_img.shape[1]) // 2)
            offset_y = max(0, (height - cropped_img.shape[0]) // 2)
            
            # Find black pixels (RGB values all < 16)
            black_pixels = np.all(cropped_img < 16, axis=2)
            
            # Create actors for each black pixel
            y_coords, x_coords = np.where(black_pixels)
            
            for y, x in zip(y_coords, x_coords):
                # Apply offset to center the image in the grid
                actor_x = float(x + offset_x)
                # Flip Y-coordinate to convert from image space (top-left origin) to simulation space (bottom-left origin)
                actor_y = float((cropped_img.shape[0] - 1 - y) + offset_y)
                
                # Random orientation and speed for each actor
                actor_angle = random.uniform(0, 2 * math.pi)
                actor_speed = self._generate_random_speed()
                actor = PhysarumActor(actor_x, actor_y, actor_angle, self.view_radius, self.view_distance, actor_speed)
                self.actors.append(actor)
                
        except Exception as e:
            raise ValueError(f"Failed to load image {image_path}: {e}")
    
    def step(self) -> None:
        """Perform one simulation step."""
        if self.num_actors == 0:
            return
            
        # Age all actors
        self.actor_ages += 1
        
        # Vectorized sensing and movement
        self._sense_and_steer()
        self._move_actors()
        self._wrap_positions()
        self._deposit_trails()
        
        # Apply lifecycle changes
        self._handle_deaths()
        self._handle_spawning()
        
        # Apply diffusion to spread trails (before decay)
        self.grid.apply_diffusion(self.diffusion_rate)
        
        # Apply decay to all trails
        self.grid.apply_decay(self.decay_rate)
        
        # Sync individual actors from vectorized arrays for backward compatibility
        self._sync_actors_from_arrays()
    
    def _sense_and_steer(self) -> None:
        """Vectorized sensing and steering for all actors."""
        if self.num_actors == 0:
            return
            
        sensor_angle_offset = 0.4  # Angle offset for left/right sensors
        
        # Calculate all sensor positions
        center_x = self.actor_positions[:, 0] + np.cos(self.actor_angles) * self.view_distance
        center_y = self.actor_positions[:, 1] + np.sin(self.actor_angles) * self.view_distance
        
        left_angles = self.actor_angles - sensor_angle_offset
        left_x = self.actor_positions[:, 0] + np.cos(left_angles) * self.view_distance
        left_y = self.actor_positions[:, 1] + np.sin(left_angles) * self.view_distance
        
        right_angles = self.actor_angles + sensor_angle_offset
        right_x = self.actor_positions[:, 0] + np.cos(right_angles) * self.view_distance
        right_y = self.actor_positions[:, 1] + np.sin(right_angles) * self.view_distance
        
        # Sample trail strength at sensor positions
        left_sense = self._sample_trail_strength_vectorized(left_x, left_y)
        center_sense = self._sample_trail_strength_vectorized(center_x, center_y)
        right_sense = self._sample_trail_strength_vectorized(right_x, right_y)
        
        # Vectorized steering logic
        turn_speed = 0.1
        
        # Continue straight if center is strongest
        straight_mask = (center_sense >= left_sense) & (center_sense >= right_sense)
        # Add small random variation
        self.actor_angles[straight_mask] += (np.random.random(np.sum(straight_mask)) - 0.5) * 0.1
        
        # Turn left if left sensor is strongest
        left_mask = (left_sense > center_sense) & (left_sense > right_sense)
        self.actor_angles[left_mask] -= turn_speed
        
        # Turn right if right sensor is strongest  
        right_mask = (right_sense > center_sense) & (right_sense > left_sense)
        self.actor_angles[right_mask] += turn_speed
    
    def _sample_trail_strength_vectorized(self, x_coords: np.ndarray, y_coords: np.ndarray) -> np.ndarray:
        """Sample trail strength at multiple positions using vectorized operations."""
        # Convert to integer coordinates
        x_int = np.clip(np.round(x_coords).astype(int), 0, self.grid.width - 1)
        y_int = np.clip(np.round(y_coords).astype(int), 0, self.grid.height - 1)
        
        # For simplicity, sample at single points instead of circular areas
        # This is a performance optimization that trades some accuracy for speed
        return self.grid.trail_map[y_int, x_int]
    
    def _move_actors(self) -> None:
        """Move all actors forward based on their angles."""
        if self.num_actors == 0:
            return
            
        # Vectorized movement using individual speeds
        self.actor_positions[:, 0] += np.cos(self.actor_angles) * self.actor_speeds
        self.actor_positions[:, 1] += np.sin(self.actor_angles) * self.actor_speeds
    
    def _wrap_positions(self) -> None:
        """Wrap actor positions around grid boundaries."""
        if self.num_actors == 0:
            return
            
        # Wrap X coordinates
        self.actor_positions[:, 0] = np.mod(self.actor_positions[:, 0], self.grid.width)
        # Wrap Y coordinates
        self.actor_positions[:, 1] = np.mod(self.actor_positions[:, 1], self.grid.height)
    
    def _deposit_trails(self) -> None:
        """Deposit trails at all actor positions."""
        if self.num_actors == 0:
            return
            
        # Convert positions to integer coordinates
        x_int = np.clip(np.round(self.actor_positions[:, 0]).astype(int), 0, self.grid.width - 1)
        y_int = np.clip(np.round(self.actor_positions[:, 1]).astype(int), 0, self.grid.height - 1)
        
        # Deposit trails (using numpy's add.at for accumulation)
        trail_amount = 1.0
        np.add.at(self.grid.trail_map, (y_int, x_int), trail_amount)
    
    def _handle_deaths(self) -> None:
        """Remove actors that should die based on age and death probability."""
        if self.num_actors == 0:
            return
            
        # Use the original death probability calculation with age factor
        death_rolls = np.random.random(self.num_actors)
        
        # Age-based death probability: older actors have higher chance of death
        age_factors = 1.0 + (self.actor_ages * 0.001)  # Gradual increase with age
        effective_death_probs = self.death_probability * age_factors
        
        # Keep actors that don't die
        survival_mask = death_rolls >= effective_death_probs
        
        if np.any(survival_mask):
            self.actor_positions = self.actor_positions[survival_mask]
            self.actor_angles = self.actor_angles[survival_mask]
            self.actor_ages = self.actor_ages[survival_mask]
            self.actor_speeds = self.actor_speeds[survival_mask]
            self.num_actors = np.sum(survival_mask)
        else:
            # All actors died
            self.num_actors = 0
            self.actor_positions = np.empty((0, 2), dtype=np.float32)
            self.actor_angles = np.empty(0, dtype=np.float32)
            self.actor_ages = np.empty(0, dtype=np.int32)
            self.actor_speeds = np.empty(0, dtype=np.float32)
        
        # Sync individual actors from vectorized arrays
        self._sync_actors_from_arrays()
    
    def _handle_spawning(self) -> None:
        """Spawn new actors from existing actor locations based on spawn probability."""
        if self.num_actors == 0:
            return
        
        # First, sync vectorized arrays from individual actors 
        # (in case they were modified outside of step())
        if len(self.actors) > 0:
            self._vectorize_actors()
            
        # Determine which actors spawn
        spawn_rolls = np.random.random(self.num_actors)
        spawn_mask = spawn_rolls < self.spawn_probability
        num_spawns = np.sum(spawn_mask)
        
        if num_spawns == 0:
            return
            
        # Get parent positions, angles, and speeds
        parent_positions = self.actor_positions[spawn_mask]
        parent_angles = self.actor_angles[spawn_mask]
        parent_speeds = self.actor_speeds[spawn_mask]
        
        # Generate spawn positions
        spawn_distance = 5.0
        spawn_angles = np.random.uniform(0, 2 * np.pi, num_spawns)
        
        new_x = parent_positions[:, 0] + spawn_distance * np.cos(spawn_angles)
        new_y = parent_positions[:, 1] + spawn_distance * np.sin(spawn_angles)
        
        # Wrap around boundaries
        new_x = np.mod(new_x, self.grid.width)
        new_y = np.mod(new_y, self.grid.height)
        
        # Direction inheritance with triangular distribution
        if self.direction_deviation > 0:
            deviations = np.random.triangular(-self.direction_deviation, 0, self.direction_deviation, num_spawns)
        else:
            deviations = np.zeros(num_spawns)
        new_angles = parent_angles + deviations
        
        # Speed inheritance with randomization
        if self.spawn_speed_randomization > 0:
            # Apply randomization as a percentage of parent speed
            speed_variations = np.random.uniform(
                -self.spawn_speed_randomization, 
                self.spawn_speed_randomization, 
                num_spawns
            )
            new_speeds = parent_speeds * (1.0 + speed_variations)
            # Ensure speeds stay positive
            new_speeds = np.maximum(new_speeds, 0.1)
        else:
            # No randomization, inherit parent speed exactly
            new_speeds = parent_speeds.copy()
        
        # Add new actors to arrays
        if num_spawns > 0:
            new_positions = np.column_stack([new_x, new_y])
            new_ages = np.zeros(num_spawns, dtype=np.int32)
            
            self.actor_positions = np.vstack([self.actor_positions, new_positions])
            self.actor_angles = np.concatenate([self.actor_angles, new_angles])
            self.actor_ages = np.concatenate([self.actor_ages, new_ages])
            self.actor_speeds = np.concatenate([self.actor_speeds, new_speeds])
            self.num_actors += num_spawns
            
            # Sync individual actors from vectorized arrays
            self._sync_actors_from_arrays()
    
    def run(self, steps: int) -> None:
        """Run the simulation for a specified number of steps.
        
        Args:
            steps: Number of simulation steps to run
        """
        for _ in range(steps):
            self.step()
    
    def get_trail_map(self) -> np.ndarray:
        """Get the current trail map.
        
        Returns:
            Copy of the current trail map
        """
        return self.grid.trail_map.copy()
    
    def get_actor_count(self) -> int:
        """Get the current number of active actors.
        
        Returns:
            Number of active actors
        """
        return len(self.actors)