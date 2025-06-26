# Project Restructuring Plan

## Current Issues

The project currently has a problematic structure where:
- Root directory contains shared simulation modules (`physarum.py`, `model_3d.py`, etc.)
- Web backend imports these modules via `sys.path` manipulation
- Dependencies are duplicated/conflicting between root and backend `pyproject.toml` files
- Missing dependencies discovered at runtime (e.g., `scikit-image`)

**Root cause**: The web backend tries to import from the project root using dynamic path manipulation, leading to dependency management issues.

## Recommended New Structure

```
/workspace
├── README.md
├── physarum-core/                  # New shared package
│   ├── pyproject.toml             # Core simulation dependencies
│   ├── README.md
│   └── physarum_core/             # Python package
│       ├── __init__.py
│       ├── simulation.py          # From physarum.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── model_3d.py        # From model_3d.py
│       │   └── model_3d_smooth.py # From model_3d_smooth.py
│       ├── output/
│       │   ├── __init__.py
│       │   └── manager.py         # From output_manager.py
│       ├── preview/
│       │   ├── __init__.py
│       │   └── generator.py       # From preview_generator.py
│       └── utils/
│           └── __init__.py
├── web/
│   ├── backend/
│   │   ├── pyproject.toml         # Depends on physarum-core
│   │   └── app/
│   └── frontend/
├── cli/                           # Optional: CLI tools
│   ├── pyproject.toml             # Depends on physarum-core
│   ├── main.py                    # From main.py
│   └── demo_3d.py                 # From demo_3d.py
└── tools/                         # Development tools
    └── scripts/
```

## Migration Steps

### Phase 1: Create Shared Package

1. **Create `physarum-core` directory structure**
   ```bash
   mkdir -p physarum-core/physarum_core/{models,output,preview,utils}
   touch physarum-core/physarum_core/__init__.py
   touch physarum-core/physarum_core/{models,output,preview,utils}/__init__.py
   ```

2. **Create `physarum-core/pyproject.toml`**
   ```toml
   [project]
   name = "physarum-core"
   version = "1.0.0"
   description = "Core simulation engine for 3D Physarum model generation"
   requires-python = ">=3.9"
   dependencies = [
       "numpy>=1.21.0",
       "scipy>=1.10.0",
       "pillow>=8.3.0",
       "trimesh>=3.15.0",
       "numpy-stl>=3.1.2",
       "scikit-image>=0.19.0",
   ]
   
   [project.optional-dependencies]
   dev = [
       "pytest>=7.0.0",
       "pytest-cov>=4.0.0",
   ]
   
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   
   [tool.hatch.build.targets.wheel]
   packages = ["physarum_core"]
   ```

3. **Move and refactor root modules**
   - `physarum.py` → `physarum-core/physarum_core/simulation.py`
   - `model_3d.py` → `physarum-core/physarum_core/models/model_3d.py`
   - `model_3d_smooth.py` → `physarum-core/physarum_core/models/model_3d_smooth.py`
   - `output_manager.py` → `physarum-core/physarum_core/output/manager.py`
   - `preview_generator.py` → `physarum-core/physarum_core/preview/generator.py`

4. **Update imports in moved modules**
   - Replace `from physarum import PhysarumSimulation` with `from physarum_core.simulation import PhysarumSimulation`
   - Update all cross-module imports to use the new package structure

### Phase 2: Update Web Backend

1. **Update `web/backend/pyproject.toml`**
   ```toml
   dependencies = [
       "fastapi==0.104.1",
       "uvicorn[standard]==0.24.0",
       "websockets==12.0",
       "python-multipart==0.0.6",
       "pydantic==2.5.0",
       "psutil>=5.9.0",
       "httpx>=0.24.0",
       "physarum-core",  # Local dependency
   ]
   ```

2. **Update backend imports**
   In `web/backend/app/core/simulation_manager.py`:
   ```python
   # Remove sys.path manipulation
   # Replace:
   from physarum import PhysarumSimulation
   from model_3d import Model3DGenerator
   from model_3d_smooth import SmoothModel3DGenerator
   from output_manager import OutputManager
   from preview_generator import PreviewGenerator
   
   # With:
   from physarum_core.simulation import PhysarumSimulation
   from physarum_core.models.model_3d import Model3DGenerator
   from physarum_core.models.model_3d_smooth import SmoothModel3DGenerator
   from physarum_core.output.manager import OutputManager
   from physarum_core.preview.generator import PreviewGenerator
   ```

### Phase 3: Create CLI Package (Optional)

1. **Create `cli/pyproject.toml`**
   ```toml
   [project]
   name = "physarum-cli"
   version = "1.0.0"
   description = "Command-line tools for 3D Physarum model generation"
   requires-python = ">=3.9"
   dependencies = [
       "physarum-core",
       "click>=8.0.0",  # For CLI interface
   ]
   ```

2. **Move CLI scripts**
   - `main.py` → `cli/main.py`
   - `demo_3d.py` → `cli/demo_3d.py`

### Phase 4: Update Development Workflow

1. **Install packages in development mode**
   ```bash
   # Install core package in development mode
   cd physarum-core
   uv pip install -e .
   
   # Install backend with core dependency
   cd ../web/backend
   uv pip install -e .
   
   # Install CLI tools (if created)
   cd ../../cli
   uv pip install -e .
   ```

2. **Update test structure**
   - Move tests to respective packages
   - Root tests → `physarum-core/tests/`
   - Backend tests remain in `web/backend/tests/`

## Benefits of This Structure

### 1. **Clean Dependency Management**
- No more `sys.path` manipulation
- Clear separation of dependencies
- Proper dependency resolution

### 2. **Better Development Experience**
- IDE autocomplete and navigation work properly
- Type checking works across packages
- Clear import paths

### 3. **Easier Testing**
- Each package can be tested independently
- No more path-related test issues
- Better test isolation

### 4. **Deployment Flexibility**
- Core simulation engine can be deployed separately
- Web backend is lightweight
- Easy to containerize individual components

### 5. **Version Management**
- Core simulation logic can be versioned independently
- Breaking changes in core don't immediately break web backend
- Easier to maintain backward compatibility

## Migration Checklist

- [ ] Create `physarum-core` package structure
- [ ] Move and refactor core modules
- [ ] Update imports in core modules
- [ ] Create comprehensive tests for core package
- [ ] Update web backend dependencies
- [ ] Update web backend imports
- [ ] Remove `sys.path` manipulation from backend
- [ ] Test web backend with new structure
- [ ] Create CLI package (optional)
- [ ] Update documentation
- [ ] Update CI/CD pipelines (if any)

## Rollback Plan

If issues arise during migration:
1. Keep the current structure until migration is complete
2. Use feature branches for migration work
3. Test thoroughly before switching default branch
4. Keep backup of current working state

## Timeline Estimate

- **Phase 1**: 2-3 hours (create structure, move files)
- **Phase 2**: 1-2 hours (update backend)
- **Phase 3**: 1 hour (CLI package, optional)
- **Phase 4**: 1 hour (development setup)
- **Testing**: 2-3 hours (thorough testing)

**Total**: 7-10 hours of development time

## Notes

- This restructuring will make the project more maintainable and professional
- The new structure follows Python packaging best practices
- Each package can have its own release cycle
- Better separation of concerns between simulation engine and web interface
- Easier for new developers to understand the codebase structure