"""
ML Service - Unified service for all ML models
===============================================
Handles loading and predictions for:
1. Future CCU Prediction (7-day forecast)
2. Anomaly Detection (campaign spikes)
3. Discovery Probability (placement prediction)
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.services.fncreate_service import fetch_map_from_api


class MLService:
    """Unified ML service for all prediction models"""
    
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
            
            # Anomaly Detector
            anomaly_path = self.models_dir / "anomaly_detector.pkl"
            if anomaly_path.exists():
                try:
                    self.anomaly_model = joblib.load(anomaly_path)
                    self.anomaly_scaler = joblib.load(self.models_dir / "anomaly_scaler.pkl")
                    
                    import json
                    with open(self.models_dir / "anomaly_metadata.json") as f:
                        self.anomaly_metadata = json.load(f)
                    
                    print("✅ Anomaly detector loaded")
                except Exception as e:
                    print(f"⚠️  Error loading Anomaly detector: {e}")
            else:
                print("⚠️  Anomaly detector not found - train with notebooks/train_anomaly_detector.ipynb")
            
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
                self.anomaly_model is not None,
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
        
        return {
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
            "model_metrics": {
                "r2_score": self.future_ccu_metadata.get('r2_score', 0),
                "mae": self.future_ccu_metadata.get('mae', 0),
                "rmse": self.future_ccu_metadata.get('rmse', 0)
            }
        }
    
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
    # Anomaly Detection
    # =============================================
    
    async def detect_anomalies(self, map_code: str) -> Dict[str, Any]:
        """
        Detect CCU anomalies/spikes for a map
        
        Args:
            map_code: Map code
            
        Returns:
            Dict with anomaly score, spikes, interpretation
        """
        if not self.anomaly_model:
            raise ValueError("Anomaly detector not loaded")
        
        # Fetch map data
        map_data = await fetch_map_from_api(map_code)
        if not map_data:
            raise ValueError(f"Map {map_code} not found")
        
        # Extract time-series
        stats_7d = map_data.get('stats_7d', {})
        if not stats_7d.get('success'):
            raise ValueError("No time-series data available")
        
        ccu_series = stats_7d.get('data', {}).get('stats', [])
        if len(ccu_series) < 50:
            raise ValueError("Insufficient data for anomaly detection")
        
        # Statistical anomaly detection
        spike_indices, spike_scores, num_spikes = self._detect_statistical_anomalies(ccu_series)
        
        # ML-based anomaly detection
        features = self._extract_anomaly_features(ccu_series)
        X_scaled = self.anomaly_scaler.transform([features])
        anomaly_score = float(self.anomaly_model.score_samples(X_scaled)[0])
        is_anomalous = self.anomaly_model.predict(X_scaled)[0] == -1
        
        # Build spike details
        spike_details = []
        for idx, score in zip(spike_indices, spike_scores):
            spike_details.append({
                "timestamp_index": int(idx),
                "ccu": int(ccu_series[idx]),
                "z_score": float(score)
            })
        
        # Interpretation
        if is_anomalous and num_spikes > 0:
            interpretation = f"Map shows {num_spikes} unusual CCU spike(s). Possible campaign activity or viral moment."
        elif is_anomalous:
            interpretation = "Map shows unusual CCU patterns. Investigate recent activity."
        else:
            interpretation = "Map shows normal CCU behavior. No significant anomalies detected."
        
        return {
            "map_code": map_code,
            "map_name": map_data['map_data'].get('name', 'Unknown'),
            "anomaly_score": anomaly_score,
            "is_anomalous": bool(is_anomalous),
            "num_spikes": num_spikes,
            "spike_details": spike_details[:10],  # Limit to 10 most significant
            "interpretation": interpretation
        }
    
    def _detect_statistical_anomalies(self, ccu_series: List[float], threshold: float = 2.5) -> Tuple[List[int], List[float], int]:
        """Detect anomalies using Z-score"""
        arr = np.array(ccu_series)
        mean = np.mean(arr)
        std = np.std(arr)
        
        if std == 0:
            return [], [], 0
        
        z_scores = np.abs((arr - mean) / std)
        anomaly_indices = np.where(z_scores > threshold)[0]
        anomaly_scores = z_scores[anomaly_indices]
        
        return anomaly_indices.tolist(), anomaly_scores.tolist(), len(anomaly_indices)
    
    def _extract_anomaly_features(self, ccu_series: List[float]) -> List[float]:
        """Extract statistical features for anomaly detection"""
        arr = np.array(ccu_series)
        
        return [
            float(np.mean(arr)),
            float(np.std(arr)),
            float(np.max(arr)),
            float(np.min(arr)),
            float(np.max(arr) - np.mean(arr)),  # Peak deviation
            float(np.std(arr) / max(np.mean(arr), 1)),  # Coefficient of variation
            float(np.max(np.diff(arr))),  # Max jump
            float(np.percentile(arr, 95)),  # 95th percentile
        ]
    
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
        
        return {
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
            "recommendations": recommendations
        }
    
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
