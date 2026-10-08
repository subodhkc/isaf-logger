"""
ISAF Fallback Storage - Emergency Data Persistence

Provides local file-based storage when primary backend fails.
Critical for EU AI Act Article 12 compliance (record-keeping requirement).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class FallbackStorage:
    """
    Emergency fallback storage for ISAF when primary backend fails.
    
    Stores layer data as JSON files in a local directory.
    """
    
    def __init__(self, fallback_dir: str = '.isaf_fallback'):
        """
        Initialize fallback storage.
        
        Args:
            fallback_dir: Directory for fallback storage files
        """
        self.fallback_dir = Path(fallback_dir)
        self.fallback_dir.mkdir(exist_ok=True)
        
        # Create README to explain what this directory is
        readme_path = self.fallback_dir / 'README.txt'
        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write(
                    "ISAF Logger Fallback Storage\n"
                    "============================\n\n"
                    "This directory contains ISAF lineage data that was stored locally\n"
                    "because the primary backend (SQLite/MLflow) was unavailable.\n\n"
                    "These files should be imported into the primary backend when it\n"
                    "becomes available again.\n\n"
                    "File format: layer_{layer_num}_{session_id}_{timestamp}.json\n"
                )
    
    def store(
        self, 
        layer_num: int, 
        data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """
        Store layer data to fallback storage.
        
        Args:
            layer_num: Layer number (6, 7, or 8)
            data: Layer data dictionary
            session_id: Optional session ID for correlation
            
        Returns:
            Path to stored file
        """
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        session_part = f"_{session_id}" if session_id else ""
        filename = f"layer_{layer_num}{session_part}_{timestamp}.json"
        filepath = self.fallback_dir / filename
        
        # Add metadata
        storage_data = {
            'stored_at': datetime.utcnow().isoformat(),
            'layer': layer_num,
            'session_id': session_id,
            'data': data,
            'fallback_reason': 'Primary backend unavailable'
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(storage_data, f, indent=2)
        
        return str(filepath)
    
    def list_files(self) -> list:
        """
        List all fallback storage files.
        
        Returns:
            List of file paths
        """
        return [
            str(f) for f in self.fallback_dir.glob('layer_*.json')
        ]
    
    def read_file(self, filepath: str) -> Dict[str, Any]:
        """
        Read a fallback storage file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Stored data
        """
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def get_count(self) -> int:
        """
        Get count of files in fallback storage.
        
        Returns:
            Number of fallback files
        """
        return len(self.list_files())
    
    def clear(self) -> int:
        """
        Clear all fallback storage files (for testing).
        
        Returns:
            Number of files deleted
        """
        files = self.list_files()
        for filepath in files:
            Path(filepath).unlink()
        return len(files)
    
    def import_to_backend(self, backend) -> int:
        """
        Import all fallback files to primary backend.
        
        Args:
            backend: ISAF backend instance (SQLite or MLflow)
            
        Returns:
            Number of files imported
        """
        files = self.list_files()
        imported = 0
        
        for filepath in files:
            try:
                data = self.read_file(filepath)
                backend.store(data['layer'], data['data'])
                Path(filepath).unlink()  # Delete after successful import
                imported += 1
            except Exception as e:
                # Log error but continue with other files
                print(f"Failed to import {filepath}: {e}")
        
        return imported
