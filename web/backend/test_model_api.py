# ABOUTME: Integration tests for model registry API endpoints
# ABOUTME: Tests the FastAPI routes for listing, downloading, and managing models

import unittest
import tempfile
import os
import json
import shutil
import time
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.model_registry import ModelRegistry, ModelRecord


class TestModelAPI(unittest.TestCase):
    """Integration tests for model registry API endpoints."""
    
    def setUp(self):
        """Set up test environment with temporary registry."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_models.db")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create test registry
        self.test_registry = ModelRegistry(output_dir=self.output_dir, db_path=self.db_path)
        
        # Patch the global registry with our test instance
        self.registry_patcher = patch('app.api.routes.models.model_registry', self.test_registry)
        self.registry_patcher.start()
        
        # Create test client
        self.client = TestClient(app)
        
        # Add some test models
        self._create_test_models()
        
    def tearDown(self):
        """Clean up test environment."""
        self.registry_patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_test_models(self):
        """Create test models for testing."""
        # CLI model
        cli_model = ModelRecord(
            id="test_cli_model",
            created_at=time.time() - 3600,  # 1 hour ago
            name="CLI Test Model",
            stl_path=os.path.join(self.output_dir, "cli_model.stl"),
            json_path=os.path.join(self.output_dir, "cli_model.json"),
            jpg_path=os.path.join(self.output_dir, "cli_model.jpg"),
            parameters={"width": 256, "height": 256, "steps": 100, "actors": 50},
            source="cli",
            git_commit="abc123def456",
            file_sizes={"stl": 2048, "json": 512, "jpg": 1024},
            favorite=True,
            tags="test,cli"
        )
        
        # Web model
        web_model = ModelRecord(
            id="test_web_model",
            created_at=time.time() - 1800,  # 30 minutes ago
            name="Web Test Model",
            stl_path=os.path.join(self.output_dir, "web_model.stl"),
            json_path=os.path.join(self.output_dir, "web_model.json"),
            parameters={"width": 128, "height": 128, "steps": 50, "actors": 25},
            source="web",
            file_sizes={"stl": 1024, "json": 256},
            favorite=False,
            tags="test,web"
        )
        
        # Create actual test files
        for model in [cli_model, web_model]:
            if model.stl_path:
                with open(model.stl_path, 'w') as f:
                    f.write(f"dummy stl content for {model.id}")
            if model.json_path:
                with open(model.json_path, 'w') as f:
                    json.dump({"model_id": model.id, "test": True}, f)
            if model.jpg_path:
                with open(model.jpg_path, 'w') as f:
                    f.write(f"dummy jpg content for {model.id}")
        
        # Register models
        self.test_registry.register_model(cli_model)
        self.test_registry.register_model(web_model)
    
    def test_list_models_all(self):
        """Test listing all models."""
        response = self.client.get("/api/models/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["models"]), 2)
        self.assertEqual(data["data"]["total_count"], 2)
        
        # Check model data structure
        model = data["data"]["models"][0]  # Should be most recent (web model)
        self.assertIn("id", model)
        self.assertIn("name", model)
        self.assertIn("source", model)
        self.assertIn("parameters", model)
        self.assertIn("favorite", model)
        self.assertIn("tags", model)
    
    def test_list_models_with_source_filter(self):
        """Test listing models filtered by source."""
        # Test CLI filter
        response = self.client.get("/api/models/?source=cli")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["models"]), 1)
        self.assertEqual(data["data"]["models"][0]["source"], "cli")
        
        # Test web filter
        response = self.client.get("/api/models/?source=web")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["data"]["models"]), 1)
        self.assertEqual(data["data"]["models"][0]["source"], "web")
    
    def test_list_models_favorites_only(self):
        """Test listing only favorite models."""
        response = self.client.get("/api/models/?favorites=true")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["models"]), 1)
        self.assertTrue(data["data"]["models"][0]["favorite"])
        self.assertEqual(data["data"]["models"][0]["id"], "test_cli_model")
    
    def test_list_models_with_pagination(self):
        """Test model listing with pagination."""
        response = self.client.get("/api/models/?limit=1&offset=0")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["data"]["models"]), 1)
        self.assertEqual(data["data"]["returned_count"], 1)
        self.assertTrue(data["data"]["has_more"])
        
        # Get second page
        response = self.client.get("/api/models/?limit=1&offset=1")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data["data"]["models"]), 1)
        self.assertFalse(data["data"]["has_more"])
    
    def test_get_specific_model(self):
        """Test getting a specific model by ID."""
        response = self.client.get("/api/models/test_cli_model")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        
        model = data["data"]
        self.assertEqual(model["id"], "test_cli_model")
        self.assertEqual(model["name"], "CLI Test Model")
        self.assertEqual(model["source"], "cli")
        self.assertTrue(model["favorite"])
        self.assertEqual(model["parameters"]["width"], 256)
    
    def test_get_nonexistent_model(self):
        """Test getting a model that doesn't exist."""
        response = self.client.get("/api/models/nonexistent")
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertIn("error", data["detail"])
    
    def test_update_model(self):
        """Test updating model metadata."""
        updates = {
            "name": "Updated CLI Model",
            "favorite": False,
            "tags": ["updated", "test"]
        }
        
        response = self.client.put("/api/models/test_cli_model", json=updates)
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        response = self.client.get("/api/models/test_cli_model")
        self.assertEqual(response.status_code, 200)
        
        model = response.json()["data"]
        self.assertEqual(model["name"], "Updated CLI Model")
        self.assertFalse(model["favorite"])
        self.assertIn("updated", model["tags"])
    
    def test_update_nonexistent_model(self):
        """Test updating a model that doesn't exist."""
        updates = {"name": "New Name"}
        
        response = self.client.put("/api/models/nonexistent", json=updates)
        self.assertEqual(response.status_code, 404)
    
    def test_download_model_file(self):
        """Test downloading model files."""
        # Test STL download
        response = self.client.get("/api/models/test_cli_model/download/stl")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/octet-stream")
        
        # Test JSON download
        response = self.client.get("/api/models/test_cli_model/download/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        
        # Test preview download
        response = self.client.get("/api/models/test_cli_model/download/preview")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/jpeg")
    
    def test_download_nonexistent_file(self):
        """Test downloading a file that doesn't exist."""
        # Web model doesn't have a preview file
        response = self.client.get("/api/models/test_web_model/download/preview")
        self.assertEqual(response.status_code, 404)
    
    def test_download_invalid_file_type(self):
        """Test downloading with invalid file type."""
        response = self.client.get("/api/models/test_cli_model/download/invalid")
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn("Invalid file type", data["detail"]["message"])
    
    def test_delete_model(self):
        """Test deleting a model."""
        response = self.client.delete("/api/models/test_web_model")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("deleted from registry", data["message"])
        
        # Verify deletion
        response = self.client.get("/api/models/test_web_model")
        self.assertEqual(response.status_code, 404)
    
    def test_delete_model_with_files(self):
        """Test deleting a model and its files."""
        # Verify files exist
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "cli_model.stl")))
        
        response = self.client.delete("/api/models/test_cli_model?delete_files=true")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("files removed", data["message"])
    
    def test_scan_models(self):
        """Test triggering a model scan."""
        response = self.client.post("/api/models/scan")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("Scan completed", data["message"])
    
    def test_get_statistics(self):
        """Test getting model statistics."""
        response = self.client.get("/api/models/statistics")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        
        stats = data["data"]
        self.assertEqual(stats["total_models"], 2)
        self.assertEqual(stats["cli_models"], 1)
        self.assertEqual(stats["web_models"], 1)
        self.assertEqual(stats["favorite_models"], 1)


if __name__ == '__main__':
    unittest.main()