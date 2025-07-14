#!/usr/bin/env python3
"""Test script to verify frontend-backend integration."""

import asyncio
import requests
import time
import json
from pathlib import Path
import pytest

# Test parameters for a quick simulation
TEST_PARAMETERS = {
    "parameters": {
        "width": 20,
        "height": 20,
        "actors": 10,
        "steps": 10,
        "decay": 0.1,
        "view_radius": 2,
        "view_distance": 5,
        "speed": 1.0,
        "spawn_speed_randomization": 0.2,
        "initial_diameter": 5.0,
        "death_probability": 0.001,
        "spawn_probability": 0.005,
        "diffusion_rate": 0.0,
        "direction_deviation": 1.57,
        "smooth": False,
        "layer_height": 1.0,
        "threshold": 0.1,
        "layer_frequency": 2,
        "smoothing_iterations": 1,
        "smoothing_type": "taubin",
        "taubin_lambda": 0.5,
        "taubin_mu": -0.52,
        "preserve_features": False,
        "feature_angle": 60.0,
        "mesh_quality": False,
        "background": False,
        "background_depth": 2.0,
        "background_margin": 0.05,
        "background_border": False,
        "border_height": 1.0,
        "border_thickness": 0.5,
        "output": "test_integration.stl"
    }
}

@pytest.mark.skip(reason="Integration test requires running backend service")
def test_backend_api():
    """Test the backend API endpoints."""
    base_url = "http://localhost:8000"
    
    print("Testing backend API...")
    
    try:
        # Test health check
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✓ Backend is running and accessible")
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            pytest.fail(f"Backend health check failed: {response.status_code}")
            
        # Test simulation start
        response = requests.post(
            f"{base_url}/api/simulate",
            json=TEST_PARAMETERS,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✓ Simulation started successfully: {job_id}")
            
            # Test status endpoint
            status_response = requests.get(f"{base_url}/api/simulate/{job_id}/status")
            if status_response.status_code == 200:
                print("✓ Status endpoint working")
                
                # Wait a moment for the simulation to potentially complete
                time.sleep(2)
                
                # Check final status
                final_status = requests.get(f"{base_url}/api/simulate/{job_id}/status")
                if final_status.status_code == 200:
                    status_data = final_status.json()
                    print(f"✓ Final status: {status_data['status']}")
                    
                    if status_data['status'] == 'completed':
                        # Test result endpoint
                        result_response = requests.get(f"{base_url}/api/simulate/{job_id}/result")
                        if result_response.status_code == 200:
                            print("✓ Result endpoint working")
                        else:
                            pytest.fail(f"Result endpoint failed: {result_response.status_code}")
                    else:
                        print(f"✓ Simulation in progress or failed: {status_data['status']}")
                        
            else:
                pytest.fail(f"Status endpoint failed: {status_response.status_code}")
                
        else:
            print(f"✗ Simulation start failed: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                print(f"Error details: {response.json()}")
            pytest.fail(f"Simulation start failed: {response.status_code}")
                
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend - make sure it's running on port 8000")
        pytest.skip("Backend service not available")
    except Exception as e:
        print(f"✗ Backend test failed: {e}")
        pytest.fail(f"Backend test failed: {e}")

@pytest.mark.skip(reason="Integration test requires running frontend service")
def test_frontend():
    """Test that frontend is accessible."""
    print("\nTesting frontend...")
    
    try:
        response = requests.get("http://localhost:5173")
        if response.status_code == 200:
            print("✓ Frontend is accessible")
        else:
            print(f"✗ Frontend returned status: {response.status_code}")
            pytest.fail(f"Frontend returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to frontend - make sure it's running on port 5173")
        pytest.skip("Frontend service not available")
    except Exception as e:
        print(f"✗ Frontend test failed: {e}")
        pytest.fail(f"Frontend test failed: {e}")

if __name__ == "__main__":
    print("Integration Test for Physarum 3D Generator Web Interface")
    print("=" * 60)
    
    backend_ok = test_backend_api()
    frontend_ok = test_frontend()
    
    print("\n" + "=" * 60)
    if backend_ok and frontend_ok:
        print("✓ All tests passed! Frontend-backend integration is working.")
    else:
        print("✗ Some tests failed. Check the services are running:")
        print("  Backend: cd web/backend && uv run uvicorn app.main:app --reload --port 8000")
        print("  Frontend: cd web/frontend && npm run dev")