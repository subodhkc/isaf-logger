# haiec-isaf-logger

**Enterprise-grade compliance logging for AI systems with cryptographic verification.**

[![PyPI version](https://badge.fury.io/py/haiec-isaf-logger.svg)](https://badge.fury.io/py/haiec-isaf-logger)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.3.0-green.svg)](https://pypi.org/project/haiec-isaf-logger/)

## Use Cases

Automate AI compliance documentation and ensure regulatory readiness:

- **Regulatory Compliance**: Automatically generate EU AI Act, NIST AI RMF, and ISO 42001 documentation
- **Audit Trail Creation**: Complete cryptographic audit trails for AI model training and deployment
- **Data Provenance**: Track data lineage with cryptographic hashing for regulatory requirements
- **Multi-Tenant AI**: Isolated session management for SaaS AI platforms serving multiple customers
- **Risk Management**: Document AI system decisions with tamper-proof evidence

Add 3 lines of code, get compliance-ready documentation with cryptographic verification.

## Quick Start

```python
import isaf

# Initialize (one line)
isaf.init()

# Add decorators to your training functions
@isaf.log_data(source="customer_data", version="3.2.1")
def load_training_data():
    return pd.read_csv("data.csv")

@isaf.log_objective(name="binary_crossentropy", constraints=["fairness < 0.05"])
def train_model(data):
    model = create_model()
    model.fit(data)
    return model

# Run training as normal
data = load_training_data()
model = train_model(data)

# Export compliance report (one line)
isaf.export("compliance_report.json")
```

## Installation

```bash
pip install haiec-isaf-logger
```

## Features

- **3 Lines of Code**: Minimal integration with existing ML pipelines
- **Full Stack Coverage**: Logs Layer 6 (Framework), Layer 7 (Data), Layer 8 (Objectives)
- **Cryptographic Verification**: SHA-256 hash chains prove lineage integrity
- **Compliance Ready**: Maps to EU AI Act, NIST AI RMF, ISO 42001, Colorado AI Act
- **Framework Agnostic**: Works with PyTorch, TensorFlow, JAX, scikit-learn
- **Flexible Storage**: SQLite for local, MLflow for production

## What Gets Logged

### Layer 6: ML Framework
- Framework versions (PyTorch, TensorFlow, etc.)
- CUDA availability and configuration
- Default parameters and numerical precision
- System environment (Python version, OS, processor)

### Layer 7: Training Data
- Data source and version
- Dataset shape, dtypes, missing values
- Data hash for provenance tracking
- Preprocessing operations

### Layer 8: Objective Function
- Loss function name and mathematical form
- Constraints and regularization terms
- Hyperparameters (learning rate, batch size, etc.)
- Business justification

## Compliance Mappings

ISAF automatically maps your logged data to regulatory requirements:

- **EU AI Act**: Article 10 (Data Governance), Article 11 (Technical Documentation)
- **NIST AI RMF**: MEASURE-2.2, GOVERN-1.1
- **ISO 42001**: Section 8.4 (Control of externally provided AI)
- **Colorado AI Act**: SB24-205 (Impact Assessment Documentation)

## CLI Tools

```bash
# Inspect lineage file
isaf inspect compliance_report.json

# Verify cryptographic integrity
isaf verify compliance_report.json

# Export from database
isaf export-from-db lineage.db --output report.json

# List sessions
isaf list-sessions lineage.db
```

## Advanced Usage

### Custom Storage Backend

```python
# SQLite (default)
isaf.init(backend='sqlite', db_path='my_lineage.db')

# MLflow
isaf.init(backend='mlflow', tracking_uri='http://localhost:5000')

# Memory only (testing)
isaf.init(backend='memory')
```

### Automation Rules

```python
# Create automation rule
await ks.createRule({
    'metricName': 'accuracy',
    'thresholdValue': 0.70,
    'thresholdOperator': '<',
    'layer1Action': 'throttle_50',
    'minDurationSeconds': 30
})
```

### Compliance Export

```python
# Export with compliance mappings
isaf.export(
    'compliance_report.json',
    include_hash_chain=True,
    compliance_mappings=['eu_ai_act', 'nist_ai_rmf', 'iso_42001']
)
```

### Verification

```python
# Verify lineage integrity
verified = isaf.verify_lineage('compliance_report.json')
print(f"Verification: {'PASSED' if verified else 'FAILED'}")
```

## Examples

### PyTorch Example

```python
import torch
import isaf

isaf.init()

@isaf.log_data(source='internal', version='1.0')
def load_data():
    return torch.utils.data.TensorDataset(X, y)

@isaf.log_objective(name='cross_entropy')
def train(model, data):
    optimizer = torch.optim.Adam(model.parameters())
    for epoch in range(10):
        # training loop
        pass
    return model

data = load_data()
model = train(model, data)
isaf.export('pytorch_lineage.json')
```

### scikit-learn Example

```python
from sklearn.ensemble import RandomForestClassifier
import isaf

isaf.init()

@isaf.log_data(source='synthetic', version='1.0')
def load_data():
    from sklearn.datasets import make_classification
    return make_classification(n_samples=1000, n_features=20)

@isaf.log_objective(name='gini_impurity', constraints=['max_depth=10'])
def train_model(X, y):
    model = RandomForestClassifier(max_depth=10)
    model.fit(X, y)
    return model

X, y = load_data()
model = train_model(X, y)
isaf.export('sklearn_lineage.json')
```

## Documentation

- **Homepage**: https://haiec.com/isaf
- **Full Documentation**: https://haiec.com/isaf/docs
- **GitHub**: https://github.com/subodhkc/isaf-logger
- **Issues**: https://github.com/subodhkc/isaf-logger/issues

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use ISAF Logger in your research, please cite:

```bibtex
@software{isaf_logger,
  title = {ISAF Logger: Instruction Stack Audit Framework},
  author = {HAIEC Lab},
  year = {2025},
  url = {https://github.com/subodhkc/isaf-logger}
}
```

## Support

- **Email**: contact@haiec.com
- **Enterprise Support**: https://haiec.com/contact
- **Community**: GitHub Discussions

---

Built by [Subodh Kc](https://subodhkc.com) — a [HAIEC](https://haiec.com) (Human AI Evidence Company) product.
