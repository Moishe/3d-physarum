# ABOUTME: Test suite for actor lifecycle simulation features in Physarum model
# ABOUTME: Tests circular placement, age-based death, and actor spawning mechanics

import unittest
import math
import random
from physarum_core.simulation import PhysarumSimulation, PhysarumActor


class TestLifecycleFunctionality(unittest.TestCase):
    """Test cases for the lifecycle simulation features."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set random seed for reproducible tests
        random.seed(42)
        
    def test_actor_age_tracking(self):
        """Test that actors age correctly over time."""
        actor = PhysarumActor(50, 50, 0, 3, 10)
        
        # Initial age should be 0
        self.assertEqual(actor.age, 0)
        
        # Age should increment with each step
        actor.age_step()
        self.assertEqual(actor.age, 1)
        
        actor.age_step()
        self.assertEqual(actor.age, 2)
    
    def test_death_probability_increases_with_age(self):
        """Test that death probability increases with actor age."""
        actor = PhysarumActor(50, 50, 0, 3, 10)
        base_death_prob = 0.1
        
        # Young actor should have lower death probability
        young_death_prob = actor.should_die(base_death_prob)
        
        # Age the actor significantly
        for _ in range(100):
            actor.age_step()
        
        # Older actor should have higher death probability
        # Test multiple times to account for randomness
        older_death_attempts = [actor.should_die(base_death_prob) for _ in range(100)]
        older_death_rate = sum(older_death_attempts) / len(older_death_attempts)
        
        # Reset actor age to 0 for comparison
        actor.age = 0
        young_death_attempts = [actor.should_die(base_death_prob) for _ in range(100)]
        young_death_rate = sum(young_death_attempts) / len(young_death_attempts)
        
        # Older actors should have higher death rate
        self.assertGreater(older_death_rate, young_death_rate)
    
    def test_circular_initial_placement(self):
        """Test that actors are initially placed in a circular pattern."""
        width, height = 100, 100
        num_actors = 8
        diameter = 20.0
        
        sim = PhysarumSimulation(
            width=width,
            height=height,
            num_actors=num_actors,
            decay_rate=0.01,
            initial_diameter=diameter
        )
        
        # Check that we have the right number of actors
        self.assertEqual(len(sim.actors), num_actors)
        
        # Check that actors are placed within the expected circular area
        center_x, center_y = width / 2, height / 2
        radius = diameter / 2
        
        for actor in sim.actors:
            distance_from_center = math.sqrt((actor.x - center_x)**2 + (actor.y - center_y)**2)
            # Allow some tolerance for actors placed within the circle
            self.assertLessEqual(distance_from_center, radius + 1)
    
    def test_actor_death_mechanism(self):
        """Test that actors die and are removed from simulation."""
        sim = PhysarumSimulation(
            width=100,
            height=100,
            num_actors=10,
            decay_rate=0.01,
            death_probability=1.0  # 100% death probability for testing
        )
        
        initial_count = sim.get_actor_count()
        self.assertEqual(initial_count, 10)
        
        # Run one step - all actors should die with 100% probability
        sim.step()
        
        # All actors should be dead
        self.assertEqual(sim.get_actor_count(), 0)
    
    def test_actor_spawning_mechanism(self):
        """Test that new actors spawn from existing ones."""
        sim = PhysarumSimulation(
            width=100,
            height=100,
            num_actors=5,
            decay_rate=0.01,
            death_probability=0.0,  # No death for this test
            spawn_probability=1.0   # 100% spawn probability for testing
        )
        
        initial_count = sim.get_actor_count()
        self.assertEqual(initial_count, 5)
        
        # Run one step - each actor should spawn a new one
        sim.step()
        
        # Should have doubled the number of actors
        self.assertEqual(sim.get_actor_count(), 10)
    
    def test_lifecycle_balance(self):
        """Test that death and spawning can balance each other."""
        sim = PhysarumSimulation(
            width=100,
            height=100,
            num_actors=20,
            decay_rate=0.01,
            death_probability=0.05,
            spawn_probability=0.05
        )
        
        initial_count = sim.get_actor_count()
        
        # Run simulation for multiple steps
        for _ in range(50):
            sim.step()
        
        final_count = sim.get_actor_count()
        
        # Population should still exist (not extinct)
        self.assertGreater(final_count, 0)
        
        # Population should be reasonably stable (within 50% of initial)
        self.assertGreaterEqual(final_count, initial_count * 0.5)
        self.assertLessEqual(final_count, initial_count * 1.5)
    
    def test_spawn_location_near_parent(self):
        """Test that spawned actors appear near parent actors."""
        sim = PhysarumSimulation(
            width=100,
            height=100,
            num_actors=1,
            decay_rate=0.01,
            death_probability=0.0,
            spawn_probability=1.0
        )
        
        # Get original actor position
        original_actor = sim.actors[0]
        original_x, original_y = original_actor.x, original_actor.y
        
        # Run one step to spawn
        sim.step()
        
        # Should have 2 actors now
        self.assertEqual(sim.get_actor_count(), 2)
        
        # Find the new actor
        new_actor = None
        for actor in sim.actors:
            if actor != original_actor:
                new_actor = actor
                break
        
        self.assertIsNotNone(new_actor)
        
        # New actor should be within spawn distance (5.0) of original
        distance = math.sqrt((new_actor.x - original_x)**2 + (new_actor.y - original_y)**2)
        self.assertLessEqual(distance, 6.0)  # Allow small tolerance
    
    def test_no_spawning_when_no_actors(self):
        """Test that no spawning occurs when there are no actors."""
        sim = PhysarumSimulation(
            width=100,
            height=100,
            num_actors=1,
            decay_rate=0.01,
            death_probability=1.0,  # Kill all actors
            spawn_probability=1.0   # High spawn probability
        )
        
        # Run one step - actor should die
        sim.step()
        self.assertEqual(sim.get_actor_count(), 0)
        
        # Run another step - no spawning should occur
        sim.step()
        self.assertEqual(sim.get_actor_count(), 0)
    
    def test_boundary_wrapping_for_spawned_actors(self):
        """Test that spawned actors wrap around boundaries correctly."""
        sim = PhysarumSimulation(
            width=10,
            height=10,
            num_actors=1,
            decay_rate=0.01,
            death_probability=0.0,
            spawn_probability=1.0
        )
        
        # Place actor near boundary
        sim.actors[0].x = 1.0
        sim.actors[0].y = 1.0
        
        # Run simulation steps to trigger spawning
        for _ in range(10):
            sim.step()
        
        # Check that all actors are within bounds
        for actor in sim.actors:
            self.assertGreaterEqual(actor.x, 0)
            self.assertLess(actor.x, 10)
            self.assertGreaterEqual(actor.y, 0)
            self.assertLess(actor.y, 10)
    
    def test_direction_inheritance_with_zero_deviation(self):
        """Test that spawned actors inherit parent direction with zero deviation."""
        # Set up simulation with zero deviation
        sim = PhysarumSimulation(
            width=100, height=100, num_actors=1, decay_rate=0.01,
            spawn_probability=1.0, direction_deviation=0.0
        )
        
        # Set parent actor to specific direction
        parent_angle = math.pi / 4  # 45 degrees
        sim.actors[0].angle = parent_angle
        
        # Force spawning
        initial_count = len(sim.actors)
        sim._handle_spawning()
        
        # Check that new actors have the same direction as parent
        new_actors = sim.actors[initial_count:]
        self.assertGreater(len(new_actors), 0, "No actors were spawned")
        
        for actor in new_actors:
            self.assertAlmostEqual(actor.angle, parent_angle, places=5,
                                 msg="Spawned actor should have same angle as parent with zero deviation")
    
    def test_direction_inheritance_with_deviation(self):
        """Test that spawned actors inherit parent direction with configurable deviation."""
        # Set a fresh random seed for this test to ensure consistency
        random.seed(123)
        
        deviation = math.pi / 6  # 30 degrees
        sim = PhysarumSimulation(
            width=100, height=100, num_actors=1, decay_rate=0.01,
            spawn_probability=1.0, direction_deviation=deviation
        )
        
        # Set parent actor to specific direction
        parent_angle = math.pi / 2  # 90 degrees
        sim.actors[0].angle = parent_angle
        
        # Force spawning once and test
        initial_count = len(sim.actors)
        sim._handle_spawning()
        new_actors = sim.actors[initial_count:]
        
        self.assertGreater(len(new_actors), 0, "No actors were spawned")
        
        # Check that all spawned angles are within deviation range
        for actor in new_actors:
            angle = actor.angle
            # Verify deviation is within expected range directly
            expected_min = parent_angle - deviation
            expected_max = parent_angle + deviation
            self.assertTrue(expected_min <= angle <= expected_max,
                          f"Spawned angle {angle} ({math.degrees(angle):.1f}°) not in expected range "
                          f"[{expected_min:.3f}, {expected_max:.3f}] "
                          f"({math.degrees(expected_min):.1f}°, {math.degrees(expected_max):.1f}°)")
            
            # Additional check: deviation from parent should be within bounds
            deviation_from_parent = abs(angle - parent_angle)
            self.assertLessEqual(deviation_from_parent, deviation + 0.001,
                               f"Deviation {deviation_from_parent:.3f} ({math.degrees(deviation_from_parent):.1f}°) "
                               f"exceeds maximum {deviation:.3f} ({math.degrees(deviation):.1f}°)")
    
    def test_direction_inheritance_parameter_validation(self):
        """Test that direction deviation parameter is validated correctly."""
        # Test negative deviation (should raise error)
        with self.assertRaises(ValueError):
            PhysarumSimulation(
                width=100, height=100, num_actors=1, decay_rate=0.01,
                direction_deviation=-0.1
            )
        
        # Test deviation > π (should raise error)
        with self.assertRaises(ValueError):
            PhysarumSimulation(
                width=100, height=100, num_actors=1, decay_rate=0.01,
                direction_deviation=4.0
            )
        
        # Test valid deviation (should not raise error)
        try:
            sim = PhysarumSimulation(
                width=100, height=100, num_actors=1, decay_rate=0.01,
                direction_deviation=math.pi / 4
            )
            self.assertEqual(sim.direction_deviation, math.pi / 4)
        except ValueError:
            self.fail("Valid direction deviation should not raise ValueError")
    
    def test_direction_inheritance_with_multiple_parents(self):
        """Test that multiple parents spawn with correct direction inheritance."""
        deviation = math.pi / 8  # 22.5 degrees
        sim = PhysarumSimulation(
            width=100, height=100, num_actors=3, decay_rate=0.01,
            spawn_probability=1.0, direction_deviation=deviation
        )
        
        # Set different angles for each parent
        parent_angles = [0, math.pi / 2, math.pi]
        for i, angle in enumerate(parent_angles):
            sim.actors[i].angle = angle
        
        # Force spawning
        initial_count = len(sim.actors)
        sim._handle_spawning()
        new_actors = sim.actors[initial_count:]
        
        self.assertGreater(len(new_actors), 0, "No actors were spawned")
        
        # Check that spawned actors have angles close to their parents
        # Note: We can't directly match parent to child, but we can verify
        # that all spawned angles are close to at least one parent angle
        for new_actor in new_actors:
            found_close_parent = False
            for parent_angle in parent_angles:
                angle_diff = abs(new_actor.angle - parent_angle)
                angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
                if angle_diff <= deviation + 0.001:  # Small tolerance
                    found_close_parent = True
                    break
            
            self.assertTrue(found_close_parent, 
                          f"Spawned actor angle {new_actor.angle} is not close to any parent angle")
    
    def test_direction_inheritance_triangular_distribution(self):
        """Test that spawned actors use triangular distribution for direction deviation."""
        # Set a specific random seed for reproducible results
        random.seed(456)
        
        deviation = math.pi / 4  # 45 degrees
        sim = PhysarumSimulation(
            width=100, height=100, num_actors=1, decay_rate=0.01,
            spawn_probability=1.0, direction_deviation=deviation
        )
        
        # Set parent actor to specific direction
        parent_angle = math.pi / 2  # 90 degrees
        sim.actors[0].angle = parent_angle
        
        # Collect many samples to test distribution shape
        deviations = []
        for _ in range(200):
            # Reset to single actor and spawn
            sim.actors = [sim.actors[0]]  # Keep only the parent
            initial_count = len(sim.actors)
            sim._handle_spawning()
            new_actors = sim.actors[initial_count:]
            
            for actor in new_actors:
                deviation_from_parent = actor.angle - parent_angle
                deviations.append(deviation_from_parent)
        
        self.assertGreater(len(deviations), 0, "No deviations collected")
        
        # Test that all deviations are within bounds
        for dev in deviations:
            self.assertTrue(-deviation <= dev <= deviation,
                          f"Deviation {dev} outside bounds [-{deviation}, {deviation}]")
        
        # Test triangular distribution properties:
        # 1. More values should be closer to 0 than to the extremes
        close_to_zero = sum(1 for dev in deviations if abs(dev) <= deviation / 3)
        close_to_extremes = sum(1 for dev in deviations if abs(dev) >= 2 * deviation / 3)
        
        # With triangular distribution, there should be more samples close to zero
        self.assertGreater(close_to_zero, close_to_extremes,
                         "Triangular distribution should have more values near zero than near extremes")
        
        # 2. Mean should be close to 0 (parent angle)
        mean_deviation = sum(deviations) / len(deviations)
        self.assertAlmostEqual(mean_deviation, 0.0, delta=0.1,
                             msg="Mean deviation should be close to 0 with triangular distribution")


if __name__ == '__main__':
    unittest.main()