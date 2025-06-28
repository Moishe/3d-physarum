# ABOUTME: Persistent model registry for tracking generated models across CLI and web interfaces
# ABOUTME: Manages SQLite database and file system scanning for complete model history

import sqlite3
import json
import os
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ModelRecord:
    """Represents a model record in the registry."""
    id: str
    created_at: float
    name: str
    stl_path: Optional[str] = None
    json_path: Optional[str] = None
    jpg_path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"  # 'cli', 'web', or 'unknown'
    git_commit: Optional[str] = None
    file_sizes: Dict[str, int] = field(default_factory=dict)
    favorite: bool = False
    tags: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "name": self.name,
            "stl_path": self.stl_path,
            "json_path": self.json_path,
            "jpg_path": self.jpg_path,
            "parameters": self.parameters,
            "source": self.source,
            "git_commit": self.git_commit,
            "file_sizes": self.file_sizes,
            "favorite": self.favorite,
            "tags": self.tags.split(",") if self.tags else []
        }


class ModelRegistry:
    """Manages persistent registry of generated 3D models with SQLite backend."""
    
    def __init__(self, output_dir: str = "output", db_path: str = None):
        """Initialize the model registry.
        
        Args:
            output_dir: Directory to scan for model files
            db_path: Path to SQLite database file (defaults to output_dir/models.db)
        """
        self.output_dir = Path(output_dir)
        self.db_path = db_path or str(self.output_dir / "models.db")
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"ModelRegistry initialized with output_dir={output_dir}, db_path={self.db_path}")
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS models (
                        id TEXT PRIMARY KEY,
                        created_at REAL NOT NULL,
                        name TEXT NOT NULL,
                        stl_path TEXT,
                        json_path TEXT,
                        jpg_path TEXT,
                        parameters TEXT,  -- JSON as text
                        source TEXT DEFAULT 'unknown',
                        git_commit TEXT,
                        file_sizes TEXT,  -- JSON as text
                        favorite INTEGER DEFAULT 0,
                        tags TEXT DEFAULT ''
                    )
                """)
                
                # Create indexes for common queries
                conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON models(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON models(source)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_favorite ON models(favorite)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _generate_model_id(self, json_path: str = None, stl_path: str = None) -> str:
        """Generate a unique model ID based on file path or timestamp."""
        if json_path and os.path.exists(json_path):
            # Use hash of JSON file content for deterministic IDs
            with open(json_path, 'r') as f:
                content = f.read()
            hash_obj = hashlib.md5(content.encode())
            return f"model_{hash_obj.hexdigest()[:12]}"
        elif stl_path:
            # Use filename-based ID
            base_name = Path(stl_path).stem
            return f"model_{base_name}_{int(time.time())}"
        else:
            # Fallback to UUID
            return f"model_{str(uuid.uuid4())[:8]}"
    
    def _parse_json_metadata(self, json_path: str) -> Tuple[Dict[str, Any], str, str]:
        """Parse JSON metadata file to extract parameters, source, and git commit.
        
        Returns:
            Tuple of (parameters, source, git_commit)
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            parameters = data.get('parameters', {})
            git_commit = data.get('git_commit_hash')
            
            # Determine source based on command line or other indicators
            command_line = data.get('command_line', '')
            if 'main.py' in command_line or any(arg.startswith('-') for arg in command_line.split()):
                source = 'cli'
            elif 'job_id' in str(data) or len(command_line) == 0:
                source = 'web'
            else:
                source = 'unknown'
            
            return parameters, source, git_commit
            
        except Exception as e:
            logger.warning(f"Failed to parse JSON metadata from {json_path}: {e}")
            return {}, 'unknown', None
    
    def _scan_output_directory(self) -> List[Dict[str, str]]:
        """Scan output directory for model files and group them by base name.
        
        Returns:
            List of file group dictionaries with 'stl', 'json', 'jpg' keys
        """
        file_groups = {}
        
        try:
            for file_path in self.output_dir.iterdir():
                if not file_path.is_file():
                    continue
                
                stem = file_path.stem
                suffix = file_path.suffix.lower()
                
                # Initialize group if not exists
                if stem not in file_groups:
                    file_groups[stem] = {'stl': None, 'json': None, 'jpg': None}
                
                # Categorize file by extension
                if suffix == '.stl':
                    file_groups[stem]['stl'] = str(file_path)
                elif suffix == '.json':
                    file_groups[stem]['json'] = str(file_path)
                elif suffix in ['.jpg', '.jpeg']:
                    file_groups[stem]['jpg'] = str(file_path)
            
            # Convert to list and filter out groups without any core files
            return [group for group in file_groups.values() 
                   if group['stl'] or group['json']]
            
        except Exception as e:
            logger.error(f"Failed to scan output directory {self.output_dir}: {e}")
            return []
    
    def scan_and_register_models(self) -> int:
        """Scan output directory and register any new models.
        
        Returns:
            Number of new models registered
        """
        logger.info("Scanning output directory for models...")
        
        file_groups = self._scan_output_directory()
        registered_count = 0
        
        for group in file_groups:
            try:
                # Generate ID and check if already registered
                model_id = self._generate_model_id(group['json'], group['stl'])
                
                if self.get_model(model_id):
                    continue  # Already registered
                
                # Parse metadata if JSON exists
                parameters = {}
                source = 'unknown'
                git_commit = None
                
                if group['json']:
                    parameters, source, git_commit = self._parse_json_metadata(group['json'])
                
                # Determine model name
                name = "Untitled Model"
                if parameters.get('output'):
                    name = Path(parameters['output']).stem
                elif group['stl']:
                    name = Path(group['stl']).stem
                elif group['json']:
                    name = Path(group['json']).stem
                
                # Get file sizes
                file_sizes = {}
                for file_type, file_path in group.items():
                    if file_path and os.path.exists(file_path):
                        file_sizes[file_type] = os.path.getsize(file_path)
                
                # Get creation time from files
                created_at = time.time()
                if group['json'] and os.path.exists(group['json']):
                    created_at = os.path.getctime(group['json'])
                elif group['stl'] and os.path.exists(group['stl']):
                    created_at = os.path.getctime(group['stl'])
                
                # Create model record
                model = ModelRecord(
                    id=model_id,
                    created_at=created_at,
                    name=name,
                    stl_path=group['stl'],
                    json_path=group['json'],
                    jpg_path=group['jpg'],
                    parameters=parameters,
                    source=source,
                    git_commit=git_commit,
                    file_sizes=file_sizes
                )
                
                # Register the model
                self.register_model(model)
                registered_count += 1
                
                logger.info(f"Registered model: {model_id} ({name})")
                
            except Exception as e:
                logger.error(f"Failed to register model from group {group}: {e}")
                continue
        
        logger.info(f"Scan complete. Registered {registered_count} new models.")
        return registered_count
    
    def register_model(self, model: ModelRecord) -> bool:
        """Register a new model in the database.
        
        Args:
            model: ModelRecord to register
            
        Returns:
            True if successfully registered
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO models 
                    (id, created_at, name, stl_path, json_path, jpg_path, 
                     parameters, source, git_commit, file_sizes, favorite, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    model.id,
                    model.created_at,
                    model.name,
                    model.stl_path,
                    model.json_path,
                    model.jpg_path,
                    json.dumps(model.parameters),
                    model.source,
                    model.git_commit,
                    json.dumps(model.file_sizes),
                    int(model.favorite),
                    model.tags
                ))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to register model {model.id}: {e}")
            return False
    
    def get_model(self, model_id: str) -> Optional[ModelRecord]:
        """Get a model by ID.
        
        Args:
            model_id: Model ID to retrieve
            
        Returns:
            ModelRecord if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM models WHERE id = ?", (model_id,))
                row = cursor.fetchone()
                
                if row:
                    return ModelRecord(
                        id=row['id'],
                        created_at=row['created_at'],
                        name=row['name'],
                        stl_path=row['stl_path'],
                        json_path=row['json_path'],
                        jpg_path=row['jpg_path'],
                        parameters=json.loads(row['parameters'] or '{}'),
                        source=row['source'],
                        git_commit=row['git_commit'],
                        file_sizes=json.loads(row['file_sizes'] or '{}'),
                        favorite=bool(row['favorite']),
                        tags=row['tags'] or ''
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get model {model_id}: {e}")
            return None
    
    def list_models(self, source: str = None, favorite_only: bool = False, 
                   limit: int = None, offset: int = 0) -> List[ModelRecord]:
        """List models with optional filtering.
        
        Args:
            source: Filter by source ('cli', 'web', etc.)
            favorite_only: Only return favorited models
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of ModelRecord objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build query with filters
                query = "SELECT * FROM models WHERE 1=1"
                params = []
                
                if source:
                    query += " AND source = ?"
                    params.append(source)
                
                if favorite_only:
                    query += " AND favorite = 1"
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                    
                    if offset:
                        query += " OFFSET ?"
                        params.append(offset)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                models = []
                for row in rows:
                    models.append(ModelRecord(
                        id=row['id'],
                        created_at=row['created_at'],
                        name=row['name'],
                        stl_path=row['stl_path'],
                        json_path=row['json_path'],
                        jpg_path=row['jpg_path'],
                        parameters=json.loads(row['parameters'] or '{}'),
                        source=row['source'],
                        git_commit=row['git_commit'],
                        file_sizes=json.loads(row['file_sizes'] or '{}'),
                        favorite=bool(row['favorite']),
                        tags=row['tags'] or ''
                    ))
                
                return models
                
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def update_model(self, model_id: str, updates: Dict[str, Any]) -> bool:
        """Update model metadata.
        
        Args:
            model_id: Model ID to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successfully updated
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Build update query dynamically
                valid_fields = ['name', 'favorite', 'tags']
                set_clauses = []
                params = []
                
                for field, value in updates.items():
                    if field in valid_fields:
                        set_clauses.append(f"{field} = ?")
                        if field == 'favorite':
                            params.append(int(value))
                        else:
                            params.append(value)
                
                if not set_clauses:
                    return False
                
                params.append(model_id)
                query = f"UPDATE models SET {', '.join(set_clauses)} WHERE id = ?"
                
                cursor = conn.execute(query, params)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update model {model_id}: {e}")
            return False
    
    def delete_model(self, model_id: str, delete_files: bool = False) -> bool:
        """Delete a model from the registry and optionally its files.
        
        Args:
            model_id: Model ID to delete
            delete_files: Whether to also delete the associated files
            
        Returns:
            True if successfully deleted
        """
        try:
            model = self.get_model(model_id)
            if not model:
                return False
            
            # Delete files if requested
            if delete_files:
                for file_path in [model.stl_path, model.json_path, model.jpg_path]:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logger.warning(f"Failed to delete file {file_path}: {e}")
            
            # Remove from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM models WHERE id = ?", (model_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete model {model_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Dictionary with various statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_models,
                        COUNT(CASE WHEN source = 'cli' THEN 1 END) as cli_models,
                        COUNT(CASE WHEN source = 'web' THEN 1 END) as web_models,
                        COUNT(CASE WHEN favorite = 1 THEN 1 END) as favorite_models,
                        SUM(CASE WHEN stl_path IS NOT NULL THEN 1 ELSE 0 END) as models_with_stl,
                        SUM(CASE WHEN jpg_path IS NOT NULL THEN 1 ELSE 0 END) as models_with_preview
                    FROM models
                """)
                row = cursor.fetchone()
                
                return {
                    'total_models': row[0],
                    'cli_models': row[1],
                    'web_models': row[2],
                    'favorite_models': row[3],
                    'models_with_stl': row[4],
                    'models_with_preview': row[5]
                }
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Global instance
model_registry = ModelRegistry()