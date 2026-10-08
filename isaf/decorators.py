"""
ISAF Decorators for automatic compliance logging.

Provides decorators to capture Layer 6 (Framework), Layer 7 (Data),
and Layer 8 (Objective) information from AI training code.
"""

import functools
import inspect
import hashlib
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime

F = TypeVar('F', bound=Callable[..., Any])


def _safe_get_source(func: Callable) -> Optional[str]:
    """Safely extract source code from a function."""
    try:
        return inspect.getsource(func)
    except (OSError, TypeError):
        return None


def _extract_arg_info(func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Extract argument names and values from function call."""
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    
    result = {}
    for name, value in bound.arguments.items():
        try:
            if hasattr(value, 'shape'):
                result[name] = {'type': type(value).__name__, 'shape': str(value.shape)}
            elif hasattr(value, '__len__') and not isinstance(value, str):
                result[name] = {'type': type(value).__name__, 'length': len(value)}
            else:
                result[name] = {'type': type(value).__name__, 'value': str(value)[:100]}
        except Exception:
            result[name] = {'type': type(value).__name__}
    
    return result


def _is_data_like(obj: Any) -> bool:
    """Check if object looks like training data."""
    if obj is None:
        return False
    
    type_name = type(obj).__name__.lower()
    data_types = ['dataframe', 'ndarray', 'tensor', 'dataset', 'dataloader']
    
    if any(dt in type_name for dt in data_types):
        return True
    
    if hasattr(obj, 'shape') or hasattr(obj, '__len__'):
        return True
    
    return False


def _compute_data_hash(data: Any, salt: Optional[str] = None) -> Optional[str]:
    """
    Compute a hash of the FULL dataset for provenance tracking.
    
    Uses chunked hashing to handle large datasets efficiently.
    Adds session ID as salt for uniqueness.
    
    Args:
        data: Data to hash (numpy array, DataFrame, tensor, etc.)
        salt: Optional salt (typically session ID)
        
    Returns:
        SHA-256 hash (full 64 characters) or None on error
    """
    try:
        hasher = hashlib.sha256()
        
        # Add salt if provided
        if salt:
            hasher.update(salt.encode())
        
        # Hash based on data type
        if hasattr(data, 'tobytes'):
            # NumPy arrays, tensors - hash ALL bytes in chunks
            bytes_data = data.tobytes()
            chunk_size = 1024 * 1024  # 1MB chunks
            for i in range(0, len(bytes_data), chunk_size):
                hasher.update(bytes_data[i:i + chunk_size])
        
        elif hasattr(data, 'values'):
            # Pandas DataFrames - hash ALL values
            # Convert to numpy and hash
            bytes_data = data.values.tobytes()
            chunk_size = 1024 * 1024
            for i in range(0, len(bytes_data), chunk_size):
                hasher.update(bytes_data[i:i + chunk_size])
        
        elif isinstance(data, (list, tuple)):
            # Lists/tuples - hash all elements
            for item in data:
                item_str = str(item).encode()
                hasher.update(item_str)
        
        else:
            # Fallback - hash full string representation
            data_str = str(data).encode()
            chunk_size = 1024 * 1024
            for i in range(0, len(data_str), chunk_size):
                hasher.update(data_str[i:i + chunk_size])
        
        return hasher.hexdigest()  # Full 64-character hash
        
    except Exception as e:
        # Log error instead of silent failure
        from isaf.error_logger import get_error_logger
        error_logger = get_error_logger()
        error_logger.log_error('data_hashing', e, {
            'data_type': type(data).__name__
        })
        return None


def log_objective(
    name: Optional[str] = None,
    constraints: Optional[List[str]] = None,
    justification: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator to log Layer 8 (Objective Function) information.
    
    Args:
        name: Name of the objective/loss function
        constraints: List of constraints or regularization terms
        justification: Business justification for this objective
    
    Example:
        @isaf.log_objective(name="cross_entropy", constraints=["L2_reg"])
        def train(model, data):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from isaf.session_manager import get_session
            from isaf.core.extractors import Layer8Extractor
            
            session = get_session()
            if session is None:
                return func(*args, **kwargs)
            
            try:
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'source_code': _safe_get_source(func),
                    'arguments': _extract_arg_info(func, args, kwargs),
                    'objective_name': name or func.__name__,
                    'constraints': constraints or [],
                    'justification': justification,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor = Layer8Extractor()
                layer_data = extractor.extract(context)
                session.log_layer(8, layer_data)
                
            except Exception as e:
                # CRITICAL: Log error instead of silent failure (EU AI Act Article 12)
                from isaf.error_logger import get_error_logger
                from isaf.fallback_storage import FallbackStorage
                
                error_logger = get_error_logger()
                error_logger.log_error('log_objective', e, {
                    'function': func.__name__,
                    'module': func.__module__
                })
                
                # Try fallback storage
                try:
                    fallback = FallbackStorage()
                    fallback.store(8, context, session_id=session.session_id)
                except Exception as fallback_error:
                    error_logger.log_error('fallback_storage', fallback_error)
            
            return func(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    return decorator


def log_data(
    source: Optional[str] = None,
    version: Optional[str] = None,
    **metadata: Any
) -> Callable[[F], F]:
    """
    Decorator to log Layer 7 (Training Data) information.
    
    Args:
        source: Data source identifier (e.g., "internal", "public", "vendor")
        version: Data version string
        **metadata: Additional metadata to log
    
    Example:
        @isaf.log_data(source="internal", version="2024-01")
        def load_training_data():
            return pd.read_csv("data.csv")
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from isaf.session_manager import get_session
            from isaf.core.extractors import Layer7Extractor
            
            result = func(*args, **kwargs)
            
            session = get_session()
            if session is None:
                return result
            
            try:
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'source': source,
                    'version': version,
                    'metadata': metadata,
                    'returned_data': result,
                    'data_hash': _compute_data_hash(result, salt=session.session_id),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor = Layer7Extractor()
                layer_data = extractor.extract(context)
                session.log_layer(7, layer_data)
                
            except Exception as e:
                # CRITICAL: Log error instead of silent failure (EU AI Act Article 12)
                from isaf.error_logger import get_error_logger
                from isaf.fallback_storage import FallbackStorage
                
                error_logger = get_error_logger()
                error_logger.log_error('log_data', e, {
                    'function': func.__name__,
                    'module': func.__module__
                })
                
                # Try fallback storage
                try:
                    fallback = FallbackStorage()
                    fallback.store(7, context, session_id=session.session_id)
                except Exception as fallback_error:
                    error_logger.log_error('fallback_storage', fallback_error)
            
            return result
        
        return wrapper  # type: ignore
    
    return decorator


def log_framework(func: Optional[F] = None) -> Union[F, Callable[[F], F]]:
    """
    Decorator to log Layer 6 (Framework) information.
    
    Automatically detects PyTorch, TensorFlow, JAX, or scikit-learn
    and logs framework configuration, versions, and defaults.
    
    Example:
        @isaf.log_framework
        def build_model():
            return torch.nn.Sequential(...)
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            from isaf.session_manager import get_session
            from isaf.core.extractors import Layer6Extractor
            
            session = get_session()
            if session is None:
                return fn(*args, **kwargs)
            
            try:
                context = {
                    'function_name': fn.__name__,
                    'module': fn.__module__,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor = Layer6Extractor()
                layer_data = extractor.extract(context)
                session.log_layer(6, layer_data)
                
            except Exception as e:
                # CRITICAL: Log error instead of silent failure (EU AI Act Article 12)
                from isaf.error_logger import get_error_logger
                from isaf.fallback_storage import FallbackStorage
                
                error_logger = get_error_logger()
                error_logger.log_error('log_framework', e, {
                    'function': fn.__name__,
                    'module': fn.__module__
                })
                
                # Try fallback storage
                try:
                    fallback = FallbackStorage()
                    fallback.store(6, context, session_id=session.session_id)
                except Exception as fallback_error:
                    error_logger.log_error('fallback_storage', fallback_error)
            
            return fn(*args, **kwargs)
        
        return wrapper  # type: ignore
    
    if func is not None:
        return decorator(func)
    
    return decorator


def log_all(func: F) -> F:
    """
    Convenience decorator that logs all available layers.
    
    Logs Layer 6 (Framework) automatically, and attempts to log
    Layer 7 (Data) if the function returns data-like objects.
    
    Example:
        @isaf.log_all
        def train_pipeline():
            data = load_data()
            model = build_model()
            train(model, data)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from isaf.session_manager import get_session
        from isaf.core.extractors import Layer6Extractor, Layer7Extractor
        
        session = get_session()
        if session is None:
            return func(*args, **kwargs)
        
        try:
            context = {
                'function_name': func.__name__,
                'module': func.__module__,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            extractor6 = Layer6Extractor()
            layer6_data = extractor6.extract(context)
            session.log_layer(6, layer6_data)
            
        except Exception as e:
            # CRITICAL: Log error instead of silent failure (EU AI Act Article 12)
            from isaf.error_logger import get_error_logger
            error_logger = get_error_logger()
            error_logger.log_error('log_all_layer6', e, {
                'function': func.__name__,
                'module': func.__module__
            })
        
        result = func(*args, **kwargs)
        
        if _is_data_like(result):
            try:
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'returned_data': result,
                    'data_hash': _compute_data_hash(result, salt=session.session_id),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor7 = Layer7Extractor()
                layer7_data = extractor7.extract(context)
                session.log_layer(7, layer7_data)
                
            except Exception as e:
                # CRITICAL: Log error instead of silent failure (EU AI Act Article 12)
                from isaf.error_logger import get_error_logger
                error_logger = get_error_logger()
                error_logger.log_error('log_all_layer7', e, {
                    'function': func.__name__,
                    'module': func.__module__
                })
        
        return result
    
    return wrapper  # type: ignore
