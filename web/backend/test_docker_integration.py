# ABOUTME: Integration tests for Docker deployment and API endpoints
# ABOUTME: Tests building Docker image, running container, and calling all API endpoints

import pytest
import docker
import requests
import time
import subprocess
import json
import os
import uuid
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DockerTestContext:
    """Manages Docker container lifecycle for testing."""

    def __init__(self):
        self.client = docker.from_env()
        self.container = None
        self.image = None
        self.image_tag = f"physarum-test-{uuid.uuid4().hex[:8]}"
        self.container_name = f"physarum-test-container-{uuid.uuid4().hex[:8]}"
        self.port = 8000
        self.base_url = f"http://localhost:{self.port}"

    def build_image(self) -> bool:
        """Build Docker image from Dockerfile."""
        try:
            logger.info(f"Building Docker image: {self.image_tag}")
            self.image, build_logs = self.client.images.build(
                path="/Users/moishe/src/3d-physarum",
                dockerfile="Dockerfile",
                tag=self.image_tag,
                rm=True,
                forcerm=True
            )

            # Log build output for debugging
            for log in build_logs:
                if 'stream' in log:
                    logger.debug(log['stream'].strip())

            logger.info(f"Successfully built image: {self.image_tag}")
            return True

        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            return False

    def start_container(self) -> bool:
        """Start container from built image."""
        try:
            logger.info(f"Starting container: {self.container_name}")
            self.container = self.client.containers.run(
                self.image_tag,
                detach=True,
                name=self.container_name,
                ports={f"{self.port}/tcp": self.port},
                remove=True
            )

            # Wait for container to be ready
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"Container ready after {i+1} seconds")
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)

            logger.error("Container failed to become ready within 30 seconds")
            return False

        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            return False

    def stop_container(self):
        """Stop and remove container."""
        if self.container:
            try:
                logger.info(f"Stopping container: {self.container_name}")
                self.container.stop(timeout=10)
                self.container = None
            except Exception as e:
                logger.error(f"Failed to stop container: {e}")

    def cleanup(self):
        """Clean up Docker resources."""
        self.stop_container()

        # Remove image
        if self.image:
            try:
                self.client.images.remove(self.image.id, force=True)
                logger.info(f"Removed image: {self.image_tag}")
            except Exception as e:
                logger.error(f"Failed to remove image: {e}")

    def get_container_logs(self) -> str:
        """Get container logs for debugging."""
        if self.container:
            try:
                return self.container.logs().decode('utf-8')
            except Exception as e:
                logger.error(f"Failed to get container logs: {e}")
                return f"Error getting logs: {e}"
        return "No container running"


@pytest.fixture(scope="session")
def docker_context():
    """Fixture that builds and starts Docker container for testing."""
    context = DockerTestContext()

    # Build image
    assert context.build_image(), "Failed to build Docker image"

    # Start container
    assert context.start_container(), "Failed to start Docker container"

    yield context

    # Cleanup
    context.cleanup()


class TestDockerBuild:
    """Test Docker image building."""

    def test_docker_build_succeeds(self, docker_context):
        """Test that Docker image builds successfully."""
        assert docker_context.image is not None
        assert any(tag.startswith(docker_context.image_tag) for tag in docker_context.image.tags)


