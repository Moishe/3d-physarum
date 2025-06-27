# ABOUTME: Tests for the output file management system
# ABOUTME: Verifies directory creation, file numbering, and JSON sidecar generation

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock
from physarum_core.output.manager import OutputManager


class TestOutputManager(unittest.TestCase):
    """Test cases for OutputManager functionality."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.output_manager = OutputManager()
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_default_output_directory_creation(self):
        """Test that default output directory is created."""
        # Change to test directory temporarily
        original_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            result = self.output_manager.ensure_output_directory("test_output.stl")
            
            # Should create output directory and return relative path from current dir
            expected_path = "output/test_output.stl"
            self.assertEqual(result, expected_path)
            self.assertTrue(os.path.exists("output"))
        finally:
            os.chdir(original_cwd)
    
    def test_absolute_path_handling(self):
        """Test that absolute paths are handled correctly."""
        abs_path = os.path.join(self.test_dir, "absolute_test.stl")
        result = self.output_manager.ensure_output_directory(abs_path)
        
        self.assertEqual(result, abs_path)
        self.assertTrue(os.path.exists(self.test_dir))
    
    def test_sequential_numbering(self):
        """Test sequential numbering of files."""
        base_path = os.path.join(self.test_dir, "test.stl")
        
        # Create first file
        stl_path1, json_path1, jpg_path1 = self.output_manager.get_unique_filename(base_path)
        with open(stl_path1, 'w') as f:
            f.write("test")
        with open(json_path1, 'w') as f:
            f.write("{}")
        with open(jpg_path1, 'w') as f:
            f.write("fake jpg")
        
        # Create second file - should be numbered
        stl_path2, json_path2, jpg_path2 = self.output_manager.get_unique_filename(base_path)
        expected_stl2 = os.path.join(self.test_dir, "test-1.stl")
        expected_json2 = os.path.join(self.test_dir, "test-1.json")
        expected_jpg2 = os.path.join(self.test_dir, "test-1.jpg")
        
        self.assertEqual(stl_path2, expected_stl2)
        self.assertEqual(json_path2, expected_json2)
        self.assertEqual(jpg_path2, expected_jpg2)
        
        # Create the numbered files
        with open(stl_path2, 'w') as f:
            f.write("test")
        with open(json_path2, 'w') as f:
            f.write("{}")
        with open(jpg_path2, 'w') as f:
            f.write("fake jpg")
        
        # Create third file - should be numbered -2
        stl_path3, json_path3, jpg_path3 = self.output_manager.get_unique_filename(base_path)
        expected_stl3 = os.path.join(self.test_dir, "test-2.stl")
        expected_json3 = os.path.join(self.test_dir, "test-2.json")
        expected_jpg3 = os.path.join(self.test_dir, "test-2.jpg")
        
        self.assertEqual(stl_path3, expected_stl3)
        self.assertEqual(json_path3, expected_json3)
        self.assertEqual(jpg_path3, expected_jpg3)
    
    def test_sidecar_json_creation(self):
        """Test creation of sidecar JSON files."""
        json_path = os.path.join(self.test_dir, "test.json")
        
        # Create mock args object
        mock_args = Mock()
        mock_args.width = 100
        mock_args.height = 100
        mock_args.actors = 50
        mock_args.steps = 100
        mock_args.smooth = False
        
        # Mock vars() function behavior
        def mock_vars(obj):
            return {
                'width': 100,
                'height': 100,
                'actors': 50,
                'steps': 100,
                'smooth': False
            }
        
        # Temporarily replace vars
        import builtins
        original_vars = builtins.vars
        builtins.vars = mock_vars
        
        try:
            command_line = "test_command --width 100 --height 100"
            self.output_manager.create_sidecar_json(json_path, mock_args, command_line)
            
            # Verify JSON file was created and has correct content
            self.assertTrue(os.path.exists(json_path))
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            self.assertIn('parameters', data)
            self.assertIn('command_line', data)
            self.assertIn('description', data)
            
            self.assertEqual(data['command_line'], command_line)
            self.assertEqual(data['parameters']['width'], 100)
            self.assertEqual(data['parameters']['height'], 100)
            self.assertEqual(data['parameters']['actors'], 50)
            self.assertEqual(data['parameters']['steps'], 100)
            self.assertEqual(data['parameters']['smooth'], False)
            
        finally:
            builtins.vars = original_vars
    
    def test_json_only_collision(self):
        """Test behavior when only JSON file exists."""
        base_path = os.path.join(self.test_dir, "test.stl")
        json_path = os.path.join(self.test_dir, "test.json")
        
        # Create only JSON file
        with open(json_path, 'w') as f:
            f.write("{}")
        
        # Should still create numbered files
        stl_path, json_path_result, jpg_path_result = self.output_manager.get_unique_filename(base_path)
        expected_stl = os.path.join(self.test_dir, "test-1.stl")
        expected_json = os.path.join(self.test_dir, "test-1.json")
        expected_jpg = os.path.join(self.test_dir, "test-1.jpg")
        
        self.assertEqual(stl_path, expected_stl)
        self.assertEqual(json_path_result, expected_json)
        self.assertEqual(jpg_path_result, expected_jpg)
    
    def test_stl_only_collision(self):
        """Test behavior when only STL file exists."""
        base_path = os.path.join(self.test_dir, "test.stl")
        
        # Create only STL file
        with open(base_path, 'w') as f:
            f.write("test")
        
        # Should still create numbered files
        stl_path, json_path, jpg_path = self.output_manager.get_unique_filename(base_path)
        expected_stl = os.path.join(self.test_dir, "test-1.stl")
        expected_json = os.path.join(self.test_dir, "test-1.json")
        expected_jpg = os.path.join(self.test_dir, "test-1.jpg")
        
        self.assertEqual(stl_path, expected_stl)
        self.assertEqual(json_path, expected_json)
        self.assertEqual(jpg_path, expected_jpg)


if __name__ == '__main__':
    unittest.main()