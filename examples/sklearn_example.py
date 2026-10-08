"""
ISAF Logger - scikit-learn Example

Demonstrates ISAF logging with a RandomForest classifier.
"""

import sys
sys.path.insert(0, '..')

import isaf
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


isaf.init(backend='memory', auto_log_framework=True)


@isaf.log_data(source='synthetic', version='1.0')
def load_data():
    """Generate synthetic classification data."""
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        random_state=42
    )
    return X, y


@isaf.log_objective(
    name='gini_impurity',
    constraints=['max_depth=10', 'min_samples_split=5'],
    justification='Standard classification objective for interpretable model'
)
def train_model(X_train, y_train):
    """Train RandomForest classifier."""
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model


def main():
    print("ISAF Logger - scikit-learn Example")
    print("=" * 40)
    
    X, y = load_data()
    print(f"Data loaded: {X.shape[0]} samples, {X.shape[1]} features")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model = train_model(X_train, y_train)
    print("Model trained")
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {accuracy:.4f}")
    
    lineage = isaf.get_lineage()
    print(f"\nLineage captured:")
    print(f"  Session ID: {lineage['session_id'][:8]}...")
    print(f"  Layers logged: {list(lineage['layers'].keys())}")
    
    output_path = isaf.export(
        'sklearn_lineage.json',
        include_hash_chain=True,
        compliance_mappings=['eu_ai_act', 'nist_ai_rmf']
    )
    print(f"\nExported to: {output_path}")
    
    verified = isaf.verify_lineage('sklearn_lineage.json')
    print(f"Verification: {'PASSED' if verified else 'FAILED'}")


if __name__ == '__main__':
    main()
