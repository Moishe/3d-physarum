# ABOUTME: Output file management system for physarum simulation results
# ABOUTME: Handles directory creation, file numbering, and JSON sidecar generation

import os
import json
from pathlib import Path
from typing import Tuple, Any


class OutputManager:
    """Manages output files for physarum simulation results."""
    
    def __init__(self, default_output_dir: str = "output"):
        """Initialize OutputManager with default output directory.
        
        Args:
            default_output_dir: Default directory for output files
        """
        self.default_output_dir = default_output_dir
    
    def ensure_output_directory(self, filename: str) -> str:
        """Ensure output directory exists and return the full path.
        
        Args:
            filename: Output filename (can be relative or absolute)
            
        Returns:
            Full path to the output file
        """
        if os.path.isabs(filename):
            # Absolute path - ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            return filename
        else:
            # Relative path - use default output directory
            output_dir = self.default_output_dir
            os.makedirs(output_dir, exist_ok=True)
            return os.path.join(output_dir, filename)
    
    def get_unique_filename(self, base_path: str) -> Tuple[str, str, str]:
        """Get unique filenames for STL, JSON, and JPG files.
        
        Args:
            base_path: Base path for the STL file
            
        Returns:
            Tuple of (stl_path, json_path, jpg_path)
        """
        base_path = Path(base_path)
        base_name = base_path.stem
        base_dir = base_path.parent
        
        # Generate paths for all three file types
        stl_path = base_path
        json_path = base_dir / f"{base_name}.json"
        jpg_path = base_dir / f"{base_name}.jpg"
        
        counter = 0
        while (stl_path.exists() or json_path.exists() or jpg_path.exists()):
            counter += 1
            numbered_name = f"{base_name}-{counter}"
            stl_path = base_dir / f"{numbered_name}.stl"
            json_path = base_dir / f"{numbered_name}.json"
            jpg_path = base_dir / f"{numbered_name}.jpg"
        
        return str(stl_path), str(json_path), str(jpg_path)
    
    def create_sidecar_json(self, json_path: str, args: Any, command_line: str) -> None:
        """Create JSON sidecar file with simulation parameters.
        
        Args:
            json_path: Path to the JSON file
            args: Arguments object containing simulation parameters
            command_line: Command line used to generate the simulation
        """
        # Extract parameters from args object
        parameters = vars(args)
        
        # Create JSON data structure
        json_data = {
            "parameters": parameters,
            "command_line": command_line,
            "description": "Parameters and command line for 3D Physarum model generation"
        }
        
        # Write JSON file
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
    
    def prepare_output_files(self, output_filename: str, args: Any) -> Tuple[str, str, str]:
        """Prepare output files for simulation results.
        
        Args:
            output_filename: Output filename
            args: Arguments object containing simulation parameters
            
        Returns:
            Tuple of (stl_path, json_path, jpg_path)
        """
        # Ensure output directory exists
        full_path = self.ensure_output_directory(output_filename)
        
        # Get unique filenames
        stl_path, json_path, jpg_path = self.get_unique_filename(full_path)
        
        return stl_path, json_path, jpg_path