# ABOUTME: Core Physarum simulation engine with grid-based slime mold simulation
# ABOUTME: Implements actors/agents with sensing, movement, and trail deposition mechanics

import numpy as np
from typing import Tuple, List, Optional
import random
import math
from PIL import Image


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
            
        # Create a copy of the current state
        original_map = self.trail_map.copy()
        
        # For each cell, diffuse its pheromone to neighbors
        for y in range(self.height):
            for x in range(self.width):
                if original_map[y, x] > 0:
                    # Amount to diffuse from this cell
                    to_diffuse = original_map[y, x] * diffusion_rate
                    
                    # Count valid neighbors
                    valid_neighbors = []
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue  # Skip center
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                valid_neighbors.append((nx, ny))
                    
                    if valid_neighbors:
                        # Distribute diffused amount equally among valid neighbors
                        per_neighbor = to_diffuse / len(valid_neighbors)
                        for nx, ny in valid_neighbors:
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
    
    def __init__(self, x: float, y: float, angle: float, view_radius: int, view_distance: int):
        """Initialize a Physarum actor.
        
        Args:
            x: Starting X position
            y: Starting Y position
            angle: Starting direction in radians
            view_radius: Radius of sensing area
            view_distance: Distance ahead for sensing
        """
        self.x = x
        self.y = y
        self.angle = angle
        self.view_radius = view_radius
        self.view_distance = view_distance
        self.turn_speed = 0.1  # How fast the actor can turn
        self.trail_deposit_amount = 1.0  # Amount of trail deposited per step
        self.age = 0  # Age in simulation steps
    
    def move(self, speed: float) -> None:
        """Move the actor forward based on its current angle.
        
        Args:
            speed: Movement speed
        """
        self.x += math.cos(self.angle) * speed
        self.y += math.sin(self.angle) * speed
    
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
                 direction_deviation: float = 1.57, image_path: Optional[str] = None):
        """Initialize the Physarum simulation.
        
        Args:
            width: Grid width
            height: Grid height
            num_actors: Number of actors to create (ignored if image_path is provided)
            decay_rate: Trail decay rate (0.0 to 1.0)
            view_radius: Sensor radius for actors
            view_distance: Sensor distance for actors
            speed: Movement speed for actors
            initial_diameter: Diameter of initial circular actor placement
            death_probability: Base probability of actor death per step
            spawn_probability: Probability of spawning new actors per step
            diffusion_rate: Rate of pheromone diffusion (0.0 to 1.0)
            direction_deviation: Maximum direction deviation for spawned actors in radians
            image_path: Path to JPEG image for initial actor placement (overrides num_actors)
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
        
        self.grid = PhysarumGrid(width, height)
        self.decay_rate = decay_rate
        self.diffusion_rate = diffusion_rate
        self.speed = speed
        self.death_probability = death_probability
        self.spawn_probability = spawn_probability
        self.direction_deviation = direction_deviation
        self.view_radius = view_radius
        self.view_distance = view_distance
        self.actors = []
        
        # Create actors based on image or circular pattern
        if image_path:
            self._create_actors_from_image(image_path, width, height)
        else:
            self._create_initial_actors(num_actors, initial_diameter, width, height)
    
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
            
            # Random orientation
            actor_angle = random.uniform(0, 2 * math.pi)
            actor = PhysarumActor(x, y, actor_angle, self.view_radius, self.view_distance)
            self.actors.append(actor)
        
        # If we need more actors than fit on the circle, place them randomly within the circle
        for _ in range(num_actors - actors_to_place):
            # Random position within the circle
            r = radius * math.sqrt(random.random())
            theta = random.uniform(0, 2 * math.pi)
            x = center_x + r * math.cos(theta)
            y = center_y + r * math.sin(theta)
            
            # Random orientation
            actor_angle = random.uniform(0, 2 * math.pi)
            actor = PhysarumActor(x, y, actor_angle, self.view_radius, self.view_distance)
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
                actor_y = float(y + offset_y)
                
                # Random orientation for each actor
                actor_angle = random.uniform(0, 2 * math.pi)
                actor = PhysarumActor(actor_x, actor_y, actor_angle, self.view_radius, self.view_distance)
                self.actors.append(actor)
                
        except Exception as e:
            raise ValueError(f"Failed to load image {image_path}: {e}")
    
    def step(self) -> None:
        """Perform one simulation step."""
        # Actor sensing and movement phase
        for actor in self.actors:
            # Age the actor
            actor.age_step()
            
            # Sense environment
            left, center, right = actor.sense_environment(self.grid)
            
            # Steer based on sensed values
            actor.steer(left, center, right)
            
            # Move actor
            actor.move(self.speed)
            
            # Wrap position around boundaries
            actor.wrap_position(self.grid.width, self.grid.height)
            
            # Deposit trail
            actor.deposit_trail(self.grid)
        
        # Apply lifecycle changes
        self._handle_deaths()
        self._handle_spawning()
        
        # Apply diffusion to spread trails (before decay)
        self.grid.apply_diffusion(self.diffusion_rate)
        
        # Apply decay to all trails
        self.grid.apply_decay(self.decay_rate)
    
    def _handle_deaths(self) -> None:
        """Remove actors that should die based on age and death probability."""
        self.actors = [actor for actor in self.actors if not actor.should_die(self.death_probability)]
    
    def _handle_spawning(self) -> None:
        """Spawn new actors from existing actor locations based on spawn probability."""
        if not self.actors:  # No actors to spawn from
            return
            
        new_actors = []
        for actor in self.actors:
            if random.random() < self.spawn_probability:
                # Spawn new actor near this actor
                spawn_distance = 5.0  # Distance from parent
                spawn_angle = random.uniform(0, 2 * math.pi)
                
                new_x = actor.x + spawn_distance * math.cos(spawn_angle)
                new_y = actor.y + spawn_distance * math.sin(spawn_angle)
                
                # Wrap around boundaries
                new_x = new_x % self.grid.width
                new_y = new_y % self.grid.height
                
                # Direction inheritance with triangular distribution (peak at 0, falloff to bounds)
                deviation = random.triangular(-self.direction_deviation, self.direction_deviation, 0)
                new_angle = actor.angle + deviation
                new_actor = PhysarumActor(new_x, new_y, new_angle, self.view_radius, self.view_distance)
                new_actors.append(new_actor)
        
        # Add new actors to the simulation
        self.actors.extend(new_actors)
    
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