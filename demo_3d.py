# ABOUTME: Demonstration script for 3D Physarum model generation
# ABOUTME: Shows how to create and save STL files from Physarum simulations

from model_3d import generate_3d_model_from_simulation
import sys


def main():
    """Demonstrate 3D model generation from Physarum simulation."""
    print("Generating 3D Physarum model...")
    
    # Generate 3D model from simulation
    generator = generate_3d_model_from_simulation(
        width=40,
        height=40,
        num_actors=15,
        decay_rate=0.005,
        steps=50,
        layer_height=1.0,
        threshold=0.15
    )
    
    print(f"Generated model with {generator.get_layer_count()} layers")
    
    # Validate connectivity
    if generator.validate_connectivity():
        print("✓ Model connectivity validation passed")
    else:
        print("✗ Model connectivity validation failed")
    
    # Save STL file
    output_filename = "physarum_3d_model.stl"
    generator.save_stl(output_filename)
    print(f"✓ STL file saved as '{output_filename}'")
    
    print("\nModel generation complete!")
    print(f"You can now 3D print the file '{output_filename}'")


if __name__ == "__main__":
    main()