# ABOUTME: Main entry point for the 3D Physarum model generator
# ABOUTME: Provides command-line interface and demonstration of the simulation engine

from physarum import PhysarumSimulation
import numpy as np


def main():
    """Run a demonstration of the Physarum simulation engine."""
    print("3D Physarum Model Generator")
    print("=" * 30)
    
    # Create a simulation with default parameters
    width, height = 100, 100
    num_actors = 50
    decay_rate = 0.01
    view_radius = 3
    view_distance = 10
    speed = 1.0
    
    print(f"Initializing simulation:")
    print(f"  Grid size: {width}x{height}")
    print(f"  Actors: {num_actors}")
    print(f"  Decay rate: {decay_rate}")
    print(f"  View radius: {view_radius}")
    print(f"  View distance: {view_distance}")
    print(f"  Speed: {speed}")
    
    # Create and run simulation
    simulation = PhysarumSimulation(
        width=width,
        height=height,
        num_actors=num_actors,
        decay_rate=decay_rate,
        view_radius=view_radius,
        view_distance=view_distance,
        speed=speed
    )
    
    print("\nRunning simulation...")
    steps = 100
    for step in range(steps):
        simulation.step()
        if step % 20 == 0:
            trail_map = simulation.get_trail_map()
            max_trail = np.max(trail_map)
            mean_trail = np.mean(trail_map)
            print(f"  Step {step:3d}: Max trail = {max_trail:.3f}, Mean trail = {mean_trail:.3f}")
    
    # Final statistics
    final_trail_map = simulation.get_trail_map()
    non_zero_pixels = np.count_nonzero(final_trail_map)
    total_pixels = width * height
    coverage = (non_zero_pixels / total_pixels) * 100
    
    print(f"\nSimulation completed after {steps} steps:")
    print(f"  Coverage: {coverage:.1f}% of grid")
    print(f"  Max trail strength: {np.max(final_trail_map):.3f}")
    print(f"  Mean trail strength: {np.mean(final_trail_map):.3f}")
    print(f"  Non-zero pixels: {non_zero_pixels}")
    
    print("\nPhysarum simulation engine implementation complete!")
    print("Next steps: 3D model generation, CLI interface, and file output.")


if __name__ == "__main__":
    main()
