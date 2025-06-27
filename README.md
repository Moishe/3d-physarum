# 3D Physarum Model Generator

A comprehensive workspace for generating 3D models based on the Physarum slime mold algorithm. This project creates fascinating organic structures that can be 3D printed, with both command-line and web interfaces available.

## Project Structure

This is a uv workspace containing multiple packages:

```
├── physarum-core/     # Core simulation engine and 3D model generation
├── cli/              # Command-line interface
├── web/              # Web application (React frontend + FastAPI backend)
│   ├── frontend/     # React/TypeScript web interface
│   └── backend/      # FastAPI REST API server
└── README.md         # This file
```

## Features

* **Time-Layered Growth**: Movement along the Z-axis represents movement through time in a 2D physarum simulation
* **Connected Structures**: The resulting model is completely self-connected with no disconnected pieces when considering the Z-axis
* **STL Output**: Generates .STL files suitable for 3D printing
* **Configurable Parameters**: Full control over simulation parameters including number of actors, decay rate, view radius and distance, etc.
* **Multiple Interfaces**: Both command-line and web-based interfaces available
* **Real-time Progress**: Web interface provides live simulation progress updates
* **Preview Generation**: Generate preview images of simulations

## Installation

This project uses `uv` for dependency management. Make sure you have `uv` installed, then:

```bash
# Install all workspace dependencies
uv sync
```

## Usage

### Web Interface (Recommended)

The web interface provides an interactive experience for generating 3D models:

1. **Start the backend server:**
   ```bash
   cd web/backend
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend (in a new terminal):**
   ```bash
   cd web/frontend
   npm install
   npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Command Line Interface

Generate a 3D model with default parameters:

```bash
cd cli
uv run python main.py
```

This will create a file named `physarum_3d_model.stl` in the cli directory.

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
- `--layer-frequency N`: Capture layer every N steps (default: 5)

#### Output Parameters

- `--output FILE, -o FILE`: Output STL filename (default: physarum_3d_model.stl)
- `--quiet, -q`: Suppress progress output
- `--verbose, -v`: Show detailed progress information

### CLI Examples

Create a larger, more complex model:
```bash
cd cli
uv run python main.py --steps 200 --actors 100 --output complex_model.stl
```

Generate a model with different dimensions and parameters:
```bash
cd cli
uv run python main.py --width 150 --height 150 --decay 0.02 --threshold 0.15
```

Create a model with modified sensing parameters:
```bash
cd cli
uv run python main.py --view-radius 5 --view-distance 15 --speed 1.5
```

Run quietly with custom output filename:
```bash
cd cli
uv run python main.py --quiet --output my_physarum.stl
```

### CLI Help

Get full help and parameter descriptions:
```bash
cd cli
uv run python main.py --help
```

## Understanding the Parameters

- **Grid Size**: Larger grids (width/height) create more detailed models but take longer to compute
- **Actors**: More actors create denser, more complex structures
- **Steps**: More steps allow for more complex growth patterns
- **Decay Rate**: Higher decay rates (closer to 1.0) create more sparse structures
- **View Radius/Distance**: Controls how far ahead actors can "see" - affects branching patterns
- **Threshold**: Lower thresholds include more of the trail in the 3D model
- **Layer Frequency**: Lower values create more detailed vertical structure but larger files

## Development

### Workspace Structure

This project uses a uv workspace with the following packages:

- **`physarum-core`**: Core simulation engine and 3D model generation
- **`cli`**: Command-line interface tools
- **`web/backend`**: FastAPI REST API server
- **`web/frontend`**: React/TypeScript web interface

### Running Tests

The core package includes comprehensive tests:

```bash
cd physarum-core
uv run pytest
```

### Using the Core Package

The `physarum-core` package can be used programmatically:

```python
from physarum_core.simulation import PhysarumSimulation
from physarum_core.models.model_3d import Model3DGenerator

# Create and run simulation
sim = PhysarumSimulation(width=100, height=100, actors=50)
sim.run(steps=100)

# Generate 3D model
generator = Model3DGenerator()
model = generator.generate_model(sim.get_layers())
generator.save_stl(model, "output.stl")
```

## Output

The application generates STL files that can be:
- Loaded into 3D printing software (Cura, PrusaSlicer, etc.)
- Viewed in 3D modeling software (Blender, MeshLab, etc.)
- 3D printed directly

The generated models are hollow structures that represent the paths taken by the Physarum simulation over time.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `cd physarum-core && uv run pytest`
5. Submit a pull request

For detailed development information, see the README files in individual package directories.
