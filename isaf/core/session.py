"""
ISAF Session Management

Provides the core session handling for ISAF logging, including
initialization, layer logging, lineage retrieval, and export.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

_global_session: Optional['ISAFSession'] = None


class ISAFSession:
    """
    Main session class for ISAF logging.
    
    Manages the logging session, stores layer data, and coordinates
    with storage backends and exporters.
    """
    
    def __init__(
        self,
        backend: str = 'sqlite',
        db_path: Optional[str] = None,
        auto_log_framework: bool = True,
        **config: Any
    ):
        self.session_id = str(uuid.uuid4())
        self.backend_type = backend
        self.db_path = db_path or 'isaf_lineage.db'
        self.auto_log_framework = auto_log_framework
        self.config = config
        self.created_at = datetime.utcnow()
        
        self._layers: Dict[int, Dict[str, Any]] = {}
        self._backend = None
        
        self._init_backend()
        
        if auto_log_framework:
            self._log_framework_automatically()
    
    def _init_backend(self) -> None:
        """Initialize the storage backend."""
        if self.backend_type == 'sqlite':
            from isaf.storage.sqlite_backend import SQLiteBackend
            self._backend = SQLiteBackend(self.db_path)
        elif self.backend_type == 'mlflow':
            from isaf.storage.mlflow_backend import MLflowBackend
            tracking_uri = self.config.get('tracking_uri')
            self._backend = MLflowBackend(tracking_uri)
        elif self.backend_type == 'memory':
            self._backend = None
        else:
            raise ValueError(f"Unknown backend: {self.backend_type}")
    
    def _log_framework_automatically(self) -> None:
        """Automatically log Layer 6 framework information."""
        try:
            from isaf.core.extractors import Layer6Extractor
            
            extractor = Layer6Extractor()
            context = {
                'function_name': '__auto_detect__',
                'module': '__main__',
                'timestamp': datetime.utcnow().isoformat()
            }
            layer_data = extractor.extract(context)
            self.log_layer(6, layer_data)
        except Exception:
            pass
    
    def log_layer(self, layer_num: int, data: Dict[str, Any]) -> None:
        """
        Log data for a specific layer.
        
        Args:
            layer_num: Layer number (6, 7, or 8)
            data: Layer data dictionary
        """
        if layer_num not in [6, 7, 8]:
            raise ValueError(f"Invalid layer number: {layer_num}. Must be 6, 7, or 8.")
        
        layer_data = {
            'layer': layer_num,
            'session_id': self.session_id,
            'logged_at': datetime.utcnow().isoformat(),
            'data': data
        }
        
        self._layers[layer_num] = layer_data
        
        if self._backend is not None:
            try:
                self._backend.store(layer_num, layer_data)
            except Exception as e:
                # CRITICAL: Log error instead of silent failure (EU AI Act Article 12)
                from isaf.error_logger import get_error_logger
                from isaf.fallback_storage import FallbackStorage
                
                error_logger = get_error_logger()
                error_logger.log_error('backend_storage', e, {
                    'layer': layer_num,
                    'session_id': self.session_id,
                    'backend_type': self.backend_type
                })
                
                # Try fallback storage
                try:
                    fallback = FallbackStorage()
                    fallback.store(layer_num, layer_data, session_id=self.session_id)
                except Exception as fallback_error:
                    error_logger.log_error('fallback_storage', fallback_error)
    
    def get_lineage(self) -> Dict[str, Any]:
        """
        Get the complete lineage for this session.
        
        Returns:
            Dictionary containing all logged layers and metadata
        """
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'layers': {
                str(k): v for k, v in sorted(self._layers.items())
            },
            'metadata': {
                'backend': self.backend_type,
                'isaf_version': '0.1.0'
            }
        }
    
    def export(
        self,
        output_path: str,
        compliance_mappings: Optional[list] = None
    ) -> str:
        """
        Export lineage to a JSON file with mandatory hash chain.
        
        Args:
            output_path: Path for the output file
            compliance_mappings: List of compliance frameworks to map to
        
        Returns:
            Path to the exported file
        """
        from isaf.export.exporter import ISAFExporter
        
        lineage = self.get_lineage()
        exporter = ISAFExporter()
        
        return exporter.export(
            lineage,
            output_path,
            include_hash_chain=True,  # Always mandatory for compliance
            compliance_mappings=compliance_mappings
        )


def init(
    backend: str = 'sqlite',
    db_path: Optional[str] = None,
    auto_log_framework: bool = True,
    **config: Any
) -> ISAFSession:
    """
    Initialize ISAF logging session.
    
    Args:
        backend: Storage backend ('sqlite', 'mlflow', or 'memory')
        db_path: Path to database file (for sqlite backend)
        auto_log_framework: Automatically log Layer 6 on init
        **config: Additional configuration options
    
    Returns:
        The initialized ISAFSession
    
    Example:
        isaf.init(backend='sqlite', db_path='my_lineage.db')
    """
    global _global_session
    _global_session = ISAFSession(
        backend=backend,
        db_path=db_path,
        auto_log_framework=auto_log_framework,
        **config
    )
    return _global_session


def get_session() -> Optional[ISAFSession]:
    """
    Get the current global session.
    
    Returns:
        The current ISAFSession or None if not initialized
    """
    return _global_session


def get_lineage(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get lineage data.
    
    Args:
        session_id: Optional session ID to retrieve (uses current if None)
    
    Returns:
        Lineage dictionary
    """
    if _global_session is None:
        raise RuntimeError("ISAF not initialized. Call isaf.init() first.")
    
    if session_id is not None and _global_session._backend is not None:
        return _global_session._backend.retrieve(session_id)
    
    return _global_session.get_lineage()


def export(
    output_path: str,
    compliance_mappings: Optional[list] = None
) -> str:
    """
    Export current session lineage to file with mandatory hash chain.
    
    Args:
        output_path: Path for the output file
        compliance_mappings: Compliance frameworks to map
    
    Returns:
        Path to exported file
    """
    if _global_session is None:
        raise RuntimeError("ISAF not initialized. Call isaf.init() first.")
    
    return _global_session.export(
        output_path,
        compliance_mappings=compliance_mappings
    )


def verify_lineage(lineage_file: str) -> bool:
    """
    Verify the cryptographic integrity of a lineage file.
    
    Args:
        lineage_file: Path to the lineage JSON file
    
    Returns:
        True if verification passes
        
    Raises:
        ValueError: If hash chain is missing (file may be tampered or old version)
    """
    import json
    from isaf.verification.hash_chain import HashChainGenerator
    
    with open(lineage_file, 'r') as f:
        data = json.load(f)
    
    if 'hash_chain' not in data:
        raise ValueError(
            f"Lineage file {lineage_file} is missing hash_chain. "
            "This file may have been tampered with or was created with an old version. "
            "Hash chains are mandatory for compliance (EU AI Act Article 12)."
        )
    
    generator = HashChainGenerator()
    return generator.verify_chain(data, data['hash_chain'])
