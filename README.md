# 3D Physarum Model Generator

This application generates 3D models based on the Physarum slime mold algorithm. The application creates fascinating organic structures that can be 3D printed.

## Features

* **Central Base Growth**: The colony starts from a central "base" and can only grow upward. Movement along the Z-axis represents movement through time in a 2D physarum simulation.
* **Connected Structures**: The resulting model is completely self-connected with no disconnected pieces when considering the Z-axis.
* **STL Output**: Generates .STL files suitable for 3D printing.
* **Configurable Parameters**: Full control over simulation parameters including number of actors, decay rate, view radius and distance, etc.
* **Command Line Interface**: Easy-to-use CLI with comprehensive parameter validation and help.

## Installation

This project uses `uv` for dependency management. Make sure you have `uv` installed, then:

```bash
uv pip install -r pyproject.toml
```

## Usage

### Basic Usage

Generate a 3D model with default parameters:

```bash
python main.py
```

This will create a file named `physarum_3d_model.stl` in the current directory.

### Command Line Options

#### Simulation Parameters

- `--width N`: Grid width in pixels (default: 100)
- `--height N`: Grid height in pixels (default: 100)
- `--actors N`: Number of Physarum actors (default: 50)
- `--steps N`: Number of simulation steps (default: 100)
- `--decay F`: Trail decay rate 0.0-1.0 (default: 0.01)
- `--view-radius N`: Actor sensing radius (default: 3)
- `--view-distance N`: Actor sensing distance (default: 10)
- `--speed F`: Actor movement speed (default: 1.0)

#### 3D Model Parameters

- `--layer-height F`: Height of each layer in 3D model (default: 1.0)
- `--threshold F`: Minimum trail strength for 3D inclusion (default: 0.1)
- `--base-radius N`: Radius of the central base (default: 10)
- `--layer-frequency N`: Capture layer every N steps (default: 5)

#### Output Parameters

- `--output FILE, -o FILE`: Output STL filename (default: physarum_3d_model.stl)
- `--quiet, -q`: Suppress progress output
- `--verbose, -v`: Show detailed progress information

### Examples

Create a larger, more complex model:
```bash
python main.py --steps 200 --actors 100 --output complex_model.stl
```

Generate a model with different dimensions and parameters:
```bash
python main.py --width 150 --height 150 --decay 0.02 --threshold 0.15
```

Create a model with modified sensing parameters:
```bash
python main.py --view-radius 5 --view-distance 15 --speed 1.5
```

Run quietly with custom output filename:
```bash
python main.py --quiet --output my_physarum.stl
```

### Help

Get full help and parameter descriptions:
```bash
python main.py --help
```

## Understanding the Parameters

- **Grid Size**: Larger grids (width/height) create more detailed models but take longer to compute
- **Actors**: More actors create denser, more complex structures
- **Steps**: More steps allow for more complex growth patterns
- **Decay Rate**: Higher decay rates (closer to 1.0) create more sparse structures
- **View Radius/Distance**: Controls how far ahead actors can "see" - affects branching patterns
- **Threshold**: Lower thresholds include more of the trail in the 3D model
- **Layer Frequency**: Lower values create more detailed vertical structure but larger files

## Output

The application generates an STL file that can be:
- Loaded into 3D printing software (Cura, PrusaSlicer, etc.)
- Viewed in 3D modeling software (Blender, MeshLab, etc.)
- 3D printed directly

The generated models are hollow structures that represent the paths taken by the Physarum simulation over time.
