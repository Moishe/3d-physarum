# ABOUTME: Unit tests for the Physarum simulation engine components
# ABOUTME: Tests cover grid mechanics, actor behavior, and simulation parameters

import pytest
import numpy as np
from physarum import PhysarumGrid, PhysarumActor, PhysarumSimulation


class TestPhysarumGrid:
    """Test cases for the PhysarumGrid class."""
    
    def test_grid_initialization(self):
        """Test that grid initializes with correct dimensions and empty values."""
        width, height = 100, 100
        grid = PhysarumGrid(width, height)
        
        assert grid.width == width
        assert grid.height == height
        assert grid.trail_map.shape == (height, width)
        assert np.all(grid.trail_map == 0)
    
    def test_grid_deposit_trail(self):
        """Test depositing trail substance at a specific position."""
        grid = PhysarumGrid(10, 10)
        x, y = 5, 5
        amount = 1.0
        
        grid.deposit_trail(x, y, amount)
        
        assert grid.trail_map[y, x] == amount
    
    def test_grid_decay(self):
        """Test trail decay mechanics."""
        grid = PhysarumGrid(10, 10)
        decay_rate = 0.1
        
        # Deposit some trail
        grid.deposit_trail(5, 5, 1.0)
        initial_value = grid.trail_map[5, 5]
        
        # Apply decay
        grid.apply_decay(decay_rate)
        
        expected_value = initial_value * (1 - decay_rate)
        assert np.isclose(grid.trail_map[5, 5], expected_value)
    
    def test_grid_bounds_checking(self):
        """Test that grid properly handles out-of-bounds coordinates."""
        grid = PhysarumGrid(10, 10)
        
        # These should not raise exceptions
        grid.deposit_trail(-1, 5, 1.0)  # Out of bounds
        grid.deposit_trail(15, 5, 1.0)  # Out of bounds
        grid.deposit_trail(5, -1, 1.0)  # Out of bounds
        grid.deposit_trail(5, 15, 1.0)  # Out of bounds
        
        # Grid should remain unchanged for out-of-bounds deposits
        assert np.all(grid.trail_map == 0)
    
    def test_grid_diffusion_no_effect_when_zero(self):
        """Test that diffusion has no effect when diffusion rate is 0."""
        grid = PhysarumGrid(10, 10)
        grid.deposit_trail(5, 5, 1.0)
        
        initial_state = grid.trail_map.copy()
        grid.apply_diffusion(0.0)
        
        assert np.array_equal(grid.trail_map, initial_state)
    
    def test_grid_diffusion_spreads_pheromone(self):
        """Test that diffusion spreads pheromone to neighboring cells."""
        grid = PhysarumGrid(10, 10)
        center_x, center_y = 5, 5
        initial_amount = 1.0
        diffusion_rate = 0.5
        
        # Deposit pheromone at center
        grid.deposit_trail(center_x, center_y, initial_amount)
        
        # Apply diffusion
        grid.apply_diffusion(diffusion_rate)
        
        # Center should have less pheromone
        assert grid.trail_map[center_y, center_x] < initial_amount
        
        # Neighbors should have gained pheromone
        neighbors_have_pheromone = False
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip center
                x, y = center_x + dx, center_y + dy
                if 0 <= x < grid.width and 0 <= y < grid.height:
                    if grid.trail_map[y, x] > 0:
                        neighbors_have_pheromone = True
                        break
        
        assert neighbors_have_pheromone
    
    def test_grid_diffusion_conserves_total_pheromone(self):
        """Test that diffusion conserves total pheromone in the system."""
        grid = PhysarumGrid(10, 10)
        grid.deposit_trail(5, 5, 1.0)
        grid.deposit_trail(3, 3, 0.5)
        
        total_before = np.sum(grid.trail_map)
        grid.apply_diffusion(0.3)
        total_after = np.sum(grid.trail_map)
        
        # Total should be conserved (within floating point precision)
        assert np.isclose(total_before, total_after, atol=1e-6)
    
    def test_grid_diffusion_with_boundaries(self):
        """Test diffusion behavior at grid boundaries."""
        grid = PhysarumGrid(5, 5)
        # Place pheromone at corner
        grid.deposit_trail(0, 0, 1.0)
        
        initial_total = np.sum(grid.trail_map)
        grid.apply_diffusion(0.5)
        final_total = np.sum(grid.trail_map)
        
        # Pheromone should still be conserved even at boundaries
        assert np.isclose(initial_total, final_total, atol=1e-6)
        
        # Corner should have less pheromone after diffusion
        assert grid.trail_map[0, 0] < 1.0


