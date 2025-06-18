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

### 6. Documentation and Polish
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