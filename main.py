# ABOUTME: Main entry point for the 3D Physarum model generator
# ABOUTME: Provides command-line interface and demonstration of the simulation engine

import argparse
import sys
import os
from physarum import PhysarumSimulation
from model_3d import Model3DGenerator
from model_3d_smooth import SmoothModel3DGenerator
import numpy as np


def create_argument_parser():
    """Create and configure the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate 3D models from Physarum slime mold simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --steps 200 --actors 100 --output my_model.stl
  %(prog)s --width 150 --height 150 --decay 0.02 --threshold 0.15
  %(prog)s --view-radius 5 --view-distance 15 --speed 1.5
  %(prog)s --diffusion-rate 0.1 --decay 0.005 --steps 300
  %(prog)s --smooth --smoothing-iterations 3 --output smooth_model.stl
  %(prog)s --smooth --smoothing-type taubin --taubin-lambda 0.6 --mesh-quality
  %(prog)s --smooth --smoothing-type feature_preserving --preserve-features --feature-angle 45
        """
    )
    
    # Simulation parameters
    sim_group = parser.add_argument_group('Simulation Parameters')
    sim_group.add_argument('--width', type=int, default=100, metavar='N',
                          help='Grid width in pixels (default: 100)')
    sim_group.add_argument('--height', type=int, default=100, metavar='N',
                          help='Grid height in pixels (default: 100)')
    sim_group.add_argument('--actors', type=int, default=50, metavar='N',
                          help='Number of Physarum actors (default: 50)')
    sim_group.add_argument('--steps', type=int, default=100, metavar='N',
                          help='Number of simulation steps (default: 100)')
    sim_group.add_argument('--decay', type=float, default=0.01, metavar='F',
                          help='Trail decay rate 0.0-1.0 (default: 0.01)')
    sim_group.add_argument('--view-radius', type=int, default=3, metavar='N',
                          help='Actor sensing radius (default: 3)')
    sim_group.add_argument('--view-distance', type=int, default=10, metavar='N',
                          help='Actor sensing distance (default: 10)')
    sim_group.add_argument('--speed', type=float, default=1.0, metavar='F',
                          help='Actor movement speed (default: 1.0)')
    sim_group.add_argument('--initial-diameter', type=float, default=20.0, metavar='F',
                          help='Initial circle diameter for actor placement (default: 20.0)')
    sim_group.add_argument('--death-probability', type=float, default=0.001, metavar='F',
                          help='Age-based death probability per step (default: 0.001)')
    sim_group.add_argument('--spawn-probability', type=float, default=0.005, metavar='F',
                          help='Probability of spawning new actors from existing locations (default: 0.005)')
    sim_group.add_argument('--diffusion-rate', type=float, default=0.0, metavar='F',
                          help='Pheromone diffusion rate 0.0-1.0 (default: 0.0 - no diffusion)')
    sim_group.add_argument('--direction-deviation', type=float, default=1.57, metavar='F',
                          help='Maximum direction deviation for spawned actors in radians (default: 1.57 - π/2 radians)')
    sim_group.add_argument('--image', type=str, metavar='PATH',
                          help='JPEG image path for initial actor placement (overrides --actors)')
    
    # 3D model parameters
    model_group = parser.add_argument_group('3D Model Parameters')
    model_group.add_argument('--smooth', action='store_true',
                            help='Use smooth surface generation (marching cubes) instead of voxels')
    model_group.add_argument('--layer-height', type=float, default=1.0, metavar='F',
                            help='Height of each layer in 3D model (default: 1.0)')
    model_group.add_argument('--threshold', type=float, default=0.1, metavar='F',
                            help='Minimum trail strength for 3D inclusion (default: 0.1)')
    model_group.add_argument('--layer-frequency', type=int, default=5, metavar='N',
                            help='Capture layer every N steps (default: 5)')
    model_group.add_argument('--smoothing-iterations', type=int, default=2, metavar='N',
                            help='Number of smoothing iterations for smooth surfaces (default: 2)')
    model_group.add_argument('--smoothing-type', type=str, default='taubin', 
                            choices=['laplacian', 'taubin', 'feature_preserving'],
                            help='Type of smoothing algorithm (default: taubin)')
    model_group.add_argument('--taubin-lambda', type=float, default=0.5, metavar='F',
                            help='Taubin smoothing lambda parameter (default: 0.5)')
    model_group.add_argument('--taubin-mu', type=float, default=-0.52, metavar='F',
                            help='Taubin smoothing mu parameter (default: -0.52)')
    model_group.add_argument('--preserve-features', action='store_true',
                            help='Preserve sharp features during smoothing')
    model_group.add_argument('--feature-angle', type=float, default=60.0, metavar='F',
                            help='Feature edge angle threshold in degrees (default: 60.0)')
    model_group.add_argument('--mesh-quality', action='store_true',
                            help='Show detailed mesh quality metrics')
    
    # Output parameters
    output_group = parser.add_argument_group('Output Parameters')
    output_group.add_argument('--output', '-o', type=str, default='physarum_3d_model.stl',
                             help='Output STL filename (default: physarum_3d_model.stl)')
    output_group.add_argument('--quiet', '-q', action='store_true',
                             help='Suppress progress output')
    output_group.add_argument('--verbose', '-v', action='store_true',
                             help='Show detailed progress information')
    
    return parser


