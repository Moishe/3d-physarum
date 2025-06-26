# ABOUTME: Comprehensive API endpoint tests to ensure all imports work correctly
# ABOUTME: Tests exercise all code paths that depend on external libraries

import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import WebSocket
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from app.main import app
from app.models.simulation import SimulationRequest, SimulationParameters, SimulationStatus
from app.core.simulation_manager import SimulationJob


class TestAPIEndpoints:
    """Test suite for all API endpoints to verify imports and functionality."""

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        return TestClient(app)

    @pytest.fixture
    def sample_simulation_request(self):
        """Sample simulation request for testing."""
        return SimulationRequest(
            parameters=SimulationParameters(
                steps=100,
                actors=50,
                width=256,
                height=256,
                smooth=True,
                decay_rate=0.95,
                diffusion_rate=0.1,
                sensor_angle=45,
                sensor_distance=9,
                rotation_angle=45,
                step_size=1,
                seed=42
            )
        )

    @pytest.fixture
    def mock_simulation_job(self):
        """Mock simulation job for testing."""
        job = Mock(spec=SimulationJob)
        job.job_id = "test-job-123"
        job.status = SimulationStatus.completed
        job.progress = {"step": 100, "total_steps": 100, "message": "Complete"}
        job.error_message = None
        job.started_at = 1234567890.0
        job.completed_at = 1234567900.0
        job.parameters = {
            "steps": 100,
            "actors": 50,
            "width": 256,
            "height": 256
        }
        job.result_files = {
            "stl": "/tmp/test.stl",
            "json": "/tmp/test.json",
            "jpg": "/tmp/test.jpg"
        }
        job.statistics = {"total_actors": 50, "simulation_time": 10.0}
        job.mesh_quality = {"vertices": 1000, "faces": 2000}
        job.file_sizes = {"stl": 1024, "json": 512, "jpg": 2048}
        job.cancel_requested = False
        return job

    def test_health_endpoint(self, client):
        """Test health check endpoint - exercises fastapi imports."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "3d-physarum-api"

    @patch('app.api.routes.simulation.simulation_manager')
    @patch('app.api.routes.simulation.ParameterAdapter')
    def test_start_simulation_endpoint(self, mock_adapter, mock_manager, client, sample_simulation_request):
        """Test simulation start endpoint - exercises pydantic, fastapi, and simulation imports."""
        # Mock parameter validation
        mock_adapter.validate_web_parameters.return_value = []
        mock_adapter.estimate_complexity.return_value = {
            "complexity_level": "medium",
            "estimated_runtime_seconds": 30.0
        }
        
        # Mock simulation manager
        mock_manager.start_simulation.return_value = "test-job-123"
        
        response = client.post("/api/simulate", json=sample_simulation_request.dict())
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "pending"
        assert "complexity" in data["message"]

    @patch('app.api.routes.simulation.simulation_manager')
    @patch('app.api.routes.simulation.psutil')
    def test_get_simulation_status_endpoint(self, mock_psutil, mock_manager, client, mock_simulation_job):
        """Test simulation status endpoint - exercises psutil and simulation manager imports."""
        # Mock psutil calls
        mock_memory = Mock()
        mock_memory.total = 8 * 1024**3  # 8GB
        mock_memory.available = 4 * 1024**3  # 4GB
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 25.0
        
        mock_disk = Mock()
        mock_disk.free = 100 * 1024**3  # 100GB
        mock_disk.total = 500 * 1024**3  # 500GB
        mock_disk.used = 400 * 1024**3   # 400GB
        mock_psutil.disk_usage.return_value = mock_disk
        
        mock_process = Mock()
        mock_process_memory = Mock()
        mock_process_memory.rss = 100 * 1024**2  # 100MB
        mock_process_memory.vms = 200 * 1024**2  # 200MB
        mock_process.memory_info.return_value = mock_process_memory
        mock_process.pid = 1234
        mock_process.num_threads.return_value = 8
        mock_psutil.Process.return_value = mock_process
        
        # Mock simulation manager
        mock_manager.get_job_status.return_value = mock_simulation_job
        mock_manager.get_job_statistics.return_value = {
            "total_jobs": 5,
            "active_jobs": 1,
            "max_concurrent_jobs": 3,
            "status_counts": {"pending": 1, "running": 0, "completed": 4}
        }
        mock_manager.jobs = {"test-job-123": mock_simulation_job}
        
        response = client.get("/api/simulate/test-job-123/status")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "completed"
        assert "progress" in data

    @patch('app.api.routes.simulation.simulation_manager')
    def test_get_simulation_result_endpoint(self, mock_manager, client, mock_simulation_job):
        """Test simulation result endpoint - exercises result serialization."""
        mock_manager.get_job_status.return_value = mock_simulation_job
        
        response = client.get("/api/simulate/test-job-123/result")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert data["status"] == "completed"
        assert "files" in data
        assert "statistics" in data
        assert "mesh_quality" in data

    @patch('app.api.routes.simulation.simulation_manager')
    @patch('app.api.routes.simulation.os.path.exists')
    def test_get_simulation_preview_endpoint(self, mock_exists, mock_manager, client, mock_simulation_job):
        """Test simulation preview endpoint - exercises file response and os imports."""
        mock_manager.get_job_status.return_value = mock_simulation_job
        mock_exists.return_value = True
        
        # Create a temporary file to serve
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(b"fake image data")
            mock_simulation_job.result_files["jpg"] = tmp_file.name
            
            response = client.get("/api/simulate/test-job-123/preview")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"
            
            # Clean up
            os.unlink(tmp_file.name)

    @patch('app.api.routes.simulation.simulation_manager')
    def test_cancel_simulation_endpoint(self, mock_manager, client):
        """Test simulation cancellation endpoint."""
        mock_manager.cancel_job.return_value = True
        
        response = client.delete("/api/simulate/test-job-123")
        assert response.status_code == 200
        data = response.json()
        assert "Cancellation requested" in data["message"]

    @patch('app.api.routes.simulation.simulation_manager')
    @patch('app.api.routes.simulation.os.path.exists')
    def test_download_simulation_file_endpoint(self, mock_exists, mock_manager, client, mock_simulation_job):
        """Test file download endpoint - exercises file response and os imports."""
        mock_manager.get_job_status.return_value = mock_simulation_job
        mock_exists.return_value = True
        
        # Create temporary files for each file type
        file_types = ["stl", "json", "jpg"]
        temp_files = {}
        
        try:
            for file_type in file_types:
                with tempfile.NamedTemporaryFile(suffix=f'.{file_type}', delete=False) as tmp_file:
                    tmp_file.write(f"fake {file_type} data".encode())
                    temp_files[file_type] = tmp_file.name
                    mock_simulation_job.result_files[file_type] = tmp_file.name
            
            # Test each file type download
            for file_type in file_types:
                response = client.get(f"/api/simulate/test-job-123/download/{file_type}")
                assert response.status_code == 200
                
                # Verify content type
                if file_type == "stl":
                    assert response.headers["content-type"] == "application/octet-stream"
                elif file_type == "json":
                    assert response.headers["content-type"] == "application/json"
                elif file_type == "jpg":
                    assert response.headers["content-type"] == "image/jpeg"
        
        finally:
            # Clean up temporary files
            for file_path in temp_files.values():
                if os.path.exists(file_path):
                    os.unlink(file_path)

    @patch('app.api.routes.simulation.simulation_manager')
    def test_list_jobs_endpoint(self, mock_manager, client):
        """Test job statistics endpoint."""
        mock_manager.get_job_statistics.return_value = {
            "total_jobs": 10,
            "active_jobs": 2,
            "max_concurrent_jobs": 5,
            "status_counts": {
                "pending": 1,
                "running": 1,
                "completed": 7,
                "failed": 1
            }
        }
        
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total_jobs"] == 10

    @patch('app.api.routes.simulation.simulation_manager')
    def test_cleanup_old_jobs_endpoint(self, mock_manager, client):
        """Test job cleanup endpoint."""
        mock_manager.cleanup_completed_jobs.return_value = None
        
        response = client.post("/api/jobs/cleanup?max_age_hours=48")
        assert response.status_code == 200
        data = response.json()
        assert "Cleanup completed" in data["message"]
        assert "48 hours" in data["message"]

    def test_websocket_endpoint(self, client):
        """Test WebSocket endpoint - exercises websocket imports."""
        # Note: This test requires a running event loop for WebSocket testing
        # For now, we test that the endpoint exists and imports work
        with client.websocket_connect("/ws/test-job-123") as websocket:
            # The connection should be established
            # The actual WebSocket functionality would be tested in integration tests
            pass

    @patch('app.api.routes.simulation.simulation_manager')
    def test_error_handling_with_debug_context(self, mock_manager, client):
        """Test error handling and debug context generation - exercises psutil in error paths."""
        # Mock simulation manager to raise an exception
        mock_manager.get_job_status.side_effect = Exception("Test exception")
        
        response = client.get("/api/simulate/nonexistent-job/status")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal server error"
        assert "Failed to get simulation status" in data["message"]
        assert data["error_type"] == "Exception"

    def test_parameter_validation_imports(self, client):
        """Test parameter validation - exercises pydantic validation imports."""
        invalid_request = {
            "parameters": {
                "steps": -1,  # Invalid: negative steps
                "actors": 0,   # Invalid: zero actors
                "width": 0,    # Invalid: zero width
                "height": 0    # Invalid: zero height
            }
        }
        
        response = client.post("/api/simulate", json=invalid_request)
        # Should get validation error (422 for pydantic validation or 400 for custom validation)
        assert response.status_code in [400, 422]

    @patch('app.api.routes.simulation.simulation_manager')
    def test_job_not_found_scenarios(self, mock_manager, client):
        """Test job not found scenarios - exercises error handling paths."""
        mock_manager.get_job_status.return_value = None
        
        # Test various endpoints with non-existent job
        endpoints = [
            "/api/simulate/nonexistent/status",
            "/api/simulate/nonexistent/result",
            "/api/simulate/nonexistent/preview"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "Job not found"

    def test_global_exception_handler(self, client):
        """Test global exception handler - exercises logging and traceback imports."""
        # This test would require triggering an unhandled exception
        # For now, we verify the handler exists by checking it's registered
        from app.main import app
        
        # Check that the global exception handler is registered
        assert hasattr(app, 'exception_handlers')
        assert Exception in app.exception_handlers


class TestImportExercise:
    """Additional tests specifically to exercise imports that might not be covered."""

    def test_numpy_import(self):
        """Test numpy import from simulation manager."""
        from app.core.simulation_manager import simulation_manager
        # This will fail if numpy is not properly installed
        assert hasattr(simulation_manager, 'start_simulation')

    def test_psutil_import(self):
        """Test psutil import from routes."""
        import app.api.routes.simulation as sim_routes
        # This will fail if psutil is not properly installed
        assert hasattr(sim_routes, 'psutil')

    def test_fastapi_imports(self):
        """Test FastAPI imports."""
        from app.main import app
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)

    def test_pydantic_imports(self):
        """Test Pydantic imports."""
        from app.models.simulation import SimulationRequest, SimulationParameters
        from pydantic import BaseModel
        assert issubclass(SimulationRequest, BaseModel)
        assert issubclass(SimulationParameters, BaseModel)

    def test_uvicorn_import(self):
        """Test uvicorn import availability."""
        import uvicorn
        assert hasattr(uvicorn, 'run')

    def test_websockets_import(self):
        """Test websockets import availability."""
        import websockets
        assert hasattr(websockets, 'serve')

    def test_trimesh_import_availability(self):
        """Test that trimesh is available for import."""
        try:
            import trimesh
            assert hasattr(trimesh, 'Trimesh')
        except ImportError:
            pytest.fail("trimesh import failed - missing dependency")

    def test_pillow_import_availability(self):
        """Test that Pillow is available for import."""
        try:
            from PIL import Image
            assert hasattr(Image, 'open')
        except ImportError:
            pytest.fail("Pillow import failed - missing dependency")

    def test_scipy_import_availability(self):
        """Test that scipy is available for import."""
        try:
            import scipy
            assert hasattr(scipy, 'version')
        except ImportError:
            pytest.fail("scipy import failed - missing dependency")

    def test_numpy_stl_import_availability(self):
        """Test that numpy-stl is available for import."""
        try:
            import stl
            assert hasattr(stl, 'mesh')
        except ImportError:
            pytest.fail("numpy-stl import failed - missing dependency")

    def test_scikit_image_import_availability(self):
        """Test that scikit-image is available for import."""
        try:
            from skimage import measure
            assert hasattr(measure, 'marching_cubes')
        except ImportError:
            pytest.fail("scikit-image import failed - missing dependency")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])