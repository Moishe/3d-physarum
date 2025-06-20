# ABOUTME: Test suite for actor lifecycle simulation features in Physarum model
# ABOUTME: Tests circular placement, age-based death, and actor spawning mechanics

import unittest
import math
import random
from physarum import PhysarumSimulation, PhysarumActor


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
        self.assertGreater(final_count, initial_count * 0.5)
        self.assertLess(final_count, initial_count * 1.5)
    
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


if __name__ == '__main__':
    unittest.main()