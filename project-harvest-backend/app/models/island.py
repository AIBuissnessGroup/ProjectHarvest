"""
Island and Metrics Pydantic Models
===================================
Data models for Fortnite islands and their performance metrics
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# Metric Data Models
# ============================================

class MetricInterval(BaseModel):
    """
    Single time interval for a metric
    
    Example:
        {
            "timestamp": "2025-11-13T00:00:00.000Z",
            "value": 1250
        }
    """
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    value: Optional[int | float] = Field(None, description="Metric value (null if no data)")


class MetricData(BaseModel):
    """
    Time-series data for a specific metric
    
    Contains multiple intervals (e.g., 7 days of daily data)
    """
    intervals: List[MetricInterval] = Field(default_factory=list, description="List of time intervals")


class IslandMetrics(BaseModel):
    """
    All performance metrics for an island
    
    Includes:
    - peak-ccu: Peak concurrent users
    - favorites: Number of favorites
    - minutes-played: Total playtime
    - average-minutes-per-player: Avg session length
    - recommendations: Algorithm recommendations
    - unique-players: Unique player count
    - plays: Total play sessions
    - retention: Player retention rate
    """
    peak_ccu: Optional[MetricData] = Field(None, alias="peak-ccu")
    favorites: Optional[MetricData] = None
    minutes_played: Optional[MetricData] = Field(None, alias="minutes-played")
    average_minutes_per_player: Optional[MetricData] = Field(None, alias="average-minutes-per-player")
    recommendations: Optional[MetricData] = None
    unique_players: Optional[MetricData] = Field(None, alias="unique-players")
    plays: Optional[MetricData] = None
    retention: Optional[MetricData] = None
    
    class Config:
        populate_by_name = True  # Allow both alias and field name


# ============================================
# Island Models
# ============================================

class IslandMeta(BaseModel):
    """Pagination metadata from Fortnite API"""
    page: Optional[Dict[str, Any]] = None


class Island(BaseModel):
    """
    Fortnite Creative Island/Map
    
    Represents a creator-made map with metadata
    """
    code: str = Field(..., description="Island code (e.g., 1234-5678-9012)")
    creator_code: Optional[str] = Field(None, alias="creatorCode")
    display_name: Optional[str] = Field(None, alias="displayName")
    title: str = Field(..., description="Island title/name")
    category: Optional[str] = Field(None, description="Island category (e.g., 'LEGO', 'pvp', 'roleplay')")
    created_in: Optional[str] = Field(None, alias="createdIn", description="Creation tool (UEFN or Creative)")
    tags: List[str] = Field(default_factory=list, description="Island tags")
    meta: Optional[IslandMeta] = None
    
    class Config:
        populate_by_name = True


class IslandWithMetrics(BaseModel):
    """
    Island data combined with its performance metrics
    
    This is what we stored in our data/raw/*.json files
    """
    island: Island
    metrics: IslandMetrics
    fetched_at: str = Field(..., description="When this data was collected")


# ============================================
# API Response Models
# ============================================

class IslandListResponse(BaseModel):
    """
    Response for GET /api/islands
    
    Paginated list of islands
    """
    data: List[Island]
    meta: Optional[Dict[str, Any]] = None
    count: int = Field(..., description="Number of islands returned")


class IslandDetailResponse(BaseModel):
    """
    Response for GET /api/islands/{code}
    
    Single island with all details
    """
    code: str
    title: str
    category: Optional[str]
    created_in: Optional[str] = Field(None, alias="createdIn")
    creator_code: Optional[str] = Field(None, alias="creatorCode")
    tags: List[str]
    
    class Config:
        populate_by_name = True


class MetricsSummary(BaseModel):
    """
    Aggregated metrics summary for an island
    
    Provides quick stats without full time-series data
    """
    peak_ccu: Optional[int] = Field(None, description="Highest CCU in period")
    total_favorites: Optional[int] = Field(None, description="Total favorites")
    total_plays: Optional[int] = Field(None, description="Total play sessions")
    total_minutes_played: Optional[int] = Field(None, description="Total playtime")
    unique_players: Optional[int] = Field(None, description="Unique players")
    avg_session_length: Optional[float] = Field(None, description="Average minutes per session")
    avg_retention: Optional[float] = Field(None, description="Average retention %")


class IslandWithSummary(BaseModel):
    """
    Island with summarized metrics (not full time-series)
    
    Good for list endpoints where full data is too heavy
    """
    code: str
    title: str
    category: Optional[str]
    metrics_summary: MetricsSummary


# ============================================
# Analytics Models
# ============================================

class PredictionRequest(BaseModel):
    """Request model for peak CCU prediction using trained Random Forest model"""
    
    # Option 1: Provide map_code and we'll fetch everything automatically
    map_code: Optional[str] = Field(None, description="Map code (e.g., '1832-0431-4852') - we'll fetch all data automatically")
    
    # Option 2: Provide manual features (all optional if map_code is provided)
    type: Optional[str] = Field(None, description="Map type: uefn, creative, lego, squidgame, etc.")
    primary_tag: Optional[str] = Field(None, description="Primary category tag (e.g., boxfight, tycoon, 1v1)")
    num_tags: Optional[int] = Field(None, ge=1, le=10, description="Number of tags/categories")
    max_players: Optional[int] = Field(None, ge=1, le=100, description="Maximum players allowed")
    xp_enabled: Optional[bool] = Field(None, description="Whether XP rewards are enabled")
    creator_followers: Optional[int] = Field(None, ge=0, description="Creator's follower count")
    version: Optional[int] = Field(None, ge=0, description="Number of updates/versions")
    current_ccu: Optional[int] = Field(None, ge=0, description="Current concurrent users")
    growth_rate_7d: Optional[float] = Field(None, description="7-day CCU growth rate (%)")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "description": "Easy mode - just provide map code",
                    "value": {
                        "map_code": "1832-0431-4852"
                    }
                },
                {
                    "description": "Manual mode - provide all features",
                    "value": {
                        "type": "uefn",
                        "primary_tag": "1v1",
                        "num_tags": 4,
                        "max_players": 16,
                        "xp_enabled": True,
                        "creator_followers": 150000,
                        "version": 50,
                        "current_ccu": 5000,
                        "growth_rate_7d": 5.2
                    }
                }
            ]
        }


class PredictionResponse(BaseModel):
    """Response model for peak CCU prediction"""
    predicted_peak_ccu: int = Field(..., description="Predicted all-time peak concurrent users")
    confidence: str = Field(..., description="Confidence level: high, medium, or low")
    model_name: str = Field(..., description="Name of the ML model used")
    model_version: str = Field(..., description="Version of the model")
    model_r2_score: Optional[float] = Field(None, description="Model's R² score on test data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "predicted_peak_ccu": 37214,
                "confidence": "high",
                "model_name": "Random Forest",
                "model_version": "1.0.0",
                "model_r2_score": 0.524
            }
        }


class ModelInfo(BaseModel):
    """Information about the loaded ML model"""
    status: str = Field(..., description="Model status: loaded or not_loaded")
    model_name: Optional[str] = Field(None, description="Name of the model")
    model_version: Optional[str] = Field(None, description="Version of the model")
    r2_score: Optional[float] = Field(None, description="R² score on test data")
    training_samples: Optional[int] = Field(None, description="Number of training samples")
    test_samples: Optional[int] = Field(None, description="Number of test samples")
    feature_columns: Optional[List[str]] = Field(None, description="List of feature columns used")


# ============================================
# Error Models
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================
# ML Prediction Models (Future CCU, Anomaly, Discovery)
# ============================================

class FutureCCURequest(BaseModel):
    """Request for Future CCU prediction (7-day forecast)"""
    map_code: str = Field(..., description="Map code (e.g., '8530-0110-2817')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_code": "8530-0110-2817"
            }
        }


class DailyForecast(BaseModel):
    """Single day forecast"""
    day: int = Field(..., description="Day number (1-7)")
    predicted_ccu: int = Field(..., description="Predicted CCU for this day")
    change_from_baseline: float = Field(..., description="% change from baseline")
    confidence_lower: int = Field(..., description="Lower bound of prediction (confidence interval)")
    confidence_upper: int = Field(..., description="Upper bound of prediction (confidence interval)")


class FutureCCUResponse(BaseModel):
    """Response for Future CCU prediction"""
    map_code: str
    map_name: str
    current_ccu: int = Field(..., description="Current CCU")
    baseline_ccu: float = Field(..., description="7-day average CCU")
    predicted_ccu_7d: int = Field(..., description="Predicted CCU in 7 days")
    daily_forecast: List[DailyForecast] = Field(default_factory=list, description="Day-by-day breakdown")
    trend: str = Field(..., description="Growing, Declining, or Stable")
    trend_strength: str = Field(..., description="Weak, Moderate, or Strong")
    key_insights: List[str] = Field(default_factory=list, description="Key insights about the forecast")
    confidence: str = Field(..., description="High, Medium, or Low")
    model_metrics: Dict[str, float] = Field(..., description="Model R², MAE, RMSE")
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_code": "8530-0110-2817",
                "map_name": "Cool Arena Map",
                "current_ccu": 5591,
                "baseline_ccu": 7548,
                "predicted_ccu_7d": 4820,
                "daily_forecast": [
                    {
                        "day": 1,
                        "predicted_ccu": 7200,
                        "change_from_baseline": -4.6,
                        "confidence_lower": 6800,
                        "confidence_upper": 7600
                    },
                    {
                        "day": 7,
                        "predicted_ccu": 4820,
                        "change_from_baseline": -36.1,
                        "confidence_lower": 4400,
                        "confidence_upper": 5240
                    }
                ],
                "trend": "Declining",
                "trend_strength": "Strong",
                "key_insights": [
                    "Steepest drop occurs on Days 6-7 (-12%)",
                    "Consider campaign on Day 5 to prevent decline"
                ],
                "confidence": "High",
                "model_metrics": {
                    "r2_score": 0.76,
                    "mae": 46,
                    "rmse": 78
                }
            }
        }


class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection on map CCU data"""
    map_code: str = Field(..., description="Map code to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_code": "8530-0110-2817"
            }
        }


class AnomalyDetectionResponse(BaseModel):
    """Response for anomaly detection"""
    map_code: str
    map_name: str
    anomaly_score: float = Field(..., description="Anomaly score (lower = more anomalous)")
    is_anomalous: bool = Field(..., description="Whether map shows anomalous behavior")
    num_spikes: int = Field(..., description="Number of CCU spikes detected")
    spike_details: List[Dict[str, Any]] = Field(default_factory=list, description="Details of each spike")
    interpretation: str = Field(..., description="Human-readable interpretation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_code": "8530-0110-2817",
                "map_name": "Cool Arena Map",
                "anomaly_score": -0.42,
                "is_anomalous": True,
                "num_spikes": 3,
                "spike_details": [
                    {"timestamp_index": 145, "ccu": 890, "z_score": 3.2}
                ],
                "interpretation": "Map shows 3 unusual CCU spikes. Possible campaign activity or viral moment."
            }
        }


class DiscoveryPredictionRequest(BaseModel):
    """Request for Discovery placement prediction"""
    map_code: str = Field(..., description="Map code to analyze")
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_code": "8530-0110-2817"
            }
        }


class DiscoveryPredictionResponse(BaseModel):
    """Response for Discovery prediction"""
    map_code: str
    map_name: str
    discovery_probability: float = Field(..., description="Probability of hitting Discovery (0-100%)")
    prediction: str = Field(..., description="YES or NO")
    confidence: str = Field(..., description="High, Medium, or Low")
    current_status: Dict[str, Any] = Field(..., description="Current map metrics")
    strengths: List[str] = Field(default_factory=list, description="Positive factors")
    weaknesses: List[str] = Field(default_factory=list, description="Negative factors")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Actionable recommendations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_code": "8530-0110-2817",
                "map_name": "Cool Arena Map",
                "discovery_probability": 73.5,
                "prediction": "YES",
                "confidence": "High",
                "current_status": {
                    "avg_ccu_7d": 450,
                    "growth_rate": 0.18,
                    "creator_followers": 12500
                },
                "strengths": [
                    "Strong upward momentum (+18% growth)",
                    "CCU in Discovery range"
                ],
                "weaknesses": [
                    "Creator follower count could be higher"
                ],
                "recommendations": [
                    {
                        "action": "Enable XP",
                        "impact": "+15% probability",
                        "priority": "high"
                    }
                ]
            }
        }


class CompareMapsRequest(BaseModel):
    """Request to compare multiple maps"""
    map_codes: List[str] = Field(..., min_length=2, description="List of map codes to compare")
    
    class Config:
        json_schema_extra = {
            "example": {
                "map_codes": ["8530-0110-2817", "7048-0233-4310", "6522-1299-1581"]
            }
        }


class CompareMapsResponse(BaseModel):
    """Response for map comparison"""
    comparison: str = Field(..., description="AI-generated comparison report")
    rankings: Dict[str, List[Dict[str, Any]]] = Field(..., description="Rankings by different metrics")
    summary_stats: Dict[str, Any] = Field(..., description="Summary statistics")


# ============================================
# Chat/AI Models
# ============================================

class ChatRequest(BaseModel):
    """Request model for AI chat endpoint"""
    message: str = Field(..., description="User's message/question", min_length=1, max_length=1000)
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None, 
        description="Optional conversation history for context"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "message": "What is the predicted peak CCU for map 1832-0431-4852?"
                },
                {
                    "message": "Compare maps 1832-0431-4852 and 6562-8953-6567"
                },
                {
                    "message": "Why is my map underperforming?"
                }
            ]
        }


class ChatResponse(BaseModel):
    """Response model for AI chat endpoint"""
    response: str = Field(..., description="AI-generated response")
    function_called: Optional[str] = Field(None, description="Name of function that was triggered (if any)")
    chart_data: Optional[Dict[str, Any]] = Field(None, description="Chart data if prediction was made (for visualization)")
    error: Optional[str] = Field(None, description="Error message if chat failed")


class InsightsRequest(BaseModel):
    """Request model for quick insights endpoint"""
    map_code: str = Field(..., description="Map code to analyze (e.g., '1832-0431-4852')")


class InsightsResponse(BaseModel):
    """Response model for quick insights endpoint"""
    map_code: str = Field(..., description="Map code that was analyzed")
    map_name: Optional[str] = Field(None, description="Name of the map")
    insights: str = Field(..., description="AI-generated insights and recommendations")
    error: Optional[str] = Field(None, description="Error message if insights generation failed")


class ChatHealthCheck(BaseModel):
    """Response model for chat service health check"""
    status: str = Field(..., description="Status of chat service ('available' or 'unavailable')")
    service: str = Field(..., description="AI service being used (e.g., 'Google Gemini')")
    configured: bool = Field(..., description="Whether API key is configured")
    message: str = Field(..., description="Human-readable status message")


# ============================================
# Health Check Model
# ============================================

class HealthCheck(BaseModel):
    """API health check response"""
    status: str = Field(..., description="API status (healthy/unhealthy)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field("0.1.0", description="API version")

