# ABOUTME: Tests for the model registry persistence system
# ABOUTME: Verifies model indexing, database operations, and file system scanning

import unittest
import tempfile
import os
import json
import shutil
import time
from unittest.mock import Mock, patch
import sqlite3

from app.core.model_registry import ModelRegistry, ModelRecord


class TestModelRegistry(unittest.TestCase):
    """Test cases for ModelRegistry functionality."""
    
    def setUp(self):
        """Set up test environment with temporary directory and database."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_models.db")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create registry instance
        self.registry = ModelRegistry(output_dir=self.output_dir, db_path=self.db_path)
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_database_initialization(self):
        """Test that database and tables are created correctly."""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check that tables exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models'")
            result = cursor.fetchone()
            self.assertIsNotNone(result)
    
    def test_register_model(self):
        """Test registering a new model."""
        model = ModelRecord(
            id="test_model_1",
            created_at=time.time(),
            name="Test Model",
            stl_path="/test/model.stl",
            json_path="/test/model.json",
            jpg_path="/test/model.jpg",
            parameters={"width": 100, "height": 100, "steps": 50},
            source="test",
            git_commit="abc123",
            file_sizes={"stl": 1024, "json": 256, "jpg": 512},
            favorite=False,
            tags="test,example"
        )
        
        success = self.registry.register_model(model)
        self.assertTrue(success)
        
        # Verify model was stored
        retrieved = self.registry.get_model("test_model_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Model")
        self.assertEqual(retrieved.source, "test")
        self.assertEqual(retrieved.parameters["width"], 100)
    
    def test_get_nonexistent_model(self):
        """Test getting a model that doesn't exist."""
        result = self.registry.get_model("nonexistent")
        self.assertIsNone(result)
    
    def test_list_models_empty(self):
        """Test listing models when registry is empty."""
        models = self.registry.list_models()
        self.assertEqual(len(models), 0)
    
    def test_list_models_with_filtering(self):
        """Test listing models with source filtering."""
        # Add test models
        cli_model = ModelRecord(
            id="cli_model",
            created_at=time.time(),
            name="CLI Model",
            source="cli",
            parameters={},
            file_sizes={},
            favorite=False,
            tags=""
        )
        
        web_model = ModelRecord(
            id="web_model", 
            created_at=time.time(),
            name="Web Model",
            source="web",
            parameters={},
            file_sizes={},
            favorite=True,
            tags=""
        )
        
        self.registry.register_model(cli_model)
        self.registry.register_model(web_model)
        
        # Test filtering by source
        cli_models = self.registry.list_models(source="cli")
        self.assertEqual(len(cli_models), 1)
        self.assertEqual(cli_models[0].source, "cli")
        
        web_models = self.registry.list_models(source="web")
        self.assertEqual(len(web_models), 1)
        self.assertEqual(web_models[0].source, "web")
        
        # Test filtering by favorites
        favorite_models = self.registry.list_models(favorite_only=True)
        self.assertEqual(len(favorite_models), 1)
        self.assertEqual(favorite_models[0].id, "web_model")
        
        # Test listing all
        all_models = self.registry.list_models()
        self.assertEqual(len(all_models), 2)
    
    def test_update_model(self):
        """Test updating model metadata."""
        # Create and register a model
        model = ModelRecord(
            id="update_test",
            created_at=time.time(),
            name="Original Name",
            source="test",
            parameters={},
            file_sizes={},
            favorite=False,
            tags=""
        )
        
        self.registry.register_model(model)
        
        # Update the model
        updates = {
            "name": "Updated Name",
            "favorite": True,
            "tags": "updated,test"
        }
        
        success = self.registry.update_model("update_test", updates)
        self.assertTrue(success)
        
        # Verify updates
        updated_model = self.registry.get_model("update_test")
        self.assertEqual(updated_model.name, "Updated Name")
        self.assertTrue(updated_model.favorite)
        self.assertEqual(updated_model.tags, "updated,test")
    
    def test_delete_model(self):
        """Test deleting a model from registry."""
        # Create and register a model
        model = ModelRecord(
            id="delete_test",
            created_at=time.time(),
            name="Delete Test",
            source="test", 
            parameters={},
            file_sizes={},
            favorite=False,
            tags=""
        )
        
        self.registry.register_model(model)
        
        # Verify it exists
        self.assertIsNotNone(self.registry.get_model("delete_test"))
        
        # Delete it
        success = self.registry.delete_model("delete_test", delete_files=False)
        self.assertTrue(success)
        
        # Verify it's gone
        self.assertIsNone(self.registry.get_model("delete_test"))
    
    def test_scan_output_directory(self):
        """Test scanning output directory for model files."""
        # Create test files in output directory
        stl_path = os.path.join(self.output_dir, "test_model.stl")
        json_path = os.path.join(self.output_dir, "test_model.json")
        jpg_path = os.path.join(self.output_dir, "test_model.jpg")
        
        # Create dummy STL file
        with open(stl_path, 'w') as f:
            f.write("dummy stl content")
        
        # Create JSON metadata file
        metadata = {
            "parameters": {"width": 256, "height": 256, "steps": 100},
            "command_line": "main.py --width 256 --height 256",
            "description": "Test model",
            "git_commit_hash": "test123"
        }
        
        with open(json_path, 'w') as f:
            json.dump(metadata, f)
        
        # Create dummy preview file
        with open(jpg_path, 'w') as f:
            f.write("dummy jpg content")
        
        # Scan and register
        registered_count = self.registry.scan_and_register_models()
        self.assertEqual(registered_count, 1)
        
        # Verify model was registered
        models = self.registry.list_models()
        self.assertEqual(len(models), 1)
        
        model = models[0]
        self.assertTrue(model.name.startswith("test_model"))
        self.assertEqual(model.source, "cli")  # Should detect CLI from command line
        self.assertEqual(model.parameters["width"], 256)
    
    def test_scan_partial_files(self):
        """Test scanning with only some files present."""
        # Create only JSON file
        json_path = os.path.join(self.output_dir, "partial_model.json")
        metadata = {
            "parameters": {"width": 100, "height": 100},
            "command_line": "python script.py",
            "description": "Partial model"
        }
        
        with open(json_path, 'w') as f:
            json.dump(metadata, f)
        
        # Scan should still register the model
        registered_count = self.registry.scan_and_register_models()
        self.assertEqual(registered_count, 1)
        
        # Verify model registration
        models = self.registry.list_models()
        self.assertEqual(len(models), 1)
        
        model = models[0]
        self.assertIsNone(model.stl_path)  # No STL file
        self.assertIsNotNone(model.json_path)  # Has JSON file
        self.assertIsNone(model.jpg_path)  # No preview file
    
    def test_get_statistics(self):
        """Test getting registry statistics."""
        # Initially empty
        stats = self.registry.get_statistics()
        self.assertEqual(stats['total_models'], 0)
        
        # Add some models
        cli_model = ModelRecord(
            id="cli_1",
            created_at=time.time(),
            name="CLI Model",
            stl_path="/test/cli.stl",
            source="cli",
            parameters={},
            file_sizes={},
            favorite=True,
            tags=""
        )
        
        web_model = ModelRecord(
            id="web_1",
            created_at=time.time(), 
            name="Web Model",
            jpg_path="/test/web.jpg",
            source="web",
            parameters={},
            file_sizes={},
            favorite=False,
            tags=""
        )
        
        self.registry.register_model(cli_model)
        self.registry.register_model(web_model)
        
        # Check updated statistics
        stats = self.registry.get_statistics()
        self.assertEqual(stats['total_models'], 2)
        self.assertEqual(stats['cli_models'], 1)
        self.assertEqual(stats['web_models'], 1)
        self.assertEqual(stats['favorite_models'], 1)
        self.assertEqual(stats['models_with_stl'], 1)
        self.assertEqual(stats['models_with_preview'], 1)
    
    def test_duplicate_registration(self):
        """Test registering the same model twice."""
        model = ModelRecord(
            id="duplicate_test",
            created_at=time.time(),
            name="Duplicate Test",
            source="test",
            parameters={},
            file_sizes={},
            favorite=False,
            tags=""
        )
        
        # First registration
        success1 = self.registry.register_model(model)
        self.assertTrue(success1)
        
        # Second registration (should replace)
        model.name = "Updated Duplicate"
        success2 = self.registry.register_model(model)
        self.assertTrue(success2)
        
        # Should only have one model
        models = self.registry.list_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].name, "Updated Duplicate")


if __name__ == '__main__':
    unittest.main()