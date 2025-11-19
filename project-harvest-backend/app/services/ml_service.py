"""
ML Prediction Service
=====================
Loads and uses the trained Random Forest model to predict peak CCU for Fortnite maps.
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MLService:
    """Machine Learning prediction service for map peak CCU predictions"""
    
    def __init__(self):
        """Initialize the ML service by loading the trained model and encoders"""
        self.model = None
        self.encoders = None
        self.metadata = None
        self.is_loaded = False
        
        # Path to saved models
        self.models_dir = Path(__file__).parent.parent.parent / "data" / "models"
        
    def load_model(self):
        """Load the trained model and encoders from disk"""
        try:
            model_path = self.models_dir / "peak_ccu_predictor.pkl"
            encoders_path = self.models_dir / "encoders.pkl"
            
            if not model_path.exists():
                logger.error(f"Model file not found at {model_path}")
                return False
            
            if not encoders_path.exists():
                logger.error(f"Encoders file not found at {encoders_path}")
                return False
            
            # Load model and encoders
            self.model = joblib.load(model_path)
            self.encoders = joblib.load(encoders_path)
            
            # Load metadata
            metadata_path = self.models_dir / "model_metadata.json"
            if metadata_path.exists():
                import json
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            
            self.is_loaded = True
            logger.info("✅ ML model loaded successfully!")
            logger.info(f"   Model: {self.encoders.get('model_name', 'Unknown')}")
            if self.metadata:
                logger.info(f"   R² Score: {self.metadata.get('r2_score', 'N/A'):.3f}")
                logger.info(f"   Training samples: {self.metadata.get('training_samples', 'N/A')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading ML model: {e}")
            self.is_loaded = False
            return False
    
    def encode_features(self, map_data: Dict) -> Optional[np.ndarray]:
        """
        Encode map features for prediction
        
        Args:
            map_data: Dictionary containing map features
            
        Returns:
            Numpy array of encoded features, or None if encoding fails
        """
        if not self.is_loaded:
            logger.error("Model not loaded. Call load_model() first.")
            return None
        
        try:
            type_encoder = self.encoders['type_encoder']
            tag_encoder = self.encoders['tag_encoder']
            
            # Get map type
            map_type = map_data.get('type', 'uefn')
            try:
                type_encoded = type_encoder.transform([map_type])[0]
            except ValueError:
                # If type not in training data, use 'uefn' as default
                logger.warning(f"Type '{map_type}' not in training data, using 'uefn'")
                type_encoded = type_encoder.transform(['uefn'])[0]
            
            # Get primary tag
            primary_tag = map_data.get('primary_tag', 'unknown')
            try:
                tag_encoded = tag_encoder.transform([primary_tag])[0]
            except ValueError:
                # If tag not in training data, use first available tag
                logger.warning(f"Tag '{primary_tag}' not in training data, using default")
                tag_encoded = 0
            
            # Build feature array in the correct order
            features = [
                type_encoded,
                tag_encoded,
                map_data.get('num_tags', 3),
                map_data.get('max_players', 16),
                1 if map_data.get('xp_enabled', True) else 0,
                map_data.get('creator_followers', 0),
                map_data.get('version', 1),
                map_data.get('current_ccu', 0),
                map_data.get('growth_rate_7d', 0)
            ]
            
            return np.array([features])
            
        except Exception as e:
            logger.error(f"Error encoding features: {e}")
            return None
    
    def predict(self, map_data: Dict) -> Optional[Dict]:
        """
        Predict peak CCU for a map
        
        Args:
            map_data: Dictionary containing map features
            
        Returns:
            Dictionary with prediction results, or None if prediction fails
        """
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        try:
            # Encode features
            X = self.encode_features(map_data)
            if X is None:
                return None
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            
            # Calculate confidence based on input data quality
            confidence = self._calculate_confidence(map_data, prediction)
            
            result = {
                "predicted_peak_ccu": int(prediction),
                "confidence": confidence,
                "model_name": self.encoders.get('model_name', 'Unknown'),
                "model_version": "1.0.0"
            }
            
            if self.metadata:
                result["model_r2_score"] = self.metadata.get('r2_score')
            
            logger.info(f"Prediction: {int(prediction):,} CCU (confidence: {confidence})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
    
    def _calculate_confidence(self, map_data: Dict, prediction: float) -> str:
        """
        Calculate confidence level based on input data quality
        
        Args:
            map_data: Input map features
            prediction: Predicted peak CCU
            
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        confidence_score = 100
        
        # Penalize if prediction is outside typical range (based on training data)
        if self.metadata:
            # Assume typical range is 1K - 200K based on training
            if prediction < 1000 or prediction > 200000:
                confidence_score -= 30
        
        # Check data quality
        if map_data.get('current_ccu', 0) == 0:
            confidence_score -= 20
        
        if map_data.get('creator_followers', 0) == 0:
            confidence_score -= 15
        
        if map_data.get('version', 0) == 0:
            confidence_score -= 10
        
        # Return confidence level
        if confidence_score >= 70:
            return "high"
        elif confidence_score >= 40:
            return "medium"
        else:
            return "low"
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        info = {
            "status": "loaded",
            "model_name": self.encoders.get('model_name', 'Unknown'),
            "model_version": "1.0.0"
        }
        
        if self.metadata:
            info.update({
                "r2_score": self.metadata.get('r2_score'),
                "training_samples": self.metadata.get('training_samples'),
                "test_samples": self.metadata.get('test_samples'),
                "feature_columns": self.metadata.get('feature_columns', [])
            })
        
        return info


# Global instance
ml_service = MLService()

