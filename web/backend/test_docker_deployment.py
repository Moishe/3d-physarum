# ABOUTME: Comprehensive test script for Docker container deployment verification
# ABOUTME: Tests health, API endpoints, and core functionality of the containerized backend

import requests
import time
import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional
import tempfile

class DockerDeploymentTester:
    def __init__(self, container_name: str = "physarum-test", port: int = 8001):
        self.container_name = container_name
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.container_id = None
        
    def build_image(self) -> bool:
        """Build the Docker image."""
        print("🔨 Building Docker image...")
        try:
            result = subprocess.run(
                ["docker", "build", "-t", "physarum-backend", "."],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                print(f"❌ Build failed: {result.stderr}")
                return False
            print("✅ Docker image built successfully")
            return True
        except subprocess.TimeoutExpired:
            print("❌ Build timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def start_container(self) -> bool:
        """Start the Docker container."""
        print(f"🚀 Starting container on port {self.port}...")
        try:
            # Stop and remove existing container if it exists
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
            
            # Start new container
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
            
            # Wait for container to be ready
            print("⏳ Waiting for container to be ready...")
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"❌ Container start error: {e}")
            return False
    
    def stop_container(self):
        """Stop and clean up the container."""
        if self.container_name:
            print("🛑 Stopping container...")
            subprocess.run(["docker", "stop", self.container_name], capture_output=True)
            subprocess.run(["docker", "rm", self.container_name], capture_output=True)
    
    def get_container_logs(self) -> str:
        """Get container logs for debugging."""
        try:
            result = subprocess.run([
                "docker", "logs", self.container_name
            ], capture_output=True, text=True)
            return result.stdout + result.stderr
        except Exception:
            return "Could not retrieve logs"
    
    def test_health_endpoint(self) -> bool:
        """Test the /health endpoint."""
        print("🏥 Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Health check passed")
                    return True
                else:
                    print(f"❌ Health check failed: {data}")
                    return False
            else:
                print(f"❌ Health endpoint returned {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check connection failed: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test basic API endpoint availability."""
        print("🔌 Testing API endpoints...")
        
        endpoints = [
            ("/health", "GET"),
            ("/docs", "GET"),  # FastAPI docs
            ("/api/models", "GET"),  # Models endpoint
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    continue  # Skip non-GET for now
                
                if response.status_code in [200, 422]:  # 422 is OK for some endpoints without params
                    print(f"✅ {endpoint} responded ({response.status_code})")
                else:
                    print(f"❌ {endpoint} failed ({response.status_code})")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ {endpoint} connection failed: {e}")
                return False
        
        return True
    
    def test_cors_headers(self) -> bool:
        """Test CORS headers are properly configured."""
        print("🌐 Testing CORS configuration...")
        try:
            response = requests.options(f"{self.base_url}/health", headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }, timeout=10)
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            }
            
            if cors_headers["Access-Control-Allow-Origin"]:
                print("✅ CORS headers present")
                return True
            else:
                print("❌ CORS headers missing")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ CORS test failed: {e}")
            return False
    
    def test_simulation_endpoint_basic(self) -> bool:
        """Test simulation endpoint accepts requests (without actually running simulation)."""
        print("⚡ Testing simulation endpoint...")
        try:
            # Test with minimal valid parameters
            test_data = {
                "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "parameters": {
                    "num_agents": 100,
                    "num_iterations": 10,
                    "diffusion_rate": 0.1,
                    "evaporation_rate": 0.1
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/simulation/run", 
                json=test_data,
                timeout=30
            )
            
            # We expect this to either start processing (200/202) or give validation error (422)
            if response.status_code in [200, 202, 422]:
                print("✅ Simulation endpoint accepts requests")
                return True
            else:
                print(f"❌ Simulation endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Simulation endpoint test failed: {e}")
            return False
    
    def test_models_endpoint(self) -> bool:
        """Test models listing endpoint."""
        print("📋 Testing models endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/models", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Models endpoint returned {len(data)} models")
                return True
            else:
                print(f"❌ Models endpoint failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Models endpoint test failed: {e}")
            return False
    
    def test_websocket_endpoint(self) -> bool:
        """Test WebSocket endpoint is available."""
        print("🔌 Testing WebSocket endpoint availability...")
        # Note: This is a basic test - we're not testing actual WebSocket functionality
        # Just checking that the endpoint doesn't return a 404
        try:
            response = requests.get(f"{self.base_url}/ws/test-job-id", timeout=5)
            # WebSocket endpoints typically return 426 (Upgrade Required) for HTTP requests
            if response.status_code in [426, 400]:
                print("✅ WebSocket endpoint is available")
                return True
            else:
                print(f"❌ WebSocket endpoint unexpected response: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ WebSocket endpoint test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        print("🧪 Starting Docker deployment tests...\n")
        
        tests = [
            ("Build Image", self.build_image),
            ("Start Container", self.start_container),
            ("Health Check", self.test_health_endpoint),
            ("API Endpoints", self.test_api_endpoints),
            ("CORS Headers", self.test_cors_headers),
            ("Models Endpoint", self.test_models_endpoint),
            ("Simulation Endpoint", self.test_simulation_endpoint_basic),
            ("WebSocket Endpoint", self.test_websocket_endpoint),
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
                    print("📋 Container logs:")
                    print(self.get_container_logs())
                    break
                    
        finally:
            self.stop_container()
        
        print(f"\n{'='*50}")
        print(f"🧪 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Docker deployment tests PASSED!")
            print("✅ Backend is ready for Railway deployment")
            return True
        else:
            print("❌ Some tests FAILED!")
            print("🔧 Fix issues before deploying to Railway")
            return False

def main():
    """Main entry point."""
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    tester = DockerDeploymentTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()