class TestPhysarumActor:
    """Test cases for the PhysarumActor class."""
    
    def test_actor_initialization(self):
        """Test that actor initializes with correct parameters."""
        x, y = 50.0, 50.0
        angle = np.pi / 4  # 45 degrees
        view_radius = 5
        view_distance = 10
        
        actor = PhysarumActor(x, y, angle, view_radius, view_distance)
        
        assert actor.x == x
        assert actor.y == y
        assert actor.angle == angle
        assert actor.view_radius == view_radius
        assert actor.view_distance == view_distance
    
    def test_actor_movement(self):
        """Test actor movement based on angle and speed."""
        actor = PhysarumActor(0.0, 0.0, 0.0, 5, 10)  # Facing right (0 radians)
        speed = 1.0
        
        initial_x, initial_y = actor.x, actor.y
        actor.move(speed)
        
        # Should move right (positive x direction)
        assert actor.x > initial_x
        assert actor.y == initial_y
    
    def test_actor_sensing(self):
        """Test actor's ability to sense trails in its environment."""
        grid = PhysarumGrid(100, 100)
        actor = PhysarumActor(50.0, 50.0, 0.0, 3, 10)
        
        # Place some trail ahead of the actor
        grid.deposit_trail(60, 50, 1.0)
        
        left_sense, center_sense, right_sense = actor.sense_environment(grid)
        
        # All sense values should be non-negative
        assert left_sense >= 0
        assert center_sense >= 0
        assert right_sense >= 0
    
    def test_actor_steering(self):
        """Test actor's steering behavior based on sensor inputs."""
        actor = PhysarumActor(50.0, 50.0, 0.0, 3, 10)
        
        # Test different steering scenarios
        initial_angle = actor.angle
        
        # Stronger signal on the left should turn left
        actor.steer(1.0, 0.0, 0.0)  # left > center > right
        assert actor.angle != initial_angle
        
        # Reset angle
        actor.angle = 0.0
        
        # Stronger signal on the right should turn right
        actor.steer(0.0, 0.0, 1.0)  # right > center > left
        assert actor.angle != 0.0


class TestPhysarumSimulation:
    """Test cases for the PhysarumSimulation class."""
    
    def test_simulation_initialization(self):
        """Test that simulation initializes with correct parameters."""
        width, height = 100, 100
        num_actors = 10
        decay_rate = 0.01
        
        simulation = PhysarumSimulation(width, height, num_actors, decay_rate)
        
        assert simulation.grid.width == width
        assert simulation.grid.height == height
        assert len(simulation.actors) == num_actors
        assert simulation.decay_rate == decay_rate
    
    def test_simulation_step(self):
        """Test that simulation can perform a single step without errors."""
        simulation = PhysarumSimulation(50, 50, 5, 0.01)
        
        # Should not raise any exceptions
        simulation.step()
        
        # Trail map should have some non-zero values after a step
        assert np.any(simulation.grid.trail_map > 0)
    
    def test_simulation_multiple_steps(self):
        """Test that simulation can run multiple steps."""
        simulation = PhysarumSimulation(50, 50, 5, 0.01)
        
        initial_state = simulation.grid.trail_map.copy()
        
        # Run several steps
        for _ in range(10):
            simulation.step()
        
        # State should have changed
        assert not np.array_equal(simulation.grid.trail_map, initial_state)
    
    def test_simulation_parameters_validation(self):
        """Test that simulation validates input parameters."""
        # Test invalid dimensions
        with pytest.raises(ValueError):
            PhysarumSimulation(0, 100, 10, 0.01)
        
        with pytest.raises(ValueError):
            PhysarumSimulation(100, 0, 10, 0.01)
        
        # Test invalid number of actors
        with pytest.raises(ValueError):
            PhysarumSimulation(100, 100, 0, 0.01)
        
        # Test invalid decay rate
        with pytest.raises(ValueError):
            PhysarumSimulation(100, 100, 10, -0.01)
        
        with pytest.raises(ValueError):
            PhysarumSimulation(100, 100, 10, 1.1)
        
        # Test invalid diffusion rate
        with pytest.raises(ValueError):
            PhysarumSimulation(100, 100, 10, 0.01, diffusion_rate=-0.1)
        
        with pytest.raises(ValueError):
            PhysarumSimulation(100, 100, 10, 0.01, diffusion_rate=1.1)
    
    def test_simulation_with_diffusion(self):
        """Test that simulation works correctly with diffusion enabled."""
        simulation = PhysarumSimulation(50, 50, 5, decay_rate=0.01, diffusion_rate=0.1)
        
        # Should not raise any exceptions
        simulation.step()
        
        # Trail map should have some non-zero values after a step
        assert np.any(simulation.grid.trail_map > 0)
        
        # Diffusion rate should be stored correctly
        assert simulation.diffusion_rate == 0.1
    
    def test_simulation_diffusion_default_zero(self):
        """Test that diffusion rate defaults to 0.0 when not specified."""
        simulation = PhysarumSimulation(50, 50, 5, 0.01)
        
        assert simulation.diffusion_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__])