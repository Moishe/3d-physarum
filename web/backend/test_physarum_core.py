# ABOUTME: Test script to verify physarum_core functionality within Docker container
# ABOUTME: Tests core simulation and model generation capabilities in containerized environment

import subprocess
import tempfile
import json
import base64
from PIL import Image
import os

def create_test_image() -> str:
    """Create a simple test image and return as base64."""
    # Create a simple 32x32 white image with a black dot
    img = Image.new('RGB', (32, 32), color='white')
    pixels = img.load()
    
    # Add a small black circle in the center
    center = 16
    for x in range(32):
        for y in range(32):
            if (x - center) ** 2 + (y - center) ** 2 <= 25:  # Small circle
                pixels[x, y] = (0, 0, 0)  # Black
    
    # Save to temporary file and encode as base64
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name, 'PNG')
        with open(tmp.name, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(tmp.name)
    
    return f"data:image/png;base64,{img_data}"

def test_physarum_core_in_container():
    """Test physarum_core functionality inside a running container."""
    print("🧬 Testing physarum_core functionality in container...")
    
    # Create test script that will run inside the container
    test_script = '''
import sys
sys.path.append('/app')

try:
    # Test basic imports
    from physarum_core.simulation import PhysarumSimulation
    from physarum_core.models.model_3d import Model3D
    from physarum_core.preview.generator import PreviewGenerator
    print("✅ Core imports successful")
    
    # Test simulation creation
    sim = PhysarumSimulation(
        width=32, height=32,
        num_agents=50,
        num_iterations=5
    )
    print("✅ Simulation object created")
    
    # Test model creation
    model = Model3D()
    print("✅ Model3D object created")
    
    # Test preview generator
    preview = PreviewGenerator()
    print("✅ PreviewGenerator created")
    
    print("🎉 All physarum_core tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Core test error: {e}")
    sys.exit(1)
'''
    
    try:
        # Write test script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(test_script)
            tmp_path = tmp.name
        
        # Copy test script into container and run it
        container_name = "physarum-test"
        
        # Copy file to container
        copy_cmd = ["docker", "cp", tmp_path, f"{container_name}:/app/test_core.py"]
        subprocess.run(copy_cmd, check=True, capture_output=True)
        
        # Run test inside container
        exec_cmd = ["docker", "exec", container_name, "python", "/app/test_core.py"]
        result = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=30)
        
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
            
        # Cleanup
        os.unlink(tmp_path)
        
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Container exec failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Core test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_physarum_core_in_container()
    exit(0 if success else 1)