class TestDockerContainer:
    """Test Docker container functionality."""

    def test_container_starts(self, docker_context):
        """Test that container starts and responds to health check."""
        assert docker_context.container is not None

        response = requests.get(f"{docker_context.base_url}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "3d-physarum-api"

    def test_openapi_docs_available(self, docker_context):
        """Test that OpenAPI documentation is available."""
        response = requests.get(f"{docker_context.base_url}/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_openapi_json_available(self, docker_context):
        """Test that OpenAPI JSON schema is available."""
        response = requests.get(f"{docker_context.base_url}/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestSimulationAPI:
    """Test simulation-related API endpoints."""

    def test_start_simulation(self, docker_context):
        """Test starting a simulation job."""
        payload = {
            "parameters": {
                "steps": 100,
                "actors": 1000,
                "width": 128,
                "height": 128,
                "smooth": False
            }
        }

        response = requests.post(f"{docker_context.base_url}/api/simulate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "message" in data

    def _start_simulation_helper(self, docker_context):
        """Helper method to start a simulation and return job ID."""
        payload = {
            "parameters": {
                "steps": 100,
                "actors": 1000,
                "width": 128,
                "height": 128,
                "smooth": False
            }
        }

        response = requests.post(f"{docker_context.base_url}/api/simulate", json=payload)
        assert response.status_code == 200

        data = response.json()
        return data["job_id"]

    def test_get_simulation_status(self, docker_context):
        """Test getting simulation status."""
        # Start a simulation first
        job_id = self._start_simulation_helper(docker_context)

        response = requests.get(f"{docker_context.base_url}/api/simulate/{job_id}/status")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert data["status"] in ["pending", "running", "completed", "failed"]

    def test_cancel_simulation(self, docker_context):
        """Test cancelling a simulation."""
        # Start a simulation first
        job_id = self._start_simulation_helper(docker_context)

        # Try to cancel it
        response = requests.delete(f"{docker_context.base_url}/api/simulate/{job_id}")

        # Should succeed or indicate job is not cancellable
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data

    def test_get_job_statistics(self, docker_context):
        """Test getting job statistics."""
        response = requests.get(f"{docker_context.base_url}/api/jobs")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

        stats = data["data"]
        assert "total_jobs" in stats
        assert "active_jobs" in stats
        assert "max_concurrent_jobs" in stats
        assert "status_counts" in stats

    def test_cleanup_old_jobs(self, docker_context):
        """Test cleaning up old jobs."""
        response = requests.post(f"{docker_context.base_url}/api/jobs/cleanup?max_age_hours=0")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    def test_invalid_simulation_parameters(self, docker_context):
        """Test handling of invalid simulation parameters."""
        payload = {
            "parameters": {
                "steps": -1,  # Invalid negative value
                "actors": 0,   # Invalid zero value
                "width": 50000,  # Too large
                "height": 50000,  # Too large
            }
        }

        response = requests.post(f"{docker_context.base_url}/api/simulate", json=payload)
        assert response.status_code == 400

        data = response.json()
        assert "error" in data["detail"]
        assert "validation_errors" in data["detail"]

    def test_nonexistent_job_status(self, docker_context):
        """Test getting status of non-existent job."""
        fake_job_id = "nonexistent-job-id"
        response = requests.get(f"{docker_context.base_url}/api/simulate/{fake_job_id}/status")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data["detail"]


class TestModelsAPI:
    """Test model registry API endpoints."""

    def test_list_models(self, docker_context):
        """Test listing models."""
        response = requests.get(f"{docker_context.base_url}/api/models/")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "models" in data["data"]
        assert "total_count" in data["data"]
        assert "statistics" in data

    def test_list_models_with_filters(self, docker_context):
        """Test listing models with filters."""
        params = {
            "source": "web",
            "favorites": "false",
            "limit": 10,
            "offset": 0
        }

        response = requests.get(f"{docker_context.base_url}/api/models/", params=params)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_get_model_statistics(self, docker_context):
        """Test getting model statistics."""
        response = requests.get(f"{docker_context.base_url}/api/models/statistics")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_scan_models(self, docker_context):
        """Test scanning for models."""
        response = requests.post(f"{docker_context.base_url}/api/models/scan")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    def test_nonexistent_model(self, docker_context):
        """Test getting non-existent model."""
        fake_model_id = "nonexistent-model-id"
        response = requests.get(f"{docker_context.base_url}/api/models/{fake_model_id}")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data["detail"]


class TestEndToEndSimulation:
    """Test complete simulation workflow."""

    @pytest.mark.slow
    def test_complete_simulation_workflow(self, docker_context):
        """Test a complete simulation from start to finish."""
        # Start simulation with minimal parameters for speed
        payload = {
            "parameters": {
                "steps": 50,      # Minimal steps for speed
                "actors": 500,    # Fewer actors for speed
                "width": 64,      # Smaller size for speed
                "height": 64,     # Smaller size for speed
                "smooth": False
            }
        }

        # Start simulation
        response = requests.post(f"{docker_context.base_url}/api/simulate", json=payload)
        assert response.status_code == 200

        job_id = response.json()["job_id"]

        # Wait for completion with timeout
        max_wait_time = 120  # 2 minutes max
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{docker_context.base_url}/api/simulate/{job_id}/status")
            assert response.status_code == 200

            status_data = response.json()
            status = status_data["status"]

            if status == "completed":
                # Test getting result
                response = requests.get(f"{docker_context.base_url}/api/simulate/{job_id}/result")
                assert response.status_code == 200

                result_data = response.json()
                assert result_data["job_id"] == job_id
                assert result_data["status"] == "completed"
                assert "files" in result_data
                assert "parameters" in result_data

                # Test downloading files
                if "jpg" in result_data["files"]:
                    response = requests.get(f"{docker_context.base_url}/api/simulate/{job_id}/download/jpg")
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "image/jpeg"

                if "json" in result_data["files"]:
                    response = requests.get(f"{docker_context.base_url}/api/simulate/{job_id}/download/json")
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "application/json"

                # Test preview endpoint
                response = requests.get(f"{docker_context.base_url}/api/simulate/{job_id}/preview")
                assert response.status_code == 200
                assert response.headers["content-type"] == "image/jpeg"

                return  # Test completed successfully

            elif status == "failed":
                # Get container logs for debugging
                logs = docker_context.get_container_logs()
                pytest.fail(f"Simulation failed. Container logs:\n{logs}")

            time.sleep(2)  # Wait 2 seconds before checking again

        # If we get here, simulation didn't complete in time
        logs = docker_context.get_container_logs()
        pytest.fail(f"Simulation didn't complete within {max_wait_time} seconds. Container logs:\n{logs}")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_malformed_json_request(self, docker_context):
        """Test handling of malformed JSON requests."""
        response = requests.post(
            f"{docker_context.base_url}/api/simulate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_content_type(self, docker_context):
        """Test handling of requests without content type."""
        response = requests.post(
            f"{docker_context.base_url}/api/simulate",
            data='{"parameters": {"steps": 100}}',
        )
        # Should still work or return appropriate error
        assert response.status_code in [200, 400, 422]

    def test_invalid_file_type_download(self, docker_context):
        """Test downloading invalid file type."""
        # Start a simulation first
        payload = {
            "parameters": {
                "steps": 50,
                "actors": 500,
                "width": 64,
                "height": 64,
                "smooth": False
            }
        }

        response = requests.post(f"{docker_context.base_url}/api/simulate", json=payload)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Try to download invalid file type
        response = requests.get(f"{docker_context.base_url}/api/simulate/{job_id}/download/invalid")
        assert response.status_code == 400

        data = response.json()
        assert "error" in data["detail"]


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "--tb=short"])
