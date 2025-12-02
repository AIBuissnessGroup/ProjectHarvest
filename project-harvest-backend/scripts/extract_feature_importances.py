"""
Extract Feature Importances from Trained Models
================================================
This script extracts the actual feature importances from our trained ML models
and saves them to the metadata files so they can be used for explanations.

Run this script after training models to update the metadata with importances.
"""

import joblib
import json
from pathlib import Path

MODELS_DIR = Path("data/models")

def extract_future_ccu_importances():
    """Extract feature importances from the Future CCU model"""
    print("=" * 60)
    print("Extracting Feature Importances: Future CCU Predictor")
    print("=" * 60)
    
    # Load model and encoders
    model_path = MODELS_DIR / "future_ccu_predictor.pkl"
    encoders_path = MODELS_DIR / "future_ccu_encoders.pkl"
    metadata_path = MODELS_DIR / "future_ccu_metadata.json"
    
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return None
    
    print(f"📂 Loading model from {model_path}")
    model = joblib.load(model_path)
    
    print(f"📂 Loading encoders from {encoders_path}")
    encoders = joblib.load(encoders_path)
    
    # Get feature names
    feature_columns = encoders.get('feature_columns', [])
    print(f"\n📊 Features ({len(feature_columns)}):")
    for i, col in enumerate(feature_columns):
        print(f"   {i+1}. {col}")
    
    # Extract feature importances
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        print(f"\n✅ Model has feature_importances_ (Random Forest/Gradient Boosting)")
    elif hasattr(model, 'coef_'):
        # For Linear Regression, use absolute coefficients as importance proxy
        importances = abs(model.coef_)
        importances = importances / importances.sum()  # Normalize to sum to 1
        print(f"\n✅ Model has coef_ (Linear Regression) - using normalized absolute coefficients")
    else:
        print(f"\n❌ Model does not have feature_importances_ or coef_")
        print(f"   Model type: {type(model)}")
        return None
    
    # Create importance dictionary
    importance_dict = {}
    for name, imp in zip(feature_columns, importances):
        importance_dict[name] = float(imp)
    
    # Sort by importance
    sorted_importances = sorted(importance_dict.items(), key=lambda x: -x[1])
    
    print(f"\n🏆 Feature Importances (sorted by importance):")
    print("-" * 50)
    for i, (name, imp) in enumerate(sorted_importances):
        bar = "█" * int(imp * 50)
        print(f"   {i+1:2}. {name:25} {imp:.4f} ({imp*100:5.1f}%) {bar}")
    
    # Load existing metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Add feature importances to metadata
    metadata['feature_importances'] = importance_dict
    metadata['feature_columns'] = feature_columns
    metadata['top_features'] = [name for name, _ in sorted_importances[:5]]
    
    # Save updated metadata
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Updated metadata saved to {metadata_path}")
    print(f"\n📈 Top 5 Most Important Features:")
    for i, (name, imp) in enumerate(sorted_importances[:5]):
        print(f"   {i+1}. {name}: {imp*100:.1f}%")
    
    return importance_dict


def extract_discovery_importances():
    """Extract feature importances from the Discovery Predictor model"""
    print("\n" + "=" * 60)
    print("Extracting Feature Importances: Discovery Predictor")
    print("=" * 60)
    
    model_path = MODELS_DIR / "discovery_predictor.pkl"
    encoders_path = MODELS_DIR / "discovery_encoders.pkl"
    metadata_path = MODELS_DIR / "discovery_metadata.json"
    
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return None
    
    print(f"📂 Loading model from {model_path}")
    model = joblib.load(model_path)
    
    print(f"📂 Loading encoders from {encoders_path}")
    encoders = joblib.load(encoders_path)
    
    feature_columns = encoders.get('feature_columns', [])
    print(f"\n📊 Features ({len(feature_columns)}):")
    for i, col in enumerate(feature_columns):
        print(f"   {i+1}. {col}")
    
    # Extract feature importances
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        print(f"\n✅ Model has feature_importances_")
    elif hasattr(model, 'coef_'):
        importances = abs(model.coef_[0] if len(model.coef_.shape) > 1 else model.coef_)
        importances = importances / importances.sum()
        print(f"\n✅ Model has coef_ - using normalized absolute coefficients")
    else:
        print(f"\n❌ Model does not have feature_importances_ or coef_")
        return None
    
    importance_dict = {}
    for name, imp in zip(feature_columns, importances):
        importance_dict[name] = float(imp)
    
    sorted_importances = sorted(importance_dict.items(), key=lambda x: -x[1])
    
    print(f"\n🏆 Feature Importances (sorted):")
    print("-" * 50)
    for i, (name, imp) in enumerate(sorted_importances):
        bar = "█" * int(imp * 50)
        print(f"   {i+1:2}. {name:25} {imp:.4f} ({imp*100:5.1f}%) {bar}")
    
    # Load and update metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    metadata['feature_importances'] = importance_dict
    metadata['feature_columns'] = feature_columns
    metadata['top_features'] = [name for name, _ in sorted_importances[:5]]
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Updated metadata saved to {metadata_path}")
    
    return importance_dict


if __name__ == "__main__":
    print("\n🔬 Feature Importance Extraction Tool")
    print("=" * 60)
    
    # Extract from all models
    future_ccu_imp = extract_future_ccu_importances()
    discovery_imp = extract_discovery_importances()
    
    print("\n" + "=" * 60)
    print("✅ DONE! Feature importances extracted and saved to metadata files.")
    print("=" * 60)
    print("\nThe ml_service.py can now use these importances to explain predictions.")

