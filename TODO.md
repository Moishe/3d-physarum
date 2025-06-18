# TODO - 3D Physarum Model Generator

## Core Implementation Tasks

### 1. Physarum Simulation Engine
- [x] Implement basic Physarum algorithm with actors/agents
- [x] Add physarum decay mechanics (multiple values per pixel)
- [x] Implement actor movement and sensing parameters
- [x] Add view radius and distance controls
- [x] Implement rate of decay parameter

### 2. 3D Model Generation
- [x] Design 2D to 3D conversion (Z-axis as time progression)
- [x] Implement central "base" starting point constraint
- [x] Ensure upward-only growth from the base
- [x] Add connectivity validation (no disconnected pieces)
- [x] Convert simulation data to 3D mesh structure

### 3. Command Line Interface
- [x] Create argument parser for simulation parameters
- [x] Add parameter validation
- [x] Implement help/usage documentation
- [x] Add configuration options for:
  - Number of actors
  - Rate of decay
  - View radius
  - View distance
  - Output file names
  - Simulation duration/steps
  - Layer height and frequency
  - Base radius and threshold

### 4. File Output Generation
- [x] Implement STL file generation for 3D printing
- [ ] Add 3D rendering to JPG functionality
- [x] Ensure proper file format compliance
- [x] Add error handling for file operations

### 5. Testing and Validation
- [ ] Create unit tests for Physarum algorithm
- [ ] Test 3D model connectivity validation
- [ ] Validate STL file output quality
- [ ] Test command line parameter handling
- [ ] Performance testing for large simulations

### 6. 3D Model Smoothing and Surface Quality Enhancement
- [ ] **Phase 1: Foundation - Replace Voxel Generation with Marching Cubes (High Priority)**
  - [ ] Add required dependencies (scikit-image, open3d, trimesh)
  - [ ] Create new smoothing module (`model_3d_smooth.py`)
  - [ ] Implement volume generation from layer stack
  - [ ] Integrate marching cubes surface extraction
  - [ ] Maintain compatibility with existing STL export
- [ ] **Phase 2: Surface Smoothing and Refinement (High Priority)**
  - [ ] Implement Laplacian smoothing with configurable iterations
  - [ ] Add Taubin smoothing to prevent volume loss
  - [ ] Implement mesh validation and repair for 3D printing
  - [ ] Add feature-preserving smoothing options
- [ ] **Phase 3: Adaptive Processing and Quality Control (Medium Priority)**
  - [ ] Implement multi-scale processing for different structure regions
  - [ ] Add quality metrics and mesh assessment tools
  - [ ] Create configurable processing pipeline with CLI integration
  - [ ] Add connectivity validation with detailed reporting
- [ ] **Phase 4: Advanced Features and Optimization (Low Priority)**
  - [ ] Add optional surface texturing based on trail density
  - [ ] Implement performance optimization and multi-threading
  - [ ] Add alternative algorithms (dual contouring, surface nets)
  - [ ] Create algorithm comparison and selection tools

### 7. Documentation and Polish
- [ ] Add inline code documentation
- [ ] Create usage examples
- [ ] Optimize performance for large models
- [ ] Add progress indicators for long simulations
- [ ] Error handling and user feedback

## Technical Considerations
- Ensure efficient memory usage for large 3D models
- Consider using numpy for numerical operations
- Look into libraries for STL generation and 3D rendering
- Plan for scalable simulation grid sizes

## 3D Smoothing Technical Notes
**Problem**: Current voxel-based approach creates blocky, pixelated STL files that don't capture the organic flow of Physarum growth patterns.

**Solution**: Replace cubic voxel generation with marching cubes surface extraction + mesh smoothing algorithms.

**Key Benefits**:
- Smooth, organic surfaces suitable for 3D printing
- Significantly reduced file sizes and triangle counts
- Better representation of natural Physarum branching patterns
- Professional-quality surface finish with maintained structural integrity

**Implementation Strategy**:
1. Convert layer stack (2D binary masks) to 3D volume array
2. Apply marching cubes algorithm to extract smooth isosurface
3. Use Laplacian/Taubin smoothing for surface refinement
4. Validate mesh for 3D printing compatibility (manifold, watertight)
5. Export as optimized STL file

**Dependencies to Add**:
- `scikit-image>=0.20.0` (marching cubes)
- `open3d>=0.17.0` (mesh processing and smoothing)
- `trimesh>=3.15.0` (mesh validation and repair)