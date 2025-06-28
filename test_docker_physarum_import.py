# ABOUTME: Test script to verify physarum_core imports work correctly in Docker
# ABOUTME: This test is designed to catch missing submodule issues during Docker builds

"""
Test to reproduce and verify physarum_core import issues in Docker.
This test should fail if the Docker build doesn't copy all required subdirectories.
"""

def test_physarum_core_imports():
    """Test that all physarum_core submodules can be imported successfully."""
    
    # Test basic physarum_core import
    try:
        import physarum_core
        print("✓ physarum_core basic import successful")
    except ImportError as e:
        print(f"✗ physarum_core basic import failed: {e}")
        return False
    
    # Test physarum_core.output import (this is where the error occurs)
    try:
        from physarum_core.output import OutputManager
        print("✓ physarum_core.output.OutputManager import successful")
    except ImportError as e:
        print(f"✗ physarum_core.output.OutputManager import failed: {e}")
        return False
    
    # Test physarum_core.models import
    try:
        from physarum_core.models.model_3d import Model3D
        print("✓ physarum_core.models.model_3d.Model3D import successful")
    except ImportError as e:
        print(f"✗ physarum_core.models.model_3d.Model3D import failed: {e}")
        return False
    
    # Test physarum_core.preview import
    try:
        from physarum_core.preview.generator import PreviewGenerator
        print("✓ physarum_core.preview.generator.PreviewGenerator import successful")
    except ImportError as e:
        print(f"✗ physarum_core.preview.generator.PreviewGenerator import failed: {e}")
        return False
    
    # Test physarum_core.simulation import
    try:
        from physarum_core.simulation import PhysarumSimulation
        print("✓ physarum_core.simulation.PhysarumSimulation import successful")
    except ImportError as e:
        print(f"✗ physarum_core.simulation.PhysarumSimulation import failed: {e}")
        return False
    
    print("✓ All physarum_core imports successful!")
    return True

if __name__ == "__main__":
    success = test_physarum_core_imports()
    exit(0 if success else 1)