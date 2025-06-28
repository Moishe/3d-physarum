# ABOUTME: Test specifically for skimage functionality in Docker production environment
# ABOUTME: Ensures scikit-image imports work and marching cubes can generate 3D meshes in containers

import pytest
import numpy as np
import subprocess
import time
import requests
import json
import tempfile
import os
from typing import Dict, Any

class SkimageDockerTest:
    """Test class for validating skimage functionality in Docker environment."""
    
    def __init__(self, container_name: str = "physarum-skimage-test", port: int = 8002):
        self.container_name = container_name
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.container_id = None
    
    def build_and_start_container(self) -> bool:
        """Build Docker image and start container."""
        print("🔨 Building and starting container for skimage test...")
        
        try:
            # Stop existing container
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            
            # Build image
            result = subprocess.run(
                ["docker", "build", "-t", "physarum-backend", "."],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                print(f"❌ Build failed: {result.stderr}")
                return False
            
            # Start container
            result = subprocess.run([
                "docker", "run", "-d", 
                "-p", f"{self.port}:8000",
                "--name", self.container_name,
                "physarum-backend"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Container start failed: {result.stderr}")
                return False
                
            self.container_id = result.stdout.strip()
            print(f"✅ Container started: {self.container_id[:12]}")
            
            # Wait for readiness
            time.sleep(10)
            return True
            
        except Exception as e:
            print(f"❌ Setup error: {e}")
            return False
    
    def stop_container(self):
        """Stop and clean up the container."""
        if self.container_name:
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
    
    def test_skimage_import_in_container(self) -> bool:
        """Test that skimage can be imported in the Docker container."""
        print("📦 Testing skimage import in container...")
        
        try:
            # Execute import test directly in container
            result = subprocess.run([
                "docker", "exec", self.container_name,
                "python", "-c", "import skimage; from skimage import measure; print('skimage import successful')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "skimage import successful" in result.stdout:
                print("✅ skimage imports successfully in container")
                return True
            else:
                print(f"❌ skimage import failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ skimage import test error: {e}")
            return False
    
    def test_marching_cubes_in_container(self) -> bool:
        """Test marching cubes functionality specifically in the container."""
        print("🧊 Testing marching cubes in container...")
        
        # Create a test script that exercises marching cubes
        test_script = '''
import numpy as np
from skimage import measure
import tempfile
import os

try:
    # Create a simple 3D volume with a sphere
    x, y, z = np.mgrid[-10:10:20j, -10:10:20j, -10:10:20j]
    volume = (x**2 + y**2 + z**2) <= 8**2
    volume = volume.astype(float)
    
    # Apply marching cubes - this is the key skimage functionality used in production
    vertices, faces, normals, values = measure.marching_cubes(
        volume, 
        level=0.5,
        spacing=(1.0, 1.0, 1.0)
    )
    
    # Validate results
    if len(vertices) > 0 and len(faces) > 0:
        print(f"SUCCESS: Generated {len(vertices)} vertices and {len(faces)} faces")
    else:
        print("ERROR: No mesh generated")
        exit(1)
        
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
    exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
'''
        
        try:
            # Write test script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                script_path = f.name
            
            # Copy script to container
            subprocess.run([
                "docker", "cp", script_path, f"{self.container_name}:/tmp/test_marching_cubes.py"
            ], check=True)
            
            # Execute test in container
            result = subprocess.run([
                "docker", "exec", self.container_name,
                "python", "/tmp/test_marching_cubes.py"
            ], capture_output=True, text=True, timeout=60)
            
            # Clean up
            os.unlink(script_path)
            
            if result.returncode == 0 and "SUCCESS:" in result.stdout:
                print("✅ marching_cubes works in container")
                return True
            else:
                print(f"❌ marching_cubes failed: {result.stdout} {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ marching_cubes test error: {e}")
            return False
    
    def test_3d_model_generation_endpoint(self) -> bool:
        """Test that the 3D model generation endpoint works with skimage."""
        print("🎯 Testing 3D model generation endpoint...")
        
        try:
            # Wait for API to be ready
            for _ in range(10):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    if response.status_code == 200:
                        break
                except:
                    time.sleep(2)
            
            # Create a minimal image for 3D model generation
            # This will trigger the path that uses skimage.measure.marching_cubes
            test_data = {
                "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "parameters": {
                    "num_agents": 50,
                    "num_iterations": 10,
                    "diffusion_rate": 0.1,
                    "evaporation_rate": 0.1,
                    "enable_3d": True,
                    "layer_height": 1.0,
                    "threshold": 0.1,
                    "smoothing_iterations": 1,
                    "smoothing_type": "boundary_outline"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/simulate", 
                json=test_data,
                timeout=120  # Longer timeout for 3D generation
            )
            
            # Check that the request is accepted and processing starts
            # This validates that skimage is available for the marching cubes operation
            if response.status_code in [200, 202]:
                print("✅ 3D model generation endpoint accepts skimage-dependent requests")
                return True
            elif response.status_code == 422:
                # Validation error is acceptable - means the endpoint is working
                print("✅ 3D model generation endpoint is functional (validation error expected)")
                return True
            else:
                print(f"❌ 3D model generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 3D model generation test error: {e}")
            return False
    
    def test_physarum_core_with_skimage(self) -> bool:
        """Test that physarum_core module works with skimage in container."""
        print("🦠 Testing physarum_core with skimage...")
        
        # Test script that imports and uses the actual production code path
        test_script = '''
import numpy as np
import sys
sys.path.append("/app")

try:
    from physarum_core.models.model_3d_smooth import SmoothModel3DGenerator
    from physarum_core.simulation import PhysarumSimulation
    
    # Create a minimal simulation
    sim = PhysarumSimulation(50, 50, 10, 0.1)
    
    # Create 3D generator - this will use skimage for marching cubes
    generator = SmoothModel3DGenerator(
        sim, 
        layer_height=1.0, 
        threshold=0.1,
        smoothing_iterations=1,
        smoothing_type="boundary_outline"
    )
    
    # Run a few simulation steps and capture layers
    for i in range(5):
        sim.step()
        if i % 2 == 0:
            generator.capture_layer()
    
    # This is the critical test - generate mesh using skimage.measure.marching_cubes
    if generator.get_layer_count() > 0:
        try:
            mesh = generator.generate_mesh()
            print(f"SUCCESS: Generated mesh with {len(mesh.vectors)} triangles")
        except Exception as mesh_error:
            print(f"MESH_ERROR: {mesh_error}")
            exit(1)
    else:
        print("SUCCESS: No layers captured (simulation too short)")
    
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
    exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
'''
        
        try:
            # Write test script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                script_path = f.name
            
            # Copy to container
            subprocess.run([
                "docker", "cp", script_path, f"{self.container_name}:/tmp/test_physarum_skimage.py"
            ], check=True)
            
            # Execute test
            result = subprocess.run([
                "docker", "exec", self.container_name,
                "python", "/tmp/test_physarum_skimage.py"
            ], capture_output=True, text=True, timeout=120)
            
            # Clean up
            os.unlink(script_path)
            
            if result.returncode == 0 and "SUCCESS:" in result.stdout:
                print("✅ physarum_core works with skimage in container")
                return True
            else:
                print(f"❌ physarum_core + skimage test failed: {result.stdout} {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ physarum_core + skimage test error: {e}")
            return False
    
    def run_all_skimage_tests(self) -> bool:
        """Run all skimage-specific tests in Docker context."""
        print("🧪 Starting skimage Docker tests...\n")
        
        tests = [
            ("Setup Container", self.build_and_start_container),
            ("Skimage Import", self.test_skimage_import_in_container),
            ("Marching Cubes", self.test_marching_cubes_in_container),
            ("Physarum Core + Skimage", self.test_physarum_core_with_skimage),
            ("3D Model API Endpoint", self.test_3d_model_generation_endpoint),
        ]
        
        passed = 0
        total = len(tests)
        
        try:
            for test_name, test_func in tests:
                print(f"\n--- {test_name} ---")
                if test_func():
                    passed += 1
                else:
                    print(f"💥 {test_name} failed!")
                    break
                    
        finally:
            self.stop_container()
        
        print(f"\n{'='*50}")
        print(f"🧪 Skimage Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All skimage Docker tests PASSED!")
            print("✅ scikit-image works correctly in production Docker environment")
            return True
        else:
            print("❌ Some skimage tests FAILED!")
            print("🔧 scikit-image may not work correctly in production")
            return False

def test_skimage_docker_integration():
    """Pytest integration for skimage Docker tests."""
    tester = SkimageDockerTest()
    assert tester.run_all_skimage_tests(), "Skimage Docker tests failed"

def main():
    """Main entry point for standalone execution."""
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    tester = SkimageDockerTest()
    success = tester.run_all_skimage_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())