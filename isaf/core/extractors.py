"""
ISAF Layer Extractors

Extracts structured data for Layers 6, 7, and 8 of the instruction stack.
"""

import sys
import platform
from datetime import datetime
from typing import Any, Dict, List, Optional


class Layer6Extractor:
    """
    Extracts Layer 6 (Framework) information.
    
    Detects ML frameworks, versions, default configurations,
    and system environment details.
    """
    
    FRAMEWORK_MODULES = {
        'torch': 'PyTorch',
        'tensorflow': 'TensorFlow',
        'jax': 'JAX',
        'sklearn': 'scikit-learn',
        'xgboost': 'XGBoost',
        'lightgbm': 'LightGBM',
        'transformers': 'Hugging Face Transformers'
    }
    
    def extract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Layer 6 data from context."""
        return {
            'layer': 6,
            'layer_name': 'Framework Configuration',
            'extracted_at': datetime.utcnow().isoformat(),
            'frameworks': self._detect_frameworks(),
            'defaults': self._extract_defaults(),
            'precision': self._detect_precision(),
            'dependencies': self._extract_dependencies(),
            'system': self._get_system_info(),
            'context': {
                'function': context.get('function_name'),
                'module': context.get('module')
            }
        }
    
    def _detect_frameworks(self) -> List[Dict[str, Any]]:
        """Detect installed ML frameworks."""
        frameworks = []
        
        for module_name, display_name in self.FRAMEWORK_MODULES.items():
            if module_name in sys.modules:
                module = sys.modules[module_name]
                version = getattr(module, '__version__', 'unknown')
                frameworks.append({
                    'name': display_name,
                    'module': module_name,
                    'version': version,
                    'loaded': True
                })
        
        return frameworks
    
    def _extract_defaults(self) -> Dict[str, Any]:
        """Extract framework default parameters."""
        defaults = {}
        
        if 'torch' in sys.modules:
            import torch
            defaults['pytorch'] = {
                'default_dtype': str(torch.get_default_dtype()),
                'cuda_available': torch.cuda.is_available(),
                'cuda_device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
                'cudnn_enabled': torch.backends.cudnn.enabled if hasattr(torch.backends, 'cudnn') else None
            }
        
        if 'tensorflow' in sys.modules:
            try:
                import tensorflow as tf
                defaults['tensorflow'] = {
                    'eager_execution': tf.executing_eagerly(),
                    'gpu_available': len(tf.config.list_physical_devices('GPU')) > 0,
                    'gpu_count': len(tf.config.list_physical_devices('GPU'))
                }
            except Exception:
                pass
        
        return defaults
    
    def _detect_precision(self) -> Dict[str, Any]:
        """Detect numerical precision settings."""
        precision = {
            'default': 'float32'
        }
        
        if 'torch' in sys.modules:
            import torch
            dtype = torch.get_default_dtype()
            precision['pytorch'] = str(dtype).replace('torch.', '')
        
        if 'numpy' in sys.modules:
            import numpy as np
            precision['numpy'] = str(np.float_.__name__)
        
        return precision
    
    def _extract_dependencies(self) -> List[Dict[str, str]]:
        """Extract relevant package versions."""
        deps = []
        packages = ['numpy', 'pandas', 'scipy', 'torch', 'tensorflow', 
                    'sklearn', 'transformers', 'datasets']
        
        for pkg in packages:
            if pkg in sys.modules:
                module = sys.modules[pkg]
                version = getattr(module, '__version__', 'unknown')
                deps.append({'package': pkg, 'version': version})
        
        return deps
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system environment information."""
        return {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'processor': platform.processor(),
            'machine': platform.machine()
        }


