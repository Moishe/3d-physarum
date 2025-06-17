# ABOUTME: Core Physarum simulation engine with grid-based slime mold simulation
# ABOUTME: Implements actors/agents with sensing, movement, and trail deposition mechanics

import numpy as np
from typing import Tuple, List
import random
import math


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


class PhysarumSimulation:
    """Main simulation engine that orchestrates grid and actors."""
    
    def __init__(self, width: int, height: int, num_actors: int, decay_rate: float, 
                 view_radius: int = 3, view_distance: int = 10, speed: float = 1.0):
        """Initialize the Physarum simulation.
        
        Args:
            width: Grid width
            height: Grid height
            num_actors: Number of actors to create
            decay_rate: Trail decay rate (0.0 to 1.0)
            view_radius: Sensor radius for actors
            view_distance: Sensor distance for actors
            speed: Movement speed for actors
        """
        # Validate parameters
        if width <= 0 or height <= 0:
            raise ValueError("Grid dimensions must be positive")
        if num_actors <= 0:
            raise ValueError("Number of actors must be positive")
        if decay_rate < 0 or decay_rate > 1:
            raise ValueError("Decay rate must be between 0 and 1")
        
        self.grid = PhysarumGrid(width, height)
        self.decay_rate = decay_rate
        self.speed = speed
        self.actors = []
        
        # Create actors with random positions and orientations
        for _ in range(num_actors):
            x = random.uniform(width * 0.2, width * 0.8)  # Start in central area
            y = random.uniform(height * 0.2, height * 0.8)
            angle = random.uniform(0, 2 * math.pi)
            actor = PhysarumActor(x, y, angle, view_radius, view_distance)
            self.actors.append(actor)
    
    def step(self) -> None:
        """Perform one simulation step."""
        # Actor sensing and movement phase
        for actor in self.actors:
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
        
        # Apply decay to all trails
        self.grid.apply_decay(self.decay_rate)
    
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