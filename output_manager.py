# ABOUTME: Output file management utilities for 3D model generation
# ABOUTME: Handles directory creation, file numbering, and sidecar JSON generation

import os
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


class OutputManager:
    """Manages output file creation with automatic numbering and sidecar JSON files."""
    
    def __init__(self, default_output_dir: str = "output"):
        """Initialize the output manager.
        
        Args:
            default_output_dir: Default directory for output files
        """
        self.default_output_dir = default_output_dir
    
    def ensure_output_directory(self, output_path: str) -> str:
        """Ensure the output directory exists and return the full path.
        
        Args:
            output_path: The requested output path
            
        Returns:
            The full output path with directory created
        """
        # If no directory specified, use default output directory
        if os.path.dirname(output_path) == "":
            output_path = os.path.join(self.default_output_dir, output_path)
        
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        return output_path
    
    def get_unique_filename(self, base_path: str) -> Tuple[str, str, str]:
        """Get a unique filename by adding sequential numbers if needed.
        
        Args:
            base_path: The base path for the file
            
        Returns:
            Tuple of (unique_stl_path, unique_json_path, unique_jpg_path)
        """
        # Ensure output directory exists
        base_path = self.ensure_output_directory(base_path)
        
        # Split path and extension
        path_without_ext = os.path.splitext(base_path)[0]
        ext = os.path.splitext(base_path)[1]
        
        # Check if base filename exists
        stl_path = base_path
        json_path = path_without_ext + ".json"
        jpg_path = path_without_ext + ".jpg"
        
        counter = 1
        while os.path.exists(stl_path) or os.path.exists(json_path) or os.path.exists(jpg_path):
            stl_path = f"{path_without_ext}-{counter}{ext}"
            json_path = f"{path_without_ext}-{counter}.json"
            jpg_path = f"{path_without_ext}-{counter}.jpg"
            counter += 1
        
        return stl_path, json_path, jpg_path
    
    def get_git_commit_hash(self) -> Optional[str]:
        """Get the current git commit hash.
        
        Returns:
            The git commit hash if available, None otherwise
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes in the git repository.
        
        Returns:
            True if there are uncommitted changes, False otherwise
        """
        try:
            # Check for staged changes
            result_staged = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                capture_output=True,
                cwd=os.getcwd()
            )
            
            # Check for unstaged changes
            result_unstaged = subprocess.run(
                ["git", "diff", "--quiet"],
                capture_output=True,
                cwd=os.getcwd()
            )
            
            # Check for untracked files
            result_untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            # If any of these return non-zero or untracked files exist, there are changes
            return (result_staged.returncode != 0 or 
                    result_unstaged.returncode != 0 or 
                    (result_untracked.returncode == 0 and result_untracked.stdout.strip()))
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def create_sidecar_json(self, json_path: str, args: Any, command_line: str) -> None:
        """Create a sidecar JSON file with parameters and command line.
        
        Args:
            json_path: Path for the JSON file
            args: The parsed arguments object
            command_line: The original command line used
        """
        # Convert args to dictionary, handling all parameter types
        params = {}
        for key, value in vars(args).items():
            params[key] = value
        
        # Get git information
        git_hash = self.get_git_commit_hash()
        has_uncommitted = self.has_uncommitted_changes()
        
        # Create the sidecar data
        sidecar_data = {
            "parameters": params,
            "command_line": command_line,
            "description": "Parameters and command line for 3D Physarum model generation",
            "git_commit_hash": git_hash,
            "has_uncommitted_changes": has_uncommitted
        }
        
        # Write the JSON file
        with open(json_path, 'w') as f:
            json.dump(sidecar_data, f, indent=2)
    
    def prepare_output_files(self, output_path: str, args: Any) -> Tuple[str, str, str]:
        """Prepare output files with unique names and create sidecar JSON.
        
        Args:
            output_path: The requested output path
            args: The parsed arguments object
            
        Returns:
            Tuple of (final_stl_path, final_json_path, final_jpg_path)
        """
        # Get unique filenames
        stl_path, json_path, jpg_path = self.get_unique_filename(output_path)
        
        # Reconstruct the command line from sys.argv
        command_line = " ".join(sys.argv)
        
        # Create sidecar JSON
        self.create_sidecar_json(json_path, args, command_line)
        
        return stl_path, json_path, jpg_path