class Layer7Extractor:
    """
    Extracts Layer 7 (Training Data) information.
    
    Analyzes datasets, preprocessing steps, and data provenance.
    """
    
    def extract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Layer 7 data from context."""
        data_obj = context.get('returned_data')
        
        return {
            'layer': 7,
            'layer_name': 'Training Data',
            'extracted_at': datetime.utcnow().isoformat(),
            'datasets': self._analyze_datasets(data_obj, context),
            'preprocessing': self._extract_preprocessing(context),
            'provenance': self._extract_provenance(context),
            'context': {
                'function': context.get('function_name'),
                'module': context.get('module'),
                'source': context.get('source'),
                'version': context.get('version')
            }
        }
    
    def _analyze_datasets(self, data_obj: Any, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze dataset characteristics."""
        if data_obj is None:
            return []
        
        datasets = []
        dataset_info: Dict[str, Any] = {
            'type': type(data_obj).__name__,
            'data_hash': context.get('data_hash')
        }
        
        if hasattr(data_obj, 'shape'):
            dataset_info['shape'] = list(data_obj.shape)
        
        if hasattr(data_obj, 'dtype'):
            dataset_info['dtype'] = str(data_obj.dtype)
        
        if hasattr(data_obj, 'dtypes'):
            dataset_info['dtypes'] = {str(k): str(v) for k, v in data_obj.dtypes.items()}
        
        if hasattr(data_obj, 'columns'):
            dataset_info['columns'] = list(data_obj.columns)[:50]
            dataset_info['column_count'] = len(data_obj.columns)
        
        if hasattr(data_obj, '__len__'):
            try:
                dataset_info['length'] = len(data_obj)
            except Exception:
                pass
        
        if hasattr(data_obj, 'isnull'):
            try:
                null_counts = data_obj.isnull().sum()
                dataset_info['missing_values'] = int(null_counts.sum())
            except Exception:
                pass
        
        datasets.append(dataset_info)
        return datasets
    
    def _extract_preprocessing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract preprocessing information."""
        return {
            'steps': [],
            'metadata': context.get('metadata', {})
        }
    
    def _extract_provenance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data provenance information."""
        return {
            'source': context.get('source', 'unknown'),
            'version': context.get('version'),
            'data_hash': context.get('data_hash'),
            'loaded_at': context.get('timestamp')
        }


class Layer8Extractor:
    """
    Extracts Layer 8 (Objective Function) information.
    
    Captures loss functions, constraints, hyperparameters,
    and optimization objectives.
    """
    
    LOSS_MAPPINGS = {
        'cross_entropy': 'H(p,q) = -Σ p(x) log q(x)',
        'mse': 'MSE = (1/n) Σ (y - ŷ)²',
        'mae': 'MAE = (1/n) Σ |y - ŷ|',
        'bce': 'BCE = -[y log(p) + (1-y) log(1-p)]',
        'nll': 'NLL = -Σ log P(y|x)',
        'hinge': 'L = max(0, 1 - y·f(x))',
        'huber': 'L = 0.5x² if |x|≤δ else δ(|x|-0.5δ)'
    }
    
    def extract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Layer 8 data from context."""
        return {
            'layer': 8,
            'layer_name': 'Objective Function',
            'extracted_at': datetime.utcnow().isoformat(),
            'objective': self._extract_objective(context),
            'constraints': self._extract_constraints(context),
            'hyperparameters': self._extract_hyperparameters(context),
            'context': {
                'function': context.get('function_name'),
                'module': context.get('module'),
                'justification': context.get('justification')
            }
        }
    
    def _extract_objective(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract objective function details."""
        name = context.get('objective_name', 'unknown')
        
        mathematical_form = None
        for key, form in self.LOSS_MAPPINGS.items():
            if key in name.lower():
                mathematical_form = form
                break
        
        return {
            'name': name,
            'mathematical_form': mathematical_form,
            'source_code': context.get('source_code'),
            'arguments': context.get('arguments', {})
        }
    
    def _extract_constraints(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract constraint information."""
        constraints = context.get('constraints', [])
        
        result = []
        for constraint in constraints:
            if isinstance(constraint, str):
                result.append({
                    'name': constraint,
                    'type': self._infer_constraint_type(constraint)
                })
            elif isinstance(constraint, dict):
                result.append(constraint)
        
        return result
    
    def _extract_hyperparameters(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hyperparameters from arguments."""
        args = context.get('arguments', {})
        hyperparams = {}
        
        hp_keywords = ['lr', 'learning_rate', 'epochs', 'batch_size', 
                       'weight_decay', 'momentum', 'dropout', 'hidden_size',
                       'num_layers', 'optimizer', 'scheduler']
        
        for key, value in args.items():
            if any(hp in key.lower() for hp in hp_keywords):
                if isinstance(value, dict) and 'value' in value:
                    hyperparams[key] = value['value']
                else:
                    hyperparams[key] = value
        
        return hyperparams
    
    def _infer_constraint_type(self, constraint: str) -> str:
        """Infer the type of constraint from its name."""
        constraint_lower = constraint.lower()
        
        if 'l1' in constraint_lower or 'lasso' in constraint_lower:
            return 'L1_regularization'
        elif 'l2' in constraint_lower or 'ridge' in constraint_lower:
            return 'L2_regularization'
        elif 'dropout' in constraint_lower:
            return 'dropout_regularization'
        elif 'clip' in constraint_lower or 'gradient' in constraint_lower:
            return 'gradient_constraint'
        elif 'early' in constraint_lower or 'stop' in constraint_lower:
            return 'early_stopping'
        else:
            return 'custom'
