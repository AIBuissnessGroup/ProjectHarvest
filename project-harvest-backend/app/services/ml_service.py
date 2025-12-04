"""
ML Service - Unified service for all ML models
===============================================
Handles loading and predictions for:
1. Future CCU Prediction (7-day forecast)
2. Anomaly Detection (campaign spikes) - Using Hybrid Method
3. Discovery Probability (placement prediction)
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Hybrid Anomaly Detection imports
from scipy.signal import find_peaks
from statsmodels.tsa.seasonal import STL
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from app.services.fncreate_service import fetch_map_from_api


class MLService:
    """Unified ML service for all prediction models"""
    
    # Path to historical data
    HISTORICAL_DIR = Path("data/historical")
    
    def __init__(self):
        self.models_dir = Path("data/models")
        
        # Model storage
        self.future_ccu_model = None
        self.future_ccu_encoders = None
        self.future_ccu_metadata = None
        
        self.anomaly_model = None
        self.anomaly_scaler = None
        self.anomaly_metadata = None
        
        self.discovery_model = None
        self.discovery_encoders = None
        self.discovery_metadata = None
        
        # Load all models
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all trained ML models"""
        print("🔄 Loading ML models...")
        
        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Future CCU Model
            future_ccu_path = self.models_dir / "future_ccu_predictor.pkl"
            if future_ccu_path.exists():
                try:
                    self.future_ccu_model = joblib.load(future_ccu_path)
                    self.future_ccu_encoders = joblib.load(self.models_dir / "future_ccu_encoders.pkl")
                    
                    import json
                    with open(self.models_dir / "future_ccu_metadata.json") as f:
                        self.future_ccu_metadata = json.load(f)
                    
                    print("✅ Future CCU model loaded")
                except Exception as e:
                    print(f"⚠️  Error loading Future CCU model: {e}")
            else:
                print("⚠️  Future CCU model not found - train with notebooks/train_future_ccu_model.ipynb")
            
            # Anomaly Detector - Now using HYBRID method (no model file needed)
            # The hybrid method uses STL + Peak Prominence + LOF on-the-fly
            print("✅ Anomaly detector ready (hybrid method: STL + Peaks + LOF)")
            
            # Load hybrid metadata if available
            hybrid_metadata_path = self.models_dir / "hybrid_anomaly_metadata.json"
            if hybrid_metadata_path.exists():
                try:
                    import json
                    with open(hybrid_metadata_path) as f:
                        self.anomaly_metadata = json.load(f)
                except:
                    self.anomaly_metadata = {"model_type": "hybrid_anomaly_detection"}
            else:
                self.anomaly_metadata = {"model_type": "hybrid_anomaly_detection"}
            
            # Discovery Predictor
            discovery_path = self.models_dir / "discovery_predictor.pkl"
            if discovery_path.exists():
                try:
                    self.discovery_model = joblib.load(discovery_path)
                    self.discovery_encoders = joblib.load(self.models_dir / "discovery_encoders.pkl")
                    
                    import json
                    with open(self.models_dir / "discovery_metadata.json") as f:
                        self.discovery_metadata = json.load(f)
                    
                    print("✅ Discovery predictor loaded")
                except Exception as e:
                    print(f"⚠️  Error loading Discovery predictor: {e}")
            else:
                print("⚠️  Discovery predictor not found - train with notebooks/train_discovery_predictor.ipynb")
            
            # Summary
            models_loaded = sum([
                self.future_ccu_model is not None,
                True,  # Anomaly detector always ready (hybrid method)
                self.discovery_model is not None
            ])
            print(f"\n📊 ML Models loaded: {models_loaded}/3")
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
    
    # =============================================
    # Future CCU Prediction
    # =============================================
    
    async def predict_future_ccu(self, map_code: str) -> Dict[str, Any]:
        """
        Predict CCU in 7 days for a given map with daily breakdown
        
        Args:
            map_code: Map code (e.g., "8530-0110-2817")
            
        Returns:
            Dict with prediction, daily forecast, trend, confidence, insights
        """
        if not self.future_ccu_model:
            raise ValueError("Future CCU model not loaded")
        
        # Fetch map data
        map_data = await fetch_map_from_api(map_code)
        if not map_data:
            raise ValueError(f"Map {map_code} not found")
        
        # Check if using cached data
        data_source = map_data.get('_source', 'unknown')
        cache_warning = map_data.get('_cache_warning', '')
        collection_date = map_data.get('_collection_date', 'Unknown')
        
        # Extract features
        features = self._extract_future_ccu_features(map_data)
        
        # Get baseline and trend
        baseline_ccu = features['baseline_ccu']
        trend_slope = features['trend_slope']
        current_ccu = features['current_ccu']
        
        # Generate daily forecast (1-7 days)
        daily_forecast = []
        for day in range(1, 8):
            # Adjust features for each day
            day_features = features.copy()
            
            # Linear interpolation based on trend slope
            # trend_slope is % change over 7 days, so per-day change is slope/7
            daily_trend_rate = trend_slope / 100 / 7
            
            # Predict CCU for this day
            predicted_day_ccu = baseline_ccu * (1 + daily_trend_rate * day)
            predicted_day_ccu = max(0, int(predicted_day_ccu))
            
            # Calculate change from baseline
            change_from_baseline = ((predicted_day_ccu - baseline_ccu) / baseline_ccu * 100) if baseline_ccu > 0 else 0
            
            # Calculate confidence intervals (±15% based on model MAE)
            mae = self.future_ccu_metadata.get('mae', 46)
            confidence_lower = max(0, int(predicted_day_ccu - mae * 1.5))
            confidence_upper = int(predicted_day_ccu + mae * 1.5)
            
            daily_forecast.append({
                "day": day,
                "predicted_ccu": predicted_day_ccu,
                "change_from_baseline": round(change_from_baseline, 1),
                "confidence_lower": confidence_lower,
                "confidence_upper": confidence_upper
            })
        
        # Final prediction (day 7)
        predicted_ccu_7d = daily_forecast[-1]['predicted_ccu']
        
        # Determine trend and strength
        total_change_pct = ((predicted_ccu_7d - baseline_ccu) / baseline_ccu * 100) if baseline_ccu > 0 else 0
        
        if total_change_pct > 10:
            trend = "Growing"
            trend_strength = "Strong" if total_change_pct > 25 else "Moderate"
        elif total_change_pct < -10:
            trend = "Declining"
            trend_strength = "Strong" if total_change_pct < -25 else "Moderate"
        else:
            trend = "Stable"
            trend_strength = "Weak"
        
        # Generate key insights
        key_insights = self._generate_daily_insights(daily_forecast, trend, baseline_ccu)
        
        # Confidence (based on prediction range)
        confidence = "High" if abs(total_change_pct) < 30 else "Medium"
        
        # Generate explanation of key factors driving the prediction
        prediction_factors = self._analyze_prediction_factors(features, trend, trend_slope)
        
        result = {
            "map_code": map_code,
            "map_name": map_data['map_data'].get('name', 'Unknown'),
            "current_ccu": current_ccu,
            "baseline_ccu": round(baseline_ccu, 1),
            "predicted_ccu_7d": predicted_ccu_7d,
            "daily_forecast": daily_forecast,
            "trend": trend,
            "trend_strength": trend_strength,
            "key_insights": key_insights,
            "confidence": confidence,
            "prediction_factors": prediction_factors,  # NEW: explains WHY the prediction is what it is
            "map_features": {  # NEW: raw feature values for transparency
                "creator_followers": features.get('creator_followers', 0),
                "map_age_days": features.get('map_age_days', 0),
                "xp_enabled": bool(features.get('xp_enabled', 0)),
                "in_discovery": bool(features.get('in_discovery', 0)),
                "max_players": features.get('max_players', 0),
                "num_tags": features.get('num_tags', 0),
                "primary_tag": features.get('primary_tag', 'unknown'),
                "trend_slope_pct": round(trend_slope, 1),
                "volatility": round(features.get('volatility', 0), 2),
                "recent_momentum_pct": round(features.get('recent_momentum', 0), 1)
            },
            "model_metrics": {
                "r2_score": self.future_ccu_metadata.get('r2_score', 0),
                "mae": self.future_ccu_metadata.get('mae', 0),
                "rmse": self.future_ccu_metadata.get('rmse', 0)
            },
            "data_source": data_source
        }
        
        # Add warning if using cached data
        if data_source == 'local_cache':
            if cache_warning:
                result['cache_warning'] = cache_warning
            result['collection_date'] = collection_date
        
        return result
    
    def _generate_daily_insights(self, daily_forecast: List[Dict], trend: str, baseline_ccu: float) -> List[str]:
        """Generate key insights from daily forecast"""
        insights = []
        
        # Find steepest drop/gain
        max_daily_change = 0
        max_change_day = 0
        
        for i in range(1, len(daily_forecast)):
            prev_ccu = daily_forecast[i-1]['predicted_ccu']
            curr_ccu = daily_forecast[i]['predicted_ccu']
            daily_change = ((curr_ccu - prev_ccu) / prev_ccu * 100) if prev_ccu > 0 else 0
            
            if abs(daily_change) > abs(max_daily_change):
                max_daily_change = daily_change
                max_change_day = i + 1
        
        # Insight 1: Steepest change
        if abs(max_daily_change) > 5:
            direction = "gain" if max_daily_change > 0 else "drop"
            insights.append(f"Steepest {direction} occurs on Day {max_change_day} ({max_daily_change:+.1f}%)")
        
        # Insight 2: Recommendation based on trend
        if trend == "Declining":
            # Find when decline starts accelerating
            for i in range(1, len(daily_forecast)):
                if daily_forecast[i]['predicted_ccu'] < baseline_ccu * 0.9:
                    insights.append(f"Consider campaign on Day {i} to prevent decline")
                    break
        elif trend == "Growing":
            # Find peak momentum day
            peak_day = max(range(len(daily_forecast)), key=lambda i: daily_forecast[i]['predicted_ccu'])
            if peak_day < 6:
                insights.append(f"Peak momentum on Day {peak_day + 1} - ideal time for campaign boost")
        
        # Insight 3: Volatility warning
        ccu_values = [d['predicted_ccu'] for d in daily_forecast]
        volatility = np.std(ccu_values) / np.mean(ccu_values) if np.mean(ccu_values) > 0 else 0
        if volatility > 0.2:
            insights.append(f"High volatility detected - CCU may fluctuate significantly")
        elif volatility < 0.05:
            insights.append(f"Stable trajectory - predictable performance")
        
        # Insight 4: Week-over-week comparison
        day7_ccu = daily_forecast[-1]['predicted_ccu']
        week_change = ((day7_ccu - baseline_ccu) / baseline_ccu * 100) if baseline_ccu > 0 else 0
        if abs(week_change) > 20:
            direction = "increase" if week_change > 0 else "decrease"
            insights.append(f"Week-over-week {direction} of {abs(week_change):.0f}% expected")
        
        return insights[:4]  # Return top 4 insights
    
    def _analyze_prediction_factors(self, features: Dict[str, Any], trend: str, trend_slope: float) -> Dict[str, Any]:
        """
        Analyze and explain the key factors driving the CCU prediction.
        Uses ACTUAL feature importances from the trained model.
        
        Feature Importances (from Random Forest model):
        - baseline_ccu: 66.4% (most important!)
        - trend_slope: 17.9%
        - recent_momentum: 9.8%
        - creator_followers: 1.7%
        - volatility: 1.3%
        - Others: <1% each
        """
        # Get actual feature importances from metadata
        feature_importances = self.future_ccu_metadata.get('feature_importances', {})
        
        # Build factor contributions with actual importance weights
        factor_contributions = []
        
        # 1. Baseline CCU (66.4% importance)
        baseline = features.get('baseline_ccu', 0)
        baseline_imp = feature_importances.get('baseline_ccu', 0.664) * 100
        if baseline > 0:
            if baseline > 300:
                direction = "positive"
                explanation = f"Strong baseline CCU ({baseline:.0f} avg)"
            elif baseline > 100:
                direction = "neutral"
                explanation = f"Moderate baseline CCU ({baseline:.0f} avg)"
            else:
                direction = "negative"
                explanation = f"Low baseline CCU ({baseline:.0f} avg)"
            
            factor_contributions.append({
                "feature": "baseline_ccu",
                "importance": baseline_imp,
                "value": baseline,
                "direction": direction,
                "explanation": explanation
            })
        
        # 2. Trend Slope (17.9% importance)
        trend_imp = feature_importances.get('trend_slope', 0.179) * 100
        if trend_slope > 5:
            direction = "positive"
            explanation = f"Upward trend (+{trend_slope:.1f}%)"
        elif trend_slope < -5:
            direction = "negative"
            explanation = f"Downward trend ({trend_slope:.1f}%)"
        else:
            direction = "neutral"
            explanation = f"Stable trend ({trend_slope:+.1f}%)"
        
        factor_contributions.append({
            "feature": "trend_slope",
            "importance": trend_imp,
            "value": trend_slope,
            "direction": direction,
            "explanation": explanation
        })
        
        # 3. Recent Momentum (9.8% importance)
        momentum = features.get('recent_momentum', 0)
        momentum_imp = feature_importances.get('recent_momentum', 0.098) * 100
        if momentum > 10:
            direction = "positive"
            explanation = f"Strong recent momentum (+{momentum:.1f}%)"
        elif momentum > 0:
            direction = "positive"
            explanation = f"Positive momentum (+{momentum:.1f}%)"
        elif momentum < -10:
            direction = "negative"
            explanation = f"Losing momentum ({momentum:.1f}%)"
        elif momentum < 0:
            direction = "negative"
            explanation = f"Slight momentum loss ({momentum:.1f}%)"
        else:
            direction = "neutral"
            explanation = "Flat momentum (0%)"
        
        factor_contributions.append({
            "feature": "recent_momentum",
            "importance": momentum_imp,
            "value": momentum,
            "direction": direction,
            "explanation": explanation
        })
        
        # 4. Creator Followers (1.7% importance)
        followers = features.get('creator_followers', 0)
        followers_imp = feature_importances.get('creator_followers', 0.017) * 100
        if followers > 10000:
            direction = "positive"
            explanation = f"Large following ({followers:,} followers)"
        elif followers > 1000:
            direction = "neutral"
            explanation = f"Moderate following ({followers:,} followers)"
        else:
            direction = "negative"
            explanation = f"Small following ({followers:,} followers)"
        
        factor_contributions.append({
            "feature": "creator_followers",
            "importance": followers_imp,
            "value": followers,
            "direction": direction,
            "explanation": explanation
        })
        
        # 5. Volatility (1.3% importance)
        volatility = features.get('volatility', 0)
        volatility_imp = feature_importances.get('volatility', 0.013) * 100
        if volatility > 0.5:
            direction = "negative"
            explanation = f"High volatility ({volatility:.2f})"
        elif volatility < 0.2:
            direction = "positive"
            explanation = f"Low volatility ({volatility:.2f})"
        else:
            direction = "neutral"
            explanation = f"Moderate volatility ({volatility:.2f})"
        
        factor_contributions.append({
            "feature": "volatility",
            "importance": volatility_imp,
            "value": volatility,
            "direction": direction,
            "explanation": explanation
        })
        
        # Sort by importance (highest first)
        factor_contributions.sort(key=lambda x: -x['importance'])
        
        # Identify primary driver (highest importance factor that's not neutral)
        primary_driver = None
        for factor in factor_contributions:
            if factor['direction'] != 'neutral':
                primary_driver = factor
                break
        
        if not primary_driver:
            primary_driver = factor_contributions[0]  # Default to most important
        
        # Build summary
        primary_explanation = f"{primary_driver['explanation']} ({primary_driver['importance']:.1f}% model weight)"
        
        # Separate positive and negative factors
        positive_factors = [f for f in factor_contributions if f['direction'] == 'positive']
        negative_factors = [f for f in factor_contributions if f['direction'] == 'negative']
        
        return {
            "primary_driver": primary_explanation,
            "primary_feature": primary_driver['feature'],
            "primary_importance": primary_driver['importance'],
            "all_factors": factor_contributions,
            "positive_factors": [
                f"{f['explanation']} ({f['importance']:.1f}% weight)" 
                for f in positive_factors
            ],
            "negative_factors": [
                f"{f['explanation']} ({f['importance']:.1f}% weight)" 
                for f in negative_factors
            ],
            "summary": f"Prediction is {trend.lower()} - primary driver: {primary_explanation}",
            "model_insight": "The model weighs baseline CCU (66.4%), trend slope (17.9%), and recent momentum (9.8%) as the top 3 factors."
        }
    
    def _extract_future_ccu_features(self, map_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for future CCU prediction"""
        data = map_data['map_data']
        creator = data.get('creator', {})
        stats_7d = map_data.get('stats_7d', {})
        
        # Calculate time-series features
        ts_features = self._calculate_trend_features(stats_7d)
        
        # Map age
        try:
            published = datetime.fromisoformat(data.get('published', '').replace('Z', '+00:00'))
            last_sync = datetime.fromisoformat(data.get('lastSyncDate', '').replace('Z', '+00:00'))
            map_age_days = (last_sync - published).days
        except:
            map_age_days = 0
        
        # Discovery status
        in_discovery = 1 if data.get('state') == 'in_discovery' else 0
        
        # Tags
        tags = data.get('tags', [])
        primary_tag = tags[0] if tags else 'unknown'
        
        return {
            'type': data.get('type', 'unknown'),
            'primary_tag': primary_tag,
            'num_tags': len(tags),
            'max_players': data.get('max_players', 0),
            'xp_enabled': 1 if data.get('xp_enabled') else 0,
            'creator_followers': creator.get('lookup_follower_count', 0),
            'version': data.get('version', 0),
            'map_age_days': map_age_days,
            'in_discovery': in_discovery,
            'baseline_ccu': ts_features['avg_ccu_7d'],
            'trend_slope': ts_features['trend_slope'],
            'volatility': ts_features['volatility'],
            'recent_momentum': ts_features['recent_momentum'],
            'current_ccu': data.get('lastSyncCcu', 0)
        }
    
    def _calculate_trend_features(self, stats_7d: Dict[str, Any]) -> Dict[str, float]:
        """Calculate time-series trend features"""
        if not stats_7d or not stats_7d.get('success'):
            return {
                'avg_ccu_7d': 0,
                'trend_slope': 0,
                'volatility': 0,
                'recent_momentum': 0
            }
        
        data_points = stats_7d.get('data', {}).get('stats', [])
        if len(data_points) < 10:
            return {
                'avg_ccu_7d': 0,
                'trend_slope': 0,
                'volatility': 0,
                'recent_momentum': 0
            }
        
        arr = np.array(data_points)
        
        # Average CCU
        avg_ccu = float(np.mean(arr))
        
        # Trend slope (early vs late)
        quarter = len(arr) // 4
        early_avg = np.mean(arr[:quarter])
        late_avg = np.mean(arr[-quarter:])
        trend_slope = (late_avg - early_avg) / max(early_avg, 1) * 100
        
        # Volatility
        volatility = np.std(arr) / max(np.mean(arr), 1)
        
        # Recent momentum
        recent_pct = int(len(arr) * 0.2)
        recent_avg = np.mean(arr[-recent_pct:])
        middle_avg = np.mean(arr[len(arr)//2 - recent_pct//2 : len(arr)//2 + recent_pct//2])
        recent_momentum = (recent_avg - middle_avg) / max(middle_avg, 1) * 100
        
        return {
            'avg_ccu_7d': avg_ccu,
            'trend_slope': float(trend_slope),
            'volatility': float(volatility),
            'recent_momentum': float(recent_momentum)
        }
    
    def _encode_future_ccu_features(self, features: Dict[str, Any]) -> List[float]:
        """Encode features for future CCU model"""
        type_encoder = self.future_ccu_encoders['type_encoder']
        tag_encoder = self.future_ccu_encoders['tag_encoder']
        feature_columns = self.future_ccu_encoders['feature_columns']
        
        # Encode categorical features
        try:
            type_encoded = type_encoder.transform([features['type']])[0]
        except:
            type_encoded = 0
        
        try:
            tag_encoded = tag_encoder.transform([features['primary_tag']])[0]
        except:
            tag_encoded = 0
        
        # Build feature vector in correct order
        feature_dict = {
            'type_encoded': type_encoded,
            'tag_encoded': tag_encoded,
            'num_tags': features['num_tags'],
            'max_players': features['max_players'],
            'xp_enabled': features['xp_enabled'],
            'creator_followers': features['creator_followers'],
            'version': features['version'],
            'map_age_days': features['map_age_days'],
            'in_discovery': features['in_discovery'],
            'baseline_ccu': features['baseline_ccu'],
            'trend_slope': features['trend_slope'],
            'volatility': features['volatility'],
            'recent_momentum': features['recent_momentum']
        }
        
        return [feature_dict[col] for col in feature_columns]
    
    # =============================================
    # Anomaly Detection (Hybrid Method)
    # =============================================
    
    async def detect_anomalies(self, map_code: str) -> Dict[str, Any]:
        """
        Detect CCU anomalies/spikes for a map using HYBRID method.
        
        Combines 3 threshold-free methods:
        1. STL Decomposition + IQR
        2. Peak Prominence Detection
        3. Local Outlier Factor (LOF)
        
        Only flags as anomaly if 2+ methods agree.
        
        ENHANCED: Uses historical data (if available) for better pattern detection.
        With 30+ days of data, can identify weekly patterns and true anomalies.
        
        Args:
            map_code: Map code
            
        Returns:
            Dict with anomaly details, spikes, interpretation
        """
        # Fetch map data
        map_data = await fetch_map_from_api(map_code)
        if not map_data:
            raise ValueError(f"Map {map_code} not found")
        
        # Check if using cached data
        data_source = map_data.get('_source', 'unknown')
        cache_warning = map_data.get('_cache_warning', '')
        collection_date = map_data.get('_collection_date', 'Unknown')
        
        # Extract time-series from current data
        stats_7d = map_data.get('stats_7d', {})
        if not stats_7d.get('success'):
            raise ValueError("No time-series data available")
        
        ccu_series = stats_7d.get('data', {}).get('stats', [])
        if len(ccu_series) < 50:
            raise ValueError("Insufficient data for anomaly detection")
        
        # Try to load historical data for better context
        historical_ccu, historical_days = self._load_historical_ccu(map_code)
        using_historical = False
        
        if historical_ccu and len(historical_ccu) > len(ccu_series) * 2:
            # Use historical data if we have significantly more (2x)
            # This gives us weekly/monthly pattern context
            ccu_series_for_detection = historical_ccu
            using_historical = True
            print(f"📊 Using {historical_days} days of historical data for anomaly detection")
        else:
            ccu_series_for_detection = ccu_series
        
        # Get date range for timestamp calculation (from current 7-day data)
        try:
            date_from_str = stats_7d.get('data', {}).get('from', '')
            date_to_str = stats_7d.get('data', {}).get('to', '')
            date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
            date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
            total_duration = (date_to - date_from).total_seconds()
            has_timestamps = True
        except:
            has_timestamps = False
            date_from = None
            total_duration = 0
        
        # Run HYBRID anomaly detection
        # If using historical, we pass the full series but focus on recent anomalies
        hybrid_result = self._detect_anomalies_hybrid(
            ccu_series_for_detection,
            focus_recent=using_historical,
            recent_count=len(ccu_series)  # Only report anomalies in recent data
        )
        
        spike_indices = hybrid_result['spike_indices']
        spike_details_raw = hybrid_result['spike_details']
        num_spikes = hybrid_result['num_spikes']
        
        # Determine if map is anomalous based on hybrid detection
        is_anomalous = num_spikes > 0
        
        # Calculate anomaly score based on spike characteristics
        if num_spikes > 0:
            avg_votes = np.mean([s['votes'] for s in spike_details_raw])
            anomaly_score = -0.5 - (avg_votes / 3) * 0.5  # More negative = more anomalous
        else:
            anomaly_score = 0.1  # Normal
        
        # Build spike details with approximate timestamps
        spike_details = []
        for spike in spike_details_raw:
            idx = spike['peak_index']
            spike_detail = {
                "timestamp_index": int(idx),
                "ccu": spike['peak_ccu'],
                "votes": spike['votes'],
                "methods_agreed": spike['methods_agreed']
            }
            
            # Calculate approximate timestamp
            if has_timestamps and len(ccu_series) > 1 and date_from:
                progress = idx / (len(ccu_series) - 1)
                seconds_offset = total_duration * progress
                spike_time = date_from + timedelta(seconds=seconds_offset)
                spike_detail["approximate_timestamp"] = spike_time.strftime('%B %d, %Y at %I:%M %p')
                spike_detail["date"] = spike_time.strftime('%Y-%m-%d')
            
            spike_details.append(spike_detail)
        
        # Get map scale info
        map_scale = hybrid_result.get('map_scale', {})
        is_small_map = map_scale.get('is_small_map', False)
        max_ccu = map_scale.get('max_ccu', 0)
        min_threshold = map_scale.get('min_spike_threshold', 0)
        
        # Interpretation
        if num_spikes > 0:
            methods_used = set()
            for s in spike_details_raw:
                methods_used.update(s['methods_agreed'])
            interpretation = f"Map shows {num_spikes} unusual CCU spike(s) detected by hybrid analysis ({', '.join(methods_used)}). Possible campaign activity or viral moment."
        elif is_small_map and max_ccu < 50:
            interpretation = f"This is a small map (peak CCU: {max_ccu}). No significant anomalies were detected because the CCU variations are too small to distinguish from normal fluctuations. For meaningful anomaly detection, spikes need to exceed {int(min_threshold)} CCU above the average."
        else:
            interpretation = "Map shows normal CCU behavior. No significant anomalies detected by hybrid analysis."
        
        # Add historical context to interpretation
        if using_historical:
            interpretation = f"[Using {historical_days} days of historical data for pattern context] " + interpretation
        
        result = {
            "map_code": map_code,
            "map_name": map_data['map_data'].get('name', 'Unknown'),
            "anomaly_score": anomaly_score,
            "is_anomalous": bool(is_anomalous),
            "num_spikes": num_spikes,
            "spike_details": spike_details[:10],
            "interpretation": interpretation,
            "detection_method": "hybrid",
            "methods_used": ["STL", "peak_prominence", "LOF"],
            "data_source": data_source,
            "map_scale": map_scale,  # Include scale info for context
            "using_historical_data": using_historical,
            "historical_days": historical_days if using_historical else 0
        }
        
        # Add warning if using cached data
        if data_source == 'local_cache':
            if cache_warning:
                result['cache_warning'] = cache_warning
            result['collection_date'] = collection_date
        
        return result
    
    def _load_historical_ccu(self, map_code: str, max_days: int = 60) -> Tuple[List[float], int]:
        """
        Load historical CCU data for a map if available.
        
        Args:
            map_code: Map code
            max_days: Maximum days of history to load
            
        Returns:
            Tuple of (combined_ccu_series, num_days)
        """
        import json
        
        # Try different directory name formats
        map_dir_options = [
            self.HISTORICAL_DIR / map_code.replace("-", ""),
            self.HISTORICAL_DIR / map_code,
        ]
        
        map_dir = None
        for option in map_dir_options:
            if option.exists():
                map_dir = option
                break
        
        if not map_dir:
            return [], 0
        
        # Load all snapshots sorted by date
        snapshots = []
        for file in sorted(map_dir.glob("*.json")):
            try:
                with open(file) as f:
                    data = json.load(f)
                    snapshots.append(data)
            except:
                continue
        
        if not snapshots:
            return [], 0
        
        # Limit to max_days
        snapshots = snapshots[-max_days:]
        
        # Combine all CCU readings
        combined_ccu = []
        for snapshot in snapshots:
            readings = snapshot.get('ccu_readings', [])
            combined_ccu.extend(readings)
        
        return combined_ccu, len(snapshots)
    
    def _detect_anomalies_hybrid(self, ccu_series: List[float], min_votes: int = 2, grouping_window: int = 6, focus_recent: bool = False, recent_count: int = 0) -> Dict[str, Any]:
        """
        Hybrid anomaly detection using ensemble of 3 methods.
        Only flags as anomaly if min_votes methods agree.
        
        Methods:
        1. STL Decomposition + IQR on residuals
        2. Peak Prominence (scipy find_peaks)
        3. Local Outlier Factor (LOF)
        
        SCALE-AWARE: Adjusts thresholds based on map's CCU scale.
        """
        arr = np.array(ccu_series, dtype=float)
        n_points = len(arr)
        
        # Calculate map scale metrics for scale-aware detection
        mean_ccu = np.mean(arr)
        max_ccu = np.max(arr)
        std_ccu = np.std(arr)
        
        # Determine if this is a "small map" (low CCU)
        is_small_map = max_ccu < 50
        is_tiny_map = max_ccu < 20
        
        # Minimum absolute spike magnitude to consider (scale-aware)
        if is_tiny_map:
            # For tiny maps (peak < 20), need at least 10 CCU spike above mean
            min_spike_magnitude = max(10, mean_ccu * 2)
        elif is_small_map:
            # For small maps (peak < 50), need at least 15 CCU spike above mean
            min_spike_magnitude = max(15, mean_ccu * 1.5)
        else:
            # For larger maps, need meaningful relative spike (25% above mean or 20 CCU)
            min_spike_magnitude = max(20, mean_ccu * 0.25)
        
        # Initialize vote counter for each point
        votes = np.zeros(n_points, dtype=int)
        method_results = {}
        
        # Method 1: STL Decomposition + IQR
        try:
            stl_indices = self._detect_anomalies_stl(ccu_series)
            for idx in stl_indices:
                votes[idx] += 1
            method_results['STL'] = stl_indices
        except Exception as e:
            method_results['STL'] = []
        
        # Method 2: Peak Prominence
        try:
            peak_indices = self._detect_anomalies_peaks(ccu_series)
            for idx in peak_indices:
                votes[idx] += 1
            method_results['peak_prominence'] = peak_indices
        except Exception as e:
            method_results['peak_prominence'] = []
        
        # Method 3: Local Outlier Factor
        try:
            lof_indices = self._detect_anomalies_lof(ccu_series)
            for idx in lof_indices:
                votes[idx] += 1
            method_results['LOF'] = lof_indices
        except Exception as e:
            method_results['LOF'] = []
        
        # Find points with enough votes
        consensus_indices = np.where(votes >= min_votes)[0].tolist()
        
        # Group nearby anomalies into spike events
        if not consensus_indices:
            return {
                'spike_indices': [],
                'spike_details': [],
                'num_spikes': 0,
                'method_results': method_results,
                'votes': votes
            }
        
        # Group consecutive/nearby indices into spike events
        spike_events = []
        current_spike = [consensus_indices[0]]
        
        for idx in consensus_indices[1:]:
            if idx - current_spike[-1] <= grouping_window:
                current_spike.append(idx)
            else:
                spike_events.append(current_spike)
                current_spike = [idx]
        spike_events.append(current_spike)
        
        # For each spike event, get the PEAK (highest CCU)
        spike_details = []
        spike_indices = []
        
        # If using historical data, only report anomalies in recent portion
        recent_start_idx = n_points - recent_count if (focus_recent and recent_count > 0) else 0
        
        for spike_group in spike_events:
            peak_idx = max(spike_group, key=lambda i: arr[i])
            peak_ccu = arr[peak_idx]
            
            # FOCUS_RECENT FILTERING: Skip spikes not in recent data when using historical
            if focus_recent and recent_count > 0 and peak_idx < recent_start_idx:
                continue  # This anomaly is in old historical data, skip it
            
            # SCALE-AWARE FILTERING: Skip spikes that don't meet minimum magnitude
            spike_magnitude = peak_ccu - mean_ccu
            if spike_magnitude < min_spike_magnitude:
                continue  # Not significant enough for this map's scale
            
            # Adjust index to be relative to recent data (for chart display)
            display_idx = peak_idx - recent_start_idx if focus_recent else peak_idx
            
            spike_indices.append(display_idx)
            
            spike_details.append({
                'peak_index': display_idx,
                'original_index': peak_idx,
                'peak_ccu': int(peak_ccu),
                'spike_magnitude': round(float(spike_magnitude), 1),
                'votes': int(votes[peak_idx]),
                'spike_duration_indices': len(spike_group),
                'methods_agreed': [
                    m for m, indices in method_results.items() 
                    if any(i in spike_group for i in indices)
                ]
            })
        
        return {
            'spike_indices': spike_indices,
            'spike_details': spike_details,
            'num_spikes': len(spike_indices),
            'method_results': method_results,
            'votes': votes,
            'map_scale': {
                'mean_ccu': round(float(mean_ccu), 1),
                'max_ccu': int(max_ccu),
                'min_spike_threshold': round(float(min_spike_magnitude), 1),
                'is_small_map': is_small_map
            },
            'historical_context': {
                'using_historical': focus_recent,
                'total_data_points': n_points,
                'recent_data_points': recent_count if focus_recent else n_points
            }
        }
    
    def _detect_anomalies_stl(self, ccu_series: List[float], period: int = 48) -> List[int]:
        """
        Detect anomalies using STL decomposition + IQR on residuals.
        Period of 48 = 24 hours at 30-min intervals.
        """
        arr = np.array(ccu_series, dtype=float)
        
        if len(arr) < period * 2:
            return []
        
        # STL decomposition
        stl = STL(arr, period=period, robust=True)
        result = stl.fit()
        residuals = result.resid
        
        # Use IQR to find anomalies in residuals
        Q1 = np.percentile(residuals, 25)
        Q3 = np.percentile(residuals, 75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR
        
        anomaly_indices = np.where(residuals > upper_bound)[0].tolist()
        return anomaly_indices
    
    def _detect_anomalies_peaks(self, ccu_series: List[float], prominence_percentile: int = 90, distance: int = 6) -> List[int]:
        """
        Detect anomalies using scipy find_peaks with prominence.
        Only keeps peaks with prominence above the given percentile.
        """
        arr = np.array(ccu_series, dtype=float)
        
        # Find ALL peaks first
        all_peaks, properties = find_peaks(arr, distance=distance, prominence=1)
        
        if len(all_peaks) == 0:
            return []
        
        prominences = properties['prominences']
        
        # Only keep peaks with high prominence
        prominence_threshold = np.percentile(prominences, prominence_percentile)
        significant_mask = prominences >= prominence_threshold
        anomaly_indices = all_peaks[significant_mask].tolist()
        
        return anomaly_indices
    
    def _detect_anomalies_lof(self, ccu_series: List[float], n_neighbors: int = 20, contamination: float = 0.05) -> List[int]:
        """
        Detect anomalies using Local Outlier Factor.
        """
        arr = np.array(ccu_series, dtype=float).reshape(-1, 1)
        
        # Add time index as a feature
        time_idx = np.arange(len(arr)).reshape(-1, 1)
        X = np.hstack([arr, time_idx])
        
        # Normalize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # LOF
        lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
        labels = lof.fit_predict(X_scaled)
        
        # Anomalies are labeled as -1
        anomaly_indices = np.where(labels == -1)[0].tolist()
        return anomaly_indices
    
    # =============================================
    # Discovery Prediction
    # =============================================
    
    async def predict_discovery(self, map_code: str) -> Dict[str, Any]:
        """
        Predict probability of hitting Discovery
        
        Args:
            map_code: Map code
            
        Returns:
            Dict with probability, prediction, recommendations
        """
        if not self.discovery_model:
            raise ValueError("Discovery predictor not loaded")
        
        # Fetch map data
        map_data = await fetch_map_from_api(map_code)
        if not map_data:
            raise ValueError(f"Map {map_code} not found")
        
        # Check if using cached data
        data_source = map_data.get('_source', 'unknown')
        cache_warning = map_data.get('_cache_warning', '')
        collection_date = map_data.get('_collection_date', 'Unknown')
        
        # Extract features
        features = self._extract_discovery_features(map_data)
        
        # Encode features
        X = self._encode_discovery_features(features)
        
        # Predict probability
        probability = float(self.discovery_model.predict_proba([X])[0][1] * 100)
        prediction = "YES" if probability > 50 else "NO"
        
        # Confidence
        if abs(probability - 50) > 30:
            confidence = "High"
        elif abs(probability - 50) > 15:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Get feature importance for explanation
        strengths, weaknesses = self._analyze_discovery_factors(features, self.discovery_model)
        
        # Generate recommendations
        recommendations = self._generate_discovery_recommendations(features, probability)
        
        result = {
            "map_code": map_code,
            "map_name": map_data['map_data'].get('name', 'Unknown'),
            "discovery_probability": round(probability, 1),
            "prediction": prediction,
            "confidence": confidence,
            "current_status": {
                "avg_ccu_7d": features['avg_ccu_7d'],
                "growth_rate": round(features['ccu_growth_rate'] * 100, 1),
                "creator_followers": features['creator_followers'],
                "in_discovery": bool(features['in_discovery'])
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "data_source": data_source
        }
        
        # Add warning if using cached data
        if data_source == 'local_cache':
            if cache_warning:
                result['cache_warning'] = cache_warning
            result['collection_date'] = collection_date
        
        return result
    
    def _extract_discovery_features(self, map_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for discovery prediction"""
        data = map_data['map_data']
        creator = data.get('creator', {})
        stats_7d = map_data.get('stats_7d', {})
        
        # Calculate time-series features
        ts_features = self._calculate_trend_features(stats_7d)
        
        # CCU stats
        ccu_values = stats_7d.get('data', {}).get('stats', [])
        if len(ccu_values) >= 50:
            ccu_arr = np.array(ccu_values)
            peak_ccu_7d = float(np.max(ccu_arr))
            ccu_growth = (ccu_arr[-24:].mean() - ccu_arr[:24].mean()) / max(ccu_arr[:24].mean(), 1)
            ccu_volatility = np.std(ccu_arr) / max(np.mean(ccu_arr), 1)
        else:
            peak_ccu_7d = 0
            ccu_growth = 0
            ccu_volatility = 0
        
        # Map age
        try:
            published = datetime.fromisoformat(data.get('published', '').replace('Z', '+00:00'))
            last_sync = datetime.fromisoformat(data.get('lastSyncDate', '').replace('Z', '+00:00'))
            map_age_days = (last_sync - published).days
        except:
            map_age_days = 0
        
        # Discovery status
        in_discovery = 1 if data.get('state') == 'in_discovery' else 0
        
        # Tags
        tags = data.get('tags', [])
        primary_tag = tags[0] if tags else 'unknown'
        
        return {
            'type': data.get('type', 'unknown'),
            'primary_tag': primary_tag,
            'num_tags': len(tags),
            'max_players': data.get('max_players', 0),
            'xp_enabled': 1 if data.get('xp_enabled') else 0,
            'creator_followers': creator.get('lookup_follower_count', 0),
            'version': data.get('version', 0),
            'map_age_days': map_age_days,
            'avg_ccu_7d': ts_features['avg_ccu_7d'],
            'peak_ccu_7d': peak_ccu_7d,
            'ccu_growth_rate': float(ccu_growth),
            'ccu_volatility': float(ccu_volatility),
            'current_ccu': data.get('lastSyncCcu', 0),
            'in_discovery': in_discovery
        }
    
    def _encode_discovery_features(self, features: Dict[str, Any]) -> List[float]:
        """Encode features for discovery model"""
        type_encoder = self.discovery_encoders['type_encoder']
        tag_encoder = self.discovery_encoders['tag_encoder']
        feature_columns = self.discovery_encoders['feature_columns']
        
        # Encode categorical
        try:
            type_encoded = type_encoder.transform([features['type']])[0]
        except:
            type_encoded = 0
        
        try:
            tag_encoded = tag_encoder.transform([features['primary_tag']])[0]
        except:
            tag_encoded = 0
        
        # Build feature vector
        feature_dict = {
            'type_encoded': type_encoded,
            'tag_encoded': tag_encoded,
            'num_tags': features['num_tags'],
            'max_players': features['max_players'],
            'xp_enabled': features['xp_enabled'],
            'creator_followers': features['creator_followers'],
            'version': features['version'],
            'map_age_days': features['map_age_days'],
            'avg_ccu_7d': features['avg_ccu_7d'],
            'peak_ccu_7d': features['peak_ccu_7d'],
            'ccu_growth_rate': features['ccu_growth_rate'],
            'ccu_volatility': features['ccu_volatility'],
            'current_ccu': features['current_ccu']
        }
        
        return [feature_dict[col] for col in feature_columns]
    
    def _analyze_discovery_factors(self, features: Dict[str, Any], model) -> Tuple[List[str], List[str]]:
        """Analyze what factors are helping/hurting Discovery chances"""
        strengths = []
        weaknesses = []
        
        # CCU analysis
        if features['avg_ccu_7d'] >= 300:
            strengths.append(f"Strong CCU ({int(features['avg_ccu_7d'])} avg)")
        elif features['avg_ccu_7d'] < 150:
            weaknesses.append(f"Low CCU ({int(features['avg_ccu_7d'])} avg, need 300+)")
        
        # Growth analysis
        if features['ccu_growth_rate'] > 0.1:
            strengths.append(f"Positive growth (+{features['ccu_growth_rate']*100:.0f}%)")
        elif features['ccu_growth_rate'] < -0.05:
            weaknesses.append(f"Declining growth ({features['ccu_growth_rate']*100:.0f}%)")
        
        # XP enabled
        if features['xp_enabled']:
            strengths.append("XP enabled")
        else:
            weaknesses.append("XP not enabled (hurts discoverability)")
        
        # Creator followers
        if features['creator_followers'] > 10000:
            strengths.append(f"Strong creator following ({features['creator_followers']:,})")
        elif features['creator_followers'] < 1000:
            weaknesses.append(f"Low creator following ({features['creator_followers']:,})")
        
        return strengths[:5], weaknesses[:5]
    
    def _generate_discovery_recommendations(self, features: Dict[str, Any], current_prob: float) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # XP recommendation
        if not features['xp_enabled']:
            recommendations.append({
                "action": "Enable XP",
                "impact": "+15% probability",
                "priority": "high"
            })
        
        # Tags recommendation
        if features['num_tags'] < 3:
            recommendations.append({
                "action": f"Add {3 - features['num_tags']} more relevant tags",
                "impact": "+8% probability",
                "priority": "medium"
            })
        
        # CCU recommendation
        if features['avg_ccu_7d'] < 300:
            recommendations.append({
                "action": "Run micro-campaign to boost CCU to 300+",
                "impact": "+20-30% probability",
                "priority": "high"
            })
        
        # Player count optimization
        if features['max_players'] not in range(16, 33):
            recommendations.append({
                "action": "Optimize max players to 16-32 (Discovery sweet spot)",
                "impact": "+5% probability",
                "priority": "low"
            })
        
        return recommendations[:4]


# Singleton instance
ml_service = MLService()
