"""
Islands API Routes
==================
Endpoints for fetching Fortnite Creative island data and metrics
"""

import json
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path

from app.models.island import (
    Island, 
    IslandListResponse, 
    IslandDetailResponse,
    IslandWithMetrics,
    MetricsSummary,
    IslandWithSummary
)
from app.services.cache import cache, make_island_key, make_islands_list_key
from app.core.config import settings

router = APIRouter(prefix="/api/islands", tags=["Islands"])

# Data directory path
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw"


# ============================================
# Helper Functions
# ============================================

def load_islands_from_file() -> List[dict]:
    """Load all islands from islands.json"""
    islands_file = DATA_DIR / "islands.json"
    
    if not islands_file.exists():
        raise FileNotFoundError("Islands data not found")
    
    with open(islands_file, 'r') as f:
        data = json.load(f)
        return data.get('data', [])


def load_island_metrics(code: str) -> Optional[dict]:
    """Load metrics for specific island"""
    metrics_file = DATA_DIR / f"metrics_{code.replace('-', '_')}.json"
    
    if not metrics_file.exists():
        return None
    
    with open(metrics_file, 'r') as f:
        return json.load(f)


def calculate_metrics_summary(metrics: dict) -> MetricsSummary:
    """Calculate aggregated metrics summary from time-series data"""
    
    def get_max_value(metric_name: str) -> Optional[int]:
        """Get maximum value from metric intervals"""
        if not metrics.get(metric_name) or not metrics[metric_name].get('intervals'):
            return None
        values = [
            interval['value'] 
            for interval in metrics[metric_name]['intervals'] 
            if interval.get('value') is not None
        ]
        return max(values) if values else None
    
    def get_total_value(metric_name: str) -> Optional[int]:
        """Get total value from metric intervals"""
        if not metrics.get(metric_name) or not metrics[metric_name].get('intervals'):
            return None
        values = [
            interval['value'] 
            for interval in metrics[metric_name]['intervals'] 
            if interval.get('value') is not None
        ]
        return sum(values) if values else None
    
    def get_avg_value(metric_name: str) -> Optional[float]:
        """Get average value from metric intervals"""
        if not metrics.get(metric_name) or not metrics[metric_name].get('intervals'):
            return None
        values = [
            interval['value'] 
            for interval in metrics[metric_name]['intervals'] 
            if interval.get('value') is not None
        ]
        return round(sum(values) / len(values), 2) if values else None
    
    return MetricsSummary(
        peak_ccu=get_max_value('peak-ccu'),
        total_favorites=get_total_value('favorites'),
        total_plays=get_total_value('plays'),
        total_minutes_played=get_total_value('minutes-played'),
        unique_players=get_total_value('unique-players'),
        avg_session_length=get_avg_value('average-minutes-per-player'),
        avg_retention=get_avg_value('retention')
    )


# ============================================
# API Endpoints
# ============================================

@router.get("", response_model=IslandListResponse)
async def get_islands(
    limit: int = Query(50, ge=1, le=200, description="Number of islands to return"),
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'pvp', 'roleplay')"),
    created_in: Optional[str] = Query(None, description="Filter by creation tool ('UEFN' or 'Creative')")
):
    """
    Get list of all islands with optional filtering
    
    Returns island metadata without full metrics (use /islands/{code} for details)
    """
    
    # Try cache first
    cache_key = make_islands_list_key()
    cached_data = await cache.get(cache_key)
    
    if cached_data:
        islands_data = cached_data
    else:
        # Load from file
        islands_data = load_islands_from_file()
        
        # Cache for 1 hour
        await cache.set(cache_key, islands_data, ttl=settings.CACHE_TTL_ISLANDS)
    
    # Apply filters
    filtered = islands_data
    
    if category:
        filtered = [i for i in filtered if i.get('category') == category]
    
    if created_in:
        filtered = [i for i in filtered if i.get('createdIn') == created_in]
    
    # Apply limit
    filtered = filtered[:limit]
    
    # Convert to Island models
    islands = [Island(**island_data) for island_data in filtered]
    
    return IslandListResponse(
        data=islands,
        count=len(islands),
        meta={"total_available": len(islands_data)}
    )


@router.get("/{code}", response_model=IslandDetailResponse)
async def get_island_detail(code: str):
    """
    Get detailed information for a specific island
    
    Args:
        code: Island code (e.g., '1333-6845-4920')
    
    Returns:
        Island details with metadata
    """
    
    # Try cache first
    cache_key = make_island_key(code)
    cached_data = await cache.get(cache_key)
    
    if cached_data:
        return IslandDetailResponse(**cached_data)
    
    # Load all islands and find the specific one
    islands_data = load_islands_from_file()
    island_data = next((i for i in islands_data if i['code'] == code), None)
    
    if not island_data:
        raise HTTPException(status_code=404, detail=f"Island {code} not found")
    
    # Cache for 1 hour
    await cache.set(cache_key, island_data, ttl=settings.CACHE_TTL_ISLANDS)
    
    return IslandDetailResponse(**island_data)


@router.get("/{code}/metrics", response_model=IslandWithMetrics)
async def get_island_metrics(code: str):
    """
    Get full metrics (time-series data) for a specific island
    
    Args:
        code: Island code (e.g., '1333-6845-4920')
    
    Returns:
        Island data with complete metrics history
    """
    
    # Load island metadata
    islands_data = load_islands_from_file()
    island_data = next((i for i in islands_data if i['code'] == code), None)
    
    if not island_data:
        raise HTTPException(status_code=404, detail=f"Island {code} not found")
    
    # Load metrics
    metrics_data = load_island_metrics(code)
    
    if not metrics_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Metrics not found for island {code}. Island may be inactive."
        )
    
    return IslandWithMetrics(
        island=Island(**island_data),
        metrics=metrics_data.get('metrics', {}),
        fetched_at=metrics_data.get('fetched_at', '')
    )


@router.get("/{code}/summary", response_model=IslandWithSummary)
async def get_island_summary(code: str):
    """
    Get island with summarized metrics (aggregated, not time-series)
    
    Lighter endpoint than /metrics - good for dashboards showing many islands
    
    Args:
        code: Island code (e.g., '1333-6845-4920')
    
    Returns:
        Island with aggregated metrics summary
    """
    
    # Load island metadata
    islands_data = load_islands_from_file()
    island_data = next((i for i in islands_data if i['code'] == code), None)
    
    if not island_data:
        raise HTTPException(status_code=404, detail=f"Island {code} not found")
    
    # Load and summarize metrics
    metrics_data = load_island_metrics(code)
    
    if metrics_data:
        summary = calculate_metrics_summary(metrics_data.get('metrics', {}))
    else:
        summary = MetricsSummary()
    
    return IslandWithSummary(
        code=island_data['code'],
        title=island_data['title'],
        category=island_data.get('category'),
        metrics_summary=summary
    )


@router.get("/{code}/exists")
async def check_island_exists(code: str):
    """
    Quick check if island exists in our database
    
    Args:
        code: Island code
    
    Returns:
        Boolean indicating if island exists
    """
    islands_data = load_islands_from_file()
    exists = any(i['code'] == code for i in islands_data)
    
    return {
        "code": code,
        "exists": exists,
        "has_metrics": load_island_metrics(code) is not None if exists else False
    }

