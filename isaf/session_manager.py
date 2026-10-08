"""
ISAF Session Manager - Context-Based Multi-Tenant Sessions

Provides thread-safe, context-based session management for multi-tenant scenarios.
Replaces global session state with context-aware session storage.
"""

import threading
from typing import Optional, Dict, Any
from contextvars import ContextVar
from datetime import datetime

from isaf.core.session import ISAFSession


# Context variable for current session (thread-safe)
_current_session: ContextVar[Optional[ISAFSession]] = ContextVar('isaf_session', default=None)

# Global session registry for multi-tenant support
_session_registry: Dict[str, ISAFSession] = {}
_registry_lock = threading.Lock()


class SessionManager:
    """
    Thread-safe session manager for ISAF.
    
    Supports:
    - Context-based sessions (thread-safe)
    - Multi-tenant isolation
    - Session lifecycle management
    """
    
    @staticmethod
    def create_session(
        tenant_id: Optional[str] = None,
        backend: str = 'sqlite',
        db_path: Optional[str] = None,
        auto_log_framework: bool = True,
        **config: Any
    ) -> ISAFSession:
        """
        Create a new ISAF session.
        
        Args:
            tenant_id: Optional tenant identifier for multi-tenant scenarios
            backend: Storage backend ('sqlite', 'mlflow', or 'memory')
            db_path: Path to database file (for sqlite backend)
            auto_log_framework: Automatically log Layer 6 on init
            **config: Additional configuration options
            
        Returns:
            The created ISAFSession
        """
        session = ISAFSession(
            backend=backend,
            db_path=db_path,
            auto_log_framework=auto_log_framework,
            **config
        )
        
        # Register session if tenant_id provided
        if tenant_id:
            with _registry_lock:
                _session_registry[tenant_id] = session
        
        # Set as current session in context
        _current_session.set(session)
        
        return session
    
    @staticmethod
    def get_session(tenant_id: Optional[str] = None) -> Optional[ISAFSession]:
        """
        Get the current session.
        
        Args:
            tenant_id: Optional tenant ID to get specific tenant's session
            
        Returns:
            The current ISAFSession or None if not initialized
        """
        # If tenant_id provided, get from registry
        if tenant_id:
            with _registry_lock:
                return _session_registry.get(tenant_id)
        
        # Otherwise get from context
        return _current_session.get()
    
    @staticmethod
    def set_session(session: ISAFSession, tenant_id: Optional[str] = None) -> None:
        """
        Set the current session.
        
        Args:
            session: The ISAFSession to set as current
            tenant_id: Optional tenant ID to register session for
        """
        # Register if tenant_id provided
        if tenant_id:
            with _registry_lock:
                _session_registry[tenant_id] = session
        
        # Set in context
        _current_session.set(session)
    
    @staticmethod
    def clear_session(tenant_id: Optional[str] = None) -> None:
        """
        Clear the current session.
        
        Args:
            tenant_id: Optional tenant ID to clear specific tenant's session
        """
        if tenant_id:
            with _registry_lock:
                _session_registry.pop(tenant_id, None)
        else:
            _current_session.set(None)
    
    @staticmethod
    def get_all_sessions() -> Dict[str, ISAFSession]:
        """
        Get all registered sessions.
        
        Returns:
            Dictionary of tenant_id -> ISAFSession
        """
        with _registry_lock:
            return _session_registry.copy()
    
    @staticmethod
    def clear_all_sessions() -> None:
        """
        Clear all registered sessions.
        """
        with _registry_lock:
            _session_registry.clear()
        _current_session.set(None)


# Convenience functions for backward compatibility
def init(
    backend: str = 'sqlite',
    db_path: Optional[str] = None,
    auto_log_framework: bool = True,
    tenant_id: Optional[str] = None,
    **config: Any
) -> ISAFSession:
    """
    Initialize ISAF logging session.
    
    Args:
        backend: Storage backend ('sqlite', 'mlflow', or 'memory')
        db_path: Path to database file (for sqlite backend)
        auto_log_framework: Automatically log Layer 6 on init
        tenant_id: Optional tenant identifier for multi-tenant scenarios
        **config: Additional configuration options
    
    Returns:
        The initialized ISAFSession
    
    Example:
        # Single-tenant
        isaf.init(backend='sqlite', db_path='my_lineage.db')
        
        # Multi-tenant
        isaf.init(backend='sqlite', tenant_id='customer-123')
    """
    return SessionManager.create_session(
        tenant_id=tenant_id,
        backend=backend,
        db_path=db_path,
        auto_log_framework=auto_log_framework,
        **config
    )


def get_session(tenant_id: Optional[str] = None) -> Optional[ISAFSession]:
    """
    Get the current session.
    
    Args:
        tenant_id: Optional tenant ID to get specific tenant's session
        
    Returns:
        The current ISAFSession or None if not initialized
    """
    return SessionManager.get_session(tenant_id)


def set_session(session: ISAFSession, tenant_id: Optional[str] = None) -> None:
    """
    Set the current session.
    
    Args:
        session: The ISAFSession to set as current
        tenant_id: Optional tenant ID to register session for
    """
    SessionManager.set_session(session, tenant_id)


def clear_session(tenant_id: Optional[str] = None) -> None:
    """
    Clear the current session.
    
    Args:
        tenant_id: Optional tenant ID to clear specific tenant's session
    """
    SessionManager.clear_session(tenant_id)
