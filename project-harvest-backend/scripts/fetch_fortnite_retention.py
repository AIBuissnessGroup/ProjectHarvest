"""
Fetch retention and engagement metrics from Fortnite Ecosystem API
for maps in our dataset to enhance our ML models.
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Fortnite Ecosystem API base URL
FORTNITE_API_BASE = "https://api.fortnite.com/ecosystem/v1"

# Directory to save data
DATA_DIR = Path(__file__).parent.parent / "data" / "fortnite_retention"
DATA_DIR.mkdir(exist_ok=True, parents=True)

# Load our existing map codes
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"


async def fetch_retention_metrics(
    client: httpx.AsyncClient,
    map_code: str,
    interval: str = "7d"
) -> Optional[Dict]:
    """
    Fetch all retention and engagement metrics for a map.
    
    Available metrics:
    - retention: Player return rate
    - favorites: Number of times favorited
    - minutes-played: Total minutes played
    - average-minutes-per-player: Avg session length
    - recommendations: Recommendation score
    - unique-players: Unique player count
    - plays: Total play sessions
    - peak-ccu: Peak concurrent users
    """
    
    metrics = {}
    
    # List of all available metrics
    metric_types = [
        "retention",
        "favorites",
        "minutes-played",
        "average-minutes-per-player",
        "recommendations",
        "unique-players",
        "plays",
        "peak-ccu"
    ]
    
    # Calculate date range (last 7 days)
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=7)
    
    from_str = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_str = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    for metric in metric_types:
        url = f"{FORTNITE_API_BASE}/islands/{map_code}/metrics/{interval}/{metric}"
        params = {
            "from": from_str,
            "to": to_str
        }
        
        try:
            response = await client.get(url, params=params, follow_redirects=True)
            
            if response.status_code == 200:
                metrics[metric] = response.json()
                print(f"  ✓ Fetched {metric}")
            elif response.status_code == 404:
                print(f"  ✗ {metric} not available (404)")
                metrics[metric] = None
            else:
                print(f"  ✗ {metric} failed: HTTP {response.status_code}")
                metrics[metric] = None
                
        except Exception as e:
            print(f"  ✗ {metric} error: {str(e)}")
            metrics[metric] = None
    
    return metrics


async def fetch_all_retention_data(limit: int = 50):
    """
    Fetch retention data for maps in our dataset.
    """
    
    # Get list of map codes from our existing dataset
    map_files = list(RAW_DATA_DIR.glob("map_*.json"))
    map_codes = []
    
    for map_file in map_files[:limit]:
        # Extract map code from filename: map_8530_0110_2817.json -> 8530-0110-2817
        filename = map_file.stem
        parts = filename.replace("map_", "").split("_")
        if len(parts) == 3:
            map_code = "-".join(parts)
            map_codes.append(map_code)
    
    print(f"\n🔍 Fetching retention data for {len(map_codes)} maps from Fortnite API...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        results = {}
        
        for i, map_code in enumerate(map_codes, 1):
            print(f"[{i}/{len(map_codes)}] Fetching {map_code}...")
            
            metrics = await fetch_retention_metrics(client, map_code)
            
            if metrics:
                results[map_code] = {
                    "map_code": map_code,
                    "fetched_at": datetime.utcnow().isoformat(),
                    "metrics": metrics
                }
                
                # Save individual file
                output_file = DATA_DIR / f"retention_{map_code.replace('-', '_')}.json"
                with open(output_file, "w") as f:
                    json.dump(results[map_code], f, indent=2)
            
            print()  # Blank line between maps
            
            # Small delay to be respectful to the API
            await asyncio.sleep(0.5)
    
    # Save summary file
    summary_file = DATA_DIR / "retention_summary.json"
    with open(summary_file, "w") as f:
        json.dump({
            "total_maps": len(map_codes),
            "fetched_at": datetime.utcnow().isoformat(),
            "maps": list(results.keys())
        }, f, indent=2)
    
    print(f"\n✅ Fetched retention data for {len(results)} maps")
    print(f"📁 Saved to: {DATA_DIR}")
    print(f"📊 Summary: {summary_file}")


if __name__ == "__main__":
    # Fetch retention data for first 50 maps as a test
    asyncio.run(fetch_all_retention_data(limit=50))

