"""
FNCreate.gg API Service
=======================
Fetches live map data from fncreate.gg API
"""

import httpx
import logging
from typing import Optional, Dict, Tuple
import numpy as np
import json
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_URL = "https://fncreate.gg"
LOCAL_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "raw"


def load_map_from_local(map_code: str) -> Optional[Dict]:
    """
    Load map data from local JSON files (fallback when API is down)
    
    Args:
        map_code: Map code (e.g., "1832-0431-4852")
    
    Returns:
        Dictionary with map data and a flag indicating it's from local cache, or None if not found
    """
    try:
        # Convert map code format: "1832-0431-4852" -> "map_1832_0431_4852.json"
        filename = f"map_{map_code.replace('-', '_')}.json"
        file_path = LOCAL_DATA_PATH / filename
        
        if not file_path.exists():
            logger.warning(f"Local file not found: {file_path}")
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Get file modification time (when data was collected)
        import os
        from datetime import datetime
        file_mtime = os.path.getmtime(file_path)
        collection_date = datetime.fromtimestamp(file_mtime).strftime('%B %d, %Y at %I:%M %p')
        
        logger.info(f"✅ Loaded map {map_code} from LOCAL CACHE (collected {collection_date})")
        
        # Add metadata to indicate this is cached data
        return {
            'map_data': data.get('map_data', {}),
            'stats_7d': data.get('stats_7d', {}),
            '_source': 'local_cache',  # Flag to indicate data source
            '_cache_warning': f'This data is from our local cache (collected {collection_date}) and may be outdated. The fncreate.gg API is currently unavailable.',
            '_collection_date': collection_date
        }
    
    except Exception as e:
        logger.error(f"Error loading local map data for {map_code}: {e}")
        return None


async def fetch_map_from_api(map_code: str) -> Optional[Dict]:
    """
    Fetch map data from fncreate.gg API, with fallback to local cache
    
    Args:
        map_code: Map code (e.g., "1832-0431-4852")
    
    Returns:
        Dictionary with map data, or None if fetch fails
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            # Fetch map details with creator info
            logger.info(f"Fetching map {map_code} from fncreate.gg...")
            
            r = await client.get(f"{BASE_URL}/api/maps/{map_code}", params={"cs": "true"})
            r.raise_for_status()
            map_response = r.json()
            
            if not map_response.get('success'):
                logger.error(f"API returned success=false for map {map_code}")
                # Try local fallback
                logger.info("⚠️  fncreate.gg API failed, trying local cache...")
                return load_map_from_local(map_code)
            
            map_data = map_response.get('data', {})
            
            # Fetch 7d stats
            stats_response = await client.post(
                f"{BASE_URL}/api/maps/{map_code}/v2/stats",
                json={"type": "7d"}
            )
            stats_response.raise_for_status()
            stats_7d = stats_response.json()
            
            logger.info(f"✅ Fetched map {map_code} from LIVE API")
            
            # Combine data
            return {
                'map_data': map_data,
                'stats_7d': stats_7d,
                '_source': 'live_api'  # Flag to indicate data source
            }
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(f"Map {map_code} not found (404)")
        else:
            logger.error(f"HTTP error fetching map {map_code}: {e}")
        
        # Try local fallback
        logger.info("⚠️  fncreate.gg API is down, trying local cache...")
        return load_map_from_local(map_code)
    
    except Exception as e:
        logger.error(f"Error fetching map {map_code}: {e}")
        
        # Try local fallback
        logger.info("⚠️  fncreate.gg API error, trying local cache...")
        return load_map_from_local(map_code)


def calculate_growth_rate(stats_7d: Dict) -> float:
    """Calculate 7-day CCU growth rate from stats"""
    if not stats_7d or not stats_7d.get('success'):
        return 0.0
    
    data_points = stats_7d.get('data', {}).get('stats', [])
    if len(data_points) < 10:
        return 0.0
    
    # Compare first quarter vs last quarter average
    quarter = len(data_points) // 4
    early_avg = np.mean(data_points[:quarter])
    late_avg = np.mean(data_points[-quarter:])
    
    if early_avg == 0:
        return 0.0
    
    growth_rate = ((late_avg - early_avg) / early_avg) * 100
    return growth_rate


def extract_features_from_api(api_data: Dict) -> Optional[Dict]:
    """
    Extract ML features from fncreate.gg API response
    
    Args:
        api_data: Response from fetch_map_from_api
    
    Returns:
        Dictionary of features for ML model, or None if extraction fails
    """
    try:
        map_data = api_data.get('map_data', {})
        stats_7d = api_data.get('stats_7d', {})
        
        # Extract creator data
        creator = map_data.get('creator', {})
        creator_followers = creator.get('lookup_follower_count', 0)
        
        # Calculate growth
        growth_rate = calculate_growth_rate(stats_7d)
        
        # Get tags
        tags = map_data.get('tags', [])
        primary_tag = tags[0] if tags else 'unknown'
        
        # Build feature dictionary
        features = {
            'map_code': map_data.get('id'),
            'name': map_data.get('name', 'Unknown'),
            'type': map_data.get('type', 'uefn'),
            'primary_tag': primary_tag,
            'num_tags': len(tags),
            'max_players': map_data.get('max_players', 16),
            'xp_enabled': bool(map_data.get('xp_enabled', True)),
            'creator_followers': creator_followers,
            'version': map_data.get('version', 1),
            'current_ccu': map_data.get('lastSyncCcu', 0),
            'growth_rate_7d': growth_rate,
        }
        
        logger.info(f"Extracted features for {features['name']} ({features['map_code']})")
        return features
        
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        return None

