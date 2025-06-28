# ABOUTME: Comprehensive Docker deployment test for physarum_core imports and simulation functionality
# ABOUTME: This test verifies that all components work correctly in the Docker environment

"""
Comprehensive test to verify Docker deployment of the 3D Physarum application.
This test catches common issues with module imports, permissions, and simulation execution.
"""

import subprocess
import sys
import time
import json

def run_docker_command(cmd):
    """Run a docker command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result

def test_physarum_imports():
    """Test that all physarum_core submodules can be imported in Docker."""
    print("🧪 Testing physarum_core imports in Docker...")
    
    cmd = '''docker run --rm physarum-test-fixed sh -c "cd /app/web/backend && uv run python -c \\"
import sys
try:
    import physarum_core
    print('✓ physarum_core import successful')
except ImportError as e:
    print(f'✗ physarum_core import failed: {e}')
    sys.exit(1)

try:
    from physarum_core.output import OutputManager
    print('✓ physarum_core.output import successful')
except ImportError as e:
    print(f'✗ physarum_core.output import failed: {e}')
    sys.exit(1)

try:
    from physarum_core.simulation import PhysarumSimulation
    print('✓ physarum_core.simulation import successful')
except ImportError as e:
    print(f'✗ physarum_core.simulation import failed: {e}')
    sys.exit(1)

try:
    from physarum_core.models.model_3d import Model3DGenerator
    print('✓ physarum_core.models import successful')
except ImportError as e:
    print(f'✗ physarum_core.models import failed: {e}')
    sys.exit(1)

try:
    from physarum_core.preview.generator import PreviewGenerator
    print('✓ physarum_core.preview import successful')
except ImportError as e:
    print(f'✗ physarum_core.preview import failed: {e}')
    sys.exit(1)

print('🎉 All imports successful!')
\\""'''
    
    result = run_docker_command(cmd)
    if result.returncode != 0:
        print(f"❌ Import test failed: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def test_file_permissions():
    """Test that file permissions are set correctly."""
    print("🧪 Testing file permissions in Docker...")
    
    cmd = '''docker run --rm physarum-test-fixed sh -c "
    echo 'Checking directory permissions:'
    ls -la /app/physarum-core/physarum_core/ | head -5
    echo ''
    echo 'Checking file permissions in output directory:'
    ls -la /app/physarum-core/physarum_core/output/
    "'''
    
    result = run_docker_command(cmd)
    if result.returncode != 0:
        print(f"❌ Permission test failed: {result.stderr}")
        return False
    
    output = result.stdout
    print(output)
    
    # Check if permissions look correct (readable by all)
    if "r--r--r--" in output or "rwxr-xr-x" in output:
        print("✅ File permissions appear correct")
        return True
    else:
        print("❌ File permissions may be incorrect")
        return False

def test_simulation_execution():
    """Test that a simulation can be executed successfully."""
    print("🧪 Testing simulation execution...")
    
    # Start container
    start_cmd = "docker run --rm -d -p 8003:8000 --name physarum-test-sim physarum-test-fixed"
    result = run_docker_command(start_cmd)
    if result.returncode != 0:
        print(f"❌ Failed to start container: {result.stderr}")
        return False
    
    try:
        # Wait for container to start
        time.sleep(5)
        
        # Start simulation using curl
        curl_cmd = '''curl -s -X POST "http://localhost:8003/api/simulate" -H "Content-Type: application/json" -d '{"parameters": {"width": 30, "height": 30, "actors": 10, "steps": 20}}' '''
        result = run_docker_command(curl_cmd)
        
        if result.returncode != 0:
            print(f"❌ Failed to start simulation: {result.stderr}")
            return False
        
        try:
            job_data = json.loads(result.stdout)
            job_id = job_data["job_id"]
            print(f"✅ Simulation started with job ID: {job_id}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Failed to parse simulation response: {e}")
            print(f"Response: {result.stdout}")
            return False
        
        # Wait for completion and check status
        max_wait = 30
        for i in range(max_wait):
            status_cmd = f'curl -s "http://localhost:8003/api/simulate/{job_id}/status"'
            status_result = run_docker_command(status_cmd)
            
            if status_result.returncode == 0:
                try:
                    status_data = json.loads(status_result.stdout)
                    if status_data["status"] == "completed":
                        print("✅ Simulation completed successfully")
                        return True
                    elif status_data["status"] == "failed":
                        print(f"❌ Simulation failed: {status_data.get('error_message', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    pass  # Continue waiting
            
            time.sleep(1)
        
        print("❌ Simulation timed out")
        return False
        
    except Exception as e:
        print(f"❌ Simulation test failed with exception: {e}")
        return False
        
    finally:
        # Clean up container
        run_docker_command("docker stop physarum-test-sim 2>/dev/null || true")

def main():
    """Run all tests."""
    print("🚀 Starting comprehensive Docker deployment tests...\n")
    
    tests = [
        ("Import Tests", test_physarum_imports),
        ("Permission Tests", test_file_permissions),
        ("Simulation Execution", test_simulation_execution)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        success = test_func()
        results.append((test_name, success))
        print(f"{'✅ PASSED' if success else '❌ FAILED'}: {test_name}\n")
    
    # Summary
    print("=" * 50)
    print("TEST SUMMARY:")
    print("=" * 50)
    
    all_passed = True
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Docker deployment is working correctly!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please check the Docker configuration")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)