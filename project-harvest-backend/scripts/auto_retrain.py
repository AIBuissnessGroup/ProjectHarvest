"""
Automated Model Retraining Script
==================================
Automatically retrains ML models when enough new data is collected.
Only deploys new models if they perform better than current ones.

Usage:
    python scripts/auto_retrain.py
    python scripts/auto_retrain.py --force  # Retrain even if not enough new data
    python scripts/auto_retrain.py --dry-run  # Check without actually retraining
"""

import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================
# Configuration
# ============================================

MODELS_DIR = Path(__file__).parent.parent / "data" / "models"
HISTORICAL_DIR = Path(__file__).parent.parent / "data" / "historical"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
TRAINING_LOG_FILE = MODELS_DIR / "training_log.json"

# Minimum days of new data before retraining
MIN_NEW_DAYS = 7

# Minimum improvement required to deploy new model
MIN_R2_IMPROVEMENT = 0.01  # 1% improvement required


# ============================================
# Training Status Functions
# ============================================

def get_last_training_info() -> Dict:
    """Get info about the last training run."""
    if TRAINING_LOG_FILE.exists():
        with open(TRAINING_LOG_FILE) as f:
            return json.load(f)
    return {
        "last_training_date": None,
        "last_data_date": None,
        "models_trained": [],
        "performance": {}
    }


def save_training_info(info: Dict):
    """Save training run info."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRAINING_LOG_FILE, 'w') as f:
        json.dump(info, f, indent=2)


def get_new_data_days() -> int:
    """Count days of new data since last training."""
    last_info = get_last_training_info()
    last_date_str = last_info.get("last_data_date")
    
    if not last_date_str:
        # No previous training, count all available data
        return count_total_data_days()
    
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
    
    # Count unique dates in historical data after last training
    new_days = set()
    for map_dir in HISTORICAL_DIR.iterdir():
        if map_dir.is_dir() and not map_dir.name.startswith("_"):
            for file in map_dir.glob("*.json"):
                try:
                    file_date = datetime.strptime(file.stem, "%Y-%m-%d")
                    if file_date > last_date:
                        new_days.add(file.stem)
                except:
                    continue
    
    return len(new_days)


def count_total_data_days() -> int:
    """Count total unique days of historical data."""
    all_days = set()
    for map_dir in HISTORICAL_DIR.iterdir():
        if map_dir.is_dir() and not map_dir.name.startswith("_"):
            for file in map_dir.glob("*.json"):
                all_days.add(file.stem)
    return len(all_days)


# ============================================
# Data Preparation Functions
# ============================================

def load_training_data() -> pd.DataFrame:
    """
    Load all available data for training.
    Combines raw data with historical snapshots.
    """
    all_features = []
    
    # Load from raw data (original fncreate.gg data)
    print("📂 Loading raw data...")
    for file in RAW_DIR.glob("map_*.json"):
        try:
            features = extract_features_from_file(file)
            if features:
                all_features.append(features)
        except Exception as e:
            continue
    
    # Load from historical data (daily snapshots)
    print("📂 Loading historical data...")
    for map_dir in HISTORICAL_DIR.iterdir():
        if map_dir.is_dir() and not map_dir.name.startswith("_"):
            try:
                features = extract_features_from_historical(map_dir)
                if features:
                    # Check if we already have this map from raw data
                    existing = [f for f in all_features if f.get('map_code') == features.get('map_code')]
                    if existing:
                        # Update with historical data (more recent)
                        idx = all_features.index(existing[0])
                        all_features[idx].update(features)
                    else:
                        all_features.append(features)
            except Exception as e:
                continue
    
    print(f"✅ Loaded {len(all_features)} maps for training")
    return pd.DataFrame(all_features)


def extract_features_from_file(file_path: Path) -> Optional[Dict]:
    """Extract features from a raw map data file."""
    with open(file_path) as f:
        data = json.load(f)
    
    map_data = data.get('map_data', {})
    stats_7d = data.get('stats_7d', {})
    
    if not stats_7d.get('success'):
        return None
    
    ccu_values = stats_7d.get('data', {}).get('stats', [])
    if len(ccu_values) < 50:
        return None
    
    # Split for prediction (85% train, 15% "future")
    split_point = int(len(ccu_values) * 0.85)
    training_data = ccu_values[:split_point]
    future_data = ccu_values[split_point:]
    
    features = {
        'map_code': map_data.get('mnemonic', ''),
        'creator_followers': map_data.get('creator', {}).get('followers', 0),
        'in_discovery': 1 if map_data.get('discovery', False) else 0,
        'xp_enabled': 1 if map_data.get('xpEnabled', False) else 0,
        'num_tags': len(map_data.get('tags', [])),
        'max_players': map_data.get('maxPlayers', 0),
        'version': map_data.get('version', 1),
        'baseline_ccu': np.mean(training_data),
        'future_ccu_7d': np.mean(future_data),
        'volatility': np.std(training_data),
    }
    
    # Trend slope
    if len(training_data) > 1:
        x = np.arange(len(training_data))
        slope, _ = np.polyfit(x, training_data, 1)
        features['trend_slope'] = slope
    else:
        features['trend_slope'] = 0
    
    # Recent momentum
    recent_idx = int(len(training_data) * 0.8)
    early_idx = int(len(training_data) * 0.2)
    recent_avg = np.mean(training_data[recent_idx:])
    early_avg = np.mean(training_data[:early_idx]) if early_idx > 0 else 0
    features['recent_momentum'] = recent_avg - early_avg if early_avg > 0 else 0
    
    # Map age
    created_at = map_data.get('createdAt')
    if created_at:
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            features['map_age_days'] = (datetime.now() - created_date).days
        except:
            features['map_age_days'] = 0
    else:
        features['map_age_days'] = 0
    
    return features


def extract_features_from_historical(map_dir: Path) -> Optional[Dict]:
    """Extract features from historical data for a map."""
    # Get all snapshots sorted by date
    snapshots = []
    for file in sorted(map_dir.glob("*.json")):
        try:
            with open(file) as f:
                snapshots.append(json.load(f))
        except:
            continue
    
    if len(snapshots) < 2:
        return None
    
    # Combine all CCU readings
    all_ccu = []
    for snapshot in snapshots:
        all_ccu.extend(snapshot.get('ccu_readings', []))
    
    if len(all_ccu) < 50:
        return None
    
    # Use combined data for features
    split_point = int(len(all_ccu) * 0.85)
    training_data = all_ccu[:split_point]
    future_data = all_ccu[split_point:]
    
    latest = snapshots[-1]
    
    # Extract map metadata (from new collection format)
    map_metadata = latest.get('map_metadata', {})
    creator_info = latest.get('creator', {})
    trend_features = latest.get('trend_features', {})
    
    features = {
        'map_code': latest.get('map_code', map_dir.name),
        'baseline_ccu': np.mean(training_data),
        'future_ccu_7d': np.mean(future_data),
        'volatility': np.std(training_data),
        'historical_days': len(snapshots),
        
        # Map metadata (if available from new collection format)
        'creator_followers': map_metadata.get('creator_followers', creator_info.get('followers', 0)),
        'in_discovery': map_metadata.get('in_discovery', 0),
        'xp_enabled': map_metadata.get('xp_enabled', 0),
        'num_tags': map_metadata.get('num_tags', 0),
        'max_players': map_metadata.get('max_players', 0),
        'version': map_metadata.get('version', 1),
    }
    
    # Calculate map age if created_at is available
    created_at = map_metadata.get('created_at', '')
    if created_at:
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            features['map_age_days'] = (datetime.now() - created_date).days
        except:
            features['map_age_days'] = 0
    else:
        features['map_age_days'] = 0
    
    # Trend slope from full history
    if len(training_data) > 1:
        x = np.arange(len(training_data))
        slope, _ = np.polyfit(x, training_data, 1)
        features['trend_slope'] = slope
    else:
        features['trend_slope'] = 0
    
    # Recent momentum
    recent_idx = int(len(training_data) * 0.8)
    early_idx = int(len(training_data) * 0.2)
    recent_avg = np.mean(training_data[recent_idx:])
    early_avg = np.mean(training_data[:early_idx]) if early_idx > 0 else 0
    features['recent_momentum'] = recent_avg - early_avg if early_avg > 0 else 0
    
    return features


# ============================================
# Model Training Functions
# ============================================

def train_future_ccu_model(df: pd.DataFrame) -> Tuple[any, Dict]:
    """
    Train the Future CCU prediction model.
    
    Returns:
        (trained_model, performance_metrics)
    """
    print("\n🚀 Training Future CCU Model...")
    
    # Filter valid data
    df = df[df['baseline_ccu'] > 0]
    df = df[df['future_ccu_7d'] > 0]
    
    # Feature columns
    feature_cols = [
        'baseline_ccu', 'trend_slope', 'recent_momentum', 
        'volatility', 'map_age_days'
    ]
    
    # Filter to available columns
    available_cols = [c for c in feature_cols if c in df.columns]
    
    # Fill missing values
    for col in available_cols:
        df[col] = df[col].fillna(0)
    
    X = df[available_cols]
    y = df['future_ccu_7d']
    
    print(f"  📊 Training samples: {len(X)}")
    print(f"  📋 Features: {available_cols}")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train Random Forest
    model = RandomForestRegressor(
        n_estimators=100, 
        random_state=42, 
        n_jobs=-1,
        max_depth=10,
        min_samples_split=5
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"  ✅ R² Score: {r2:.4f}")
    print(f"  ✅ MAE: {mae:.2f} CCU")
    
    performance = {
        "r2_score": round(r2, 4),
        "mae": round(mae, 2),
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features": available_cols
    }
    
    return model, performance


def get_current_model_performance() -> Dict:
    """Get performance metrics of currently deployed model."""
    metadata_file = MODELS_DIR / "future_ccu_metadata.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
            return {
                "r2_score": metadata.get("test_r2", 0),
                "mae": metadata.get("test_mae", float('inf'))
            }
    return {"r2_score": 0, "mae": float('inf')}


# ============================================
# Model Deployment Functions
# ============================================

def backup_current_model():
    """Backup current model before replacing."""
    backup_dir = MODELS_DIR / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_backup = [
        "future_ccu_predictor.pkl",
        "future_ccu_encoders.pkl", 
        "future_ccu_metadata.json"
    ]
    
    for filename in files_to_backup:
        src = MODELS_DIR / filename
        if src.exists():
            shutil.copy(src, backup_dir / filename)
    
    print(f"  📦 Backed up current model to {backup_dir}")


def deploy_new_model(model, performance: Dict, feature_cols: List[str]):
    """Deploy the new trained model."""
    # Backup current model first
    backup_current_model()
    
    # Save new model
    joblib.dump(model, MODELS_DIR / "future_ccu_predictor.pkl")
    
    # Save metadata
    metadata = {
        "model_type": "RandomForestRegressor",
        "trained_date": datetime.now().isoformat(),
        "test_r2": performance["r2_score"],
        "test_mae": performance["mae"],
        "training_samples": performance["training_samples"],
        "features": feature_cols,
        "auto_trained": True
    }
    
    with open(MODELS_DIR / "future_ccu_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("  🚀 New model deployed!")


# ============================================
# Main Retraining Function
# ============================================

def auto_retrain(force: bool = False, dry_run: bool = False) -> Dict:
    """
    Main auto-retraining function.
    
    Args:
        force: Retrain even if not enough new data
        dry_run: Check without actually retraining
    
    Returns:
        Summary of retraining results
    """
    print("=" * 60)
    print("🤖 Automated Model Retraining")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "action": "none",
        "reason": "",
        "new_performance": None,
        "old_performance": None
    }
    
    # Check how much new data we have
    new_days = get_new_data_days()
    total_days = count_total_data_days()
    
    print(f"\n📊 Data Status:")
    print(f"  Total historical days: {total_days}")
    print(f"  New days since last training: {new_days}")
    print(f"  Minimum required: {MIN_NEW_DAYS}")
    
    # Check if retraining is needed
    if new_days < MIN_NEW_DAYS and not force:
        print(f"\n⏭️  Skipping: Not enough new data ({new_days} < {MIN_NEW_DAYS} days)")
        results["action"] = "skipped"
        results["reason"] = f"Not enough new data ({new_days} days)"
        return results
    
    if dry_run:
        print("\n🔍 Dry run mode - would retrain with current data")
        results["action"] = "dry_run"
        return results
    
    # Load training data
    print("\n📂 Loading training data...")
    df = load_training_data()
    
    if len(df) < 50:
        print(f"❌ Not enough training samples ({len(df)} < 50)")
        results["action"] = "failed"
        results["reason"] = "Not enough training samples"
        return results
    
    # Get current model performance
    current_perf = get_current_model_performance()
    results["old_performance"] = current_perf
    print(f"\n📈 Current model R²: {current_perf['r2_score']:.4f}")
    
    # Train new model
    new_model, new_perf = train_future_ccu_model(df)
    results["new_performance"] = new_perf
    
    # Compare performance
    improvement = new_perf["r2_score"] - current_perf["r2_score"]
    print(f"\n📊 Performance Comparison:")
    print(f"  Old R²: {current_perf['r2_score']:.4f}")
    print(f"  New R²: {new_perf['r2_score']:.4f}")
    print(f"  Improvement: {improvement:+.4f}")
    
    # Deploy if improved
    if improvement >= MIN_R2_IMPROVEMENT or force:
        print("\n✅ Deploying new model...")
        deploy_new_model(new_model, new_perf, new_perf["features"])
        results["action"] = "deployed"
        results["reason"] = f"Improved by {improvement:.4f}"
        
        # Update training log
        save_training_info({
            "last_training_date": datetime.now().strftime("%Y-%m-%d"),
            "last_data_date": datetime.now().strftime("%Y-%m-%d"),
            "models_trained": ["future_ccu_predictor"],
            "performance": new_perf
        })
    else:
        print(f"\n⏭️  Not deploying: Improvement ({improvement:.4f}) < minimum ({MIN_R2_IMPROVEMENT})")
        results["action"] = "not_deployed"
        results["reason"] = f"Insufficient improvement ({improvement:.4f})"
    
    print("\n" + "=" * 60)
    print("✅ Auto-retraining complete!")
    print("=" * 60)
    
    return results


# ============================================
# CLI Entry Point
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Automated model retraining")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force retrain even if not enough new data"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Check status without retraining"
    )
    
    args = parser.parse_args()
    
    results = auto_retrain(force=args.force, dry_run=args.dry_run)
    
    # Print summary
    print(f"\nResult: {results['action']}")
    if results['reason']:
        print(f"Reason: {results['reason']}")


if __name__ == "__main__":
    main()

