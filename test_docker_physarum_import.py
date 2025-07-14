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
        assert False, f"physarum_core basic import failed: {e}"
    
    # Test physarum_core.output import (this is where the error occurs)
    try:
        from physarum_core.output import OutputManager
        print("✓ physarum_core.output.OutputManager import successful")
    except ImportError as e:
        print(f"✗ physarum_core.output.OutputManager import failed: {e}")
        assert False, f"physarum_core.output.OutputManager import failed: {e}"
    
    # Test physarum_core.models import
    try:
        from physarum_core.models.model_3d import Model3DGenerator
        print("✓ physarum_core.models.model_3d.Model3DGenerator import successful")
    except ImportError as e:
        print(f"✗ physarum_core.models.model_3d.Model3DGenerator import failed: {e}")
        assert False, f"physarum_core.models.model_3d.Model3DGenerator import failed: {e}"
    
    # Test physarum_core.preview import
    try:
        from physarum_core.preview.generator import PreviewGenerator
        print("✓ physarum_core.preview.generator.PreviewGenerator import successful")
    except ImportError as e:
        print(f"✗ physarum_core.preview.generator.PreviewGenerator import failed: {e}")
        assert False, f"physarum_core.preview.generator.PreviewGenerator import failed: {e}"
    
    # Test physarum_core.simulation import
    try:
        from physarum_core.simulation import PhysarumSimulation
        print("✓ physarum_core.simulation.PhysarumSimulation import successful")
    except ImportError as e:
        print(f"✗ physarum_core.simulation.PhysarumSimulation import failed: {e}")
        assert False, f"physarum_core.simulation.PhysarumSimulation import failed: {e}"
    
    print("✓ All physarum_core imports successful!")

if __name__ == "__main__":
    try:
        test_physarum_core_imports()
        exit(0)
    except Exception:
        exit(1)