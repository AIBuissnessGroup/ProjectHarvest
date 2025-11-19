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
# Health Check Model
# ============================================

class HealthCheck(BaseModel):
    """API health check response"""
    status: str = Field(..., description="API status (healthy/unhealthy)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field("0.1.0", description="API version")