def validate_parameters(args):
    """Validate command line parameters."""
    errors = []
    
    # Grid dimensions
    if args.width <= 0:
        errors.append("Width must be positive")
    if args.height <= 0:
        errors.append("Height must be positive")
    
    # Actor parameters
    if args.image is None and args.actors <= 0:
        errors.append("Number of actors must be positive when no image is provided")
    if args.steps <= 0:
        errors.append("Number of steps must be positive")
    
    # Image validation
    if args.image:
        import os
        if not os.path.exists(args.image):
            errors.append(f"Image file does not exist: {args.image}")
        elif not args.image.lower().endswith(('.jpg', '.jpeg')):
            errors.append("Image file must be a JPEG (.jpg or .jpeg)")
    
    # Rates and distances
    if args.decay < 0 or args.decay > 1:
        errors.append("Decay rate must be between 0.0 and 1.0")
    if args.view_radius < 0:
        errors.append("View radius must be non-negative")
    if args.view_distance < 0:
        errors.append("View distance must be non-negative")
    if args.speed < 0:
        errors.append("Speed must be non-negative")
    
    # 3D model parameters
    if args.layer_height <= 0:
        errors.append("Layer height must be positive")
    if args.threshold < 0:
        errors.append("Threshold must be non-negative")
    if args.layer_frequency <= 0:
        errors.append("Layer frequency must be positive")
    if args.smoothing_iterations < 0:
        errors.append("Smoothing iterations must be non-negative")
    if args.taubin_lambda <= 0 or args.taubin_lambda >= 1:
        errors.append("Taubin lambda must be between 0 and 1 (exclusive)")
    if args.taubin_mu >= 0 or args.taubin_mu <= -1:
        errors.append("Taubin mu must be between -1 and 0 (exclusive)")
    if args.feature_angle <= 0 or args.feature_angle >= 180:
        errors.append("Feature angle must be between 0 and 180 degrees")
    
    # Lifecycle parameters
    if args.initial_diameter <= 0:
        errors.append("Initial diameter must be positive")
    if args.death_probability < 0 or args.death_probability > 1:
        errors.append("Death probability must be between 0.0 and 1.0")
    if args.spawn_probability < 0 or args.spawn_probability > 1:
        errors.append("Spawn probability must be between 0.0 and 1.0")
    if args.diffusion_rate < 0 or args.diffusion_rate > 1:
        errors.append("Diffusion rate must be between 0.0 and 1.0")
    if args.direction_deviation < 0 or args.direction_deviation > 3.14159:
        errors.append("Direction deviation must be between 0.0 and π (3.14159) radians")
    
    # Output validation
    if not args.output.endswith('.stl'):
        errors.append("Output filename must end with .stl")
    
    if errors:
        print("Parameter validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def run_simulation_with_3d_generation(args):
    """Run the Physarum simulation and generate 3D model."""
    
    if not args.quiet:
        print("3D Physarum Model Generator")
        print("=" * 40)
        print(f"Grid size: {args.width}x{args.height}")
        if args.image:
            print(f"Initialization: Image-based ({args.image})")
        else:
            print(f"Actors: {args.actors}")
        print(f"Steps: {args.steps}")
        print(f"Decay rate: {args.decay}")
        print(f"Diffusion rate: {args.diffusion_rate}")
        print(f"View radius: {args.view_radius}")
        print(f"View distance: {args.view_distance}")
        print(f"Speed: {args.speed}")
        print(f"Model type: {'Smooth (Marching Cubes)' if args.smooth else 'Voxel-based'}")
        print(f"Layer height: {args.layer_height}")
        print(f"Threshold: {args.threshold}")
        if args.smooth:
            print(f"Smoothing iterations: {args.smoothing_iterations}")
            print(f"Smoothing type: {args.smoothing_type}")
            if args.smoothing_type == 'taubin':
                print(f"Taubin lambda: {args.taubin_lambda}")
                print(f"Taubin mu: {args.taubin_mu}")
            if args.smoothing_type == 'feature_preserving' or args.preserve_features:
                print(f"Preserve features: {args.preserve_features}")
                print(f"Feature angle: {args.feature_angle}°")
        print(f"Output file: {args.output}")
        print()
    
    # Create simulation
    simulation = PhysarumSimulation(
        width=args.width,
        height=args.height,
        num_actors=args.actors,
        decay_rate=args.decay,
        view_radius=args.view_radius,
        view_distance=args.view_distance,
        speed=args.speed,
        initial_diameter=args.initial_diameter,
        death_probability=args.death_probability,
        spawn_probability=args.spawn_probability,
        diffusion_rate=args.diffusion_rate,
        direction_deviation=args.direction_deviation,
        image_path=args.image
    )
    
    # Create 3D model generator (smooth or voxel-based)
    if args.smooth:
        generator = SmoothModel3DGenerator(
            simulation=simulation,
            layer_height=args.layer_height,
            threshold=args.threshold,
            smoothing_iterations=args.smoothing_iterations,
            smoothing_type=args.smoothing_type,
            taubin_lambda=args.taubin_lambda,
            taubin_mu=args.taubin_mu,
            preserve_features=args.preserve_features,
            feature_angle=args.feature_angle
        )
    else:
        generator = Model3DGenerator(
            simulation=simulation,
            layer_height=args.layer_height,
            threshold=args.threshold
        )
    
    if not args.quiet:
        print("Running simulation and generating 3D model...")
    
    # Run simulation with layer capture
    for step in range(args.steps):
        simulation.step()
        
        # Capture layer at specified frequency
        if step % args.layer_frequency == 0:
            generator.capture_layer()
        
        # Progress reporting
        if not args.quiet and step % 20 == 0:
            trail_map = simulation.get_trail_map()
            max_trail = np.max(trail_map)
            mean_trail = np.mean(trail_map)
            layers_captured = generator.get_layer_count()
            actor_count = simulation.get_actor_count()
            print(f"  Step {step:3d}: Max trail = {max_trail:.3f}, "
                  f"Mean trail = {mean_trail:.3f}, Layers = {layers_captured}, Actors = {actor_count}")
    
    # Capture final layer
    generator.capture_layer()
    
    if not args.quiet:
        print(f"\nSimulation completed. Captured {generator.get_layer_count()} layers.")
        print("Validating 3D model connectivity...")
    
    # Validate connectivity
    if not generator.validate_connectivity():
        print("Warning: 3D model may have connectivity issues", file=sys.stderr)
    
    # Generate and save STL file
    if not args.quiet:
        print(f"Generating STL file: {args.output}")
    
    try:
        generator.save_stl(args.output)
        if not args.quiet:
            print(f"✓ STL file saved successfully: {args.output}")
            
            # File size information
            file_size = os.path.getsize(args.output)
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
            print(f"  File size: {size_str}")
            
            # Show mesh quality metrics if requested and using smooth generator
            if args.mesh_quality and args.smooth and hasattr(generator, 'get_mesh_quality_metrics'):
                print("\nMesh Quality Metrics:")
                print("-" * 20)
                metrics = generator.get_mesh_quality_metrics()
                if "error" in metrics:
                    print(f"Error: {metrics['error']}")
                else:
                    print(f"Vertices: {metrics['vertex_count']:,}")
                    print(f"Faces: {metrics['face_count']:,}")
                    print(f"Volume: {metrics['volume']:.2f}")
                    print(f"Surface Area: {metrics['surface_area']:.2f}")
                    print(f"Watertight: {'✓' if metrics['is_watertight'] else '✗'}")
                    print(f"Winding Consistent: {'✓' if metrics['is_winding_consistent'] else '✗'}")
                    print(f"3D Print Ready: {'✓' if metrics['print_ready'] else '✗'}")
                    if metrics['issues']:
                        print("Issues:")
                        for issue in metrics['issues']:
                            print(f"  - {issue}")
            
    except Exception as e:
        print(f"Error saving STL file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the 3D Physarum model generator."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate parameters
    validate_parameters(args)
    
    # Run simulation and generate 3D model
    run_simulation_with_3d_generation(args)


if __name__ == "__main__":
    main()
