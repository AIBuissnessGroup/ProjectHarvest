"""
Daily CCU Data Collection Script
=================================
Collects and stores daily CCU snapshots for all tracked maps.
Run this daily (via cron or Railway scheduled task) to build historical data.

Usage:
    python scripts/collect_daily_ccu.py
    python scripts/collect_daily_ccu.py --maps 8530-0110-2817,0038-9297-7629
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.fncreate_service import fetch_map_from_api


# ============================================
# Configuration
# ============================================

HISTORICAL_DATA_DIR = Path(__file__).parent.parent / "data" / "historical"
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
TRACKED_MAPS_FILE = Path(__file__).parent.parent / "data" / "tracked_maps.json"


# ============================================
# Helper Functions
# ============================================

def get_tracked_maps() -> List[str]:
    """
    Get list of map codes to track.
    Sources:
    1. tracked_maps.json (manually curated list)
    2. All maps in data/raw/ directory
    """
    tracked = set()
    
    # Load from tracked_maps.json if exists
    if TRACKED_MAPS_FILE.exists():
        try:
            with open(TRACKED_MAPS_FILE) as f:
                data = json.load(f)
                tracked.update(data.get('maps', []))
        except Exception as e:
            print(f"⚠️  Error loading tracked_maps.json: {e}")
    
    # Also include all maps from raw data directory
    if RAW_DATA_DIR.exists():
        for file in RAW_DATA_DIR.glob("map_*.json"):
            # Extract map code from filename (map_XXXX-XXXX-XXXX.json)
            map_code = file.stem.replace("map_", "")
            tracked.add(map_code)
    
    return list(tracked)


def save_daily_snapshot(map_code: str, map_data: Dict, date: str) -> bool:
    """
    Save a daily CCU snapshot for a map.
    
    Args:
        map_code: Map code
        map_data: Full map data from API
        date: Date string (YYYY-MM-DD)
    
    Returns:
        True if saved successfully
    """
    # Create directory for this map
    map_dir = HISTORICAL_DATA_DIR / map_code.replace("-", "")
    map_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract CCU data from stats_7d
    stats_7d = map_data.get('stats_7d', {})
    if not stats_7d.get('success'):
        return False
    
    ccu_readings = stats_7d.get('data', {}).get('stats', [])
    if not ccu_readings:
        return False
    
    # Get date range
    date_from = stats_7d.get('data', {}).get('from', '')
    date_to = stats_7d.get('data', {}).get('to', '')
    
    # Calculate summary stats
    import numpy as np
    arr = np.array(ccu_readings)
    
    snapshot = {
        "map_code": map_code,
        "map_name": map_data.get('map_data', {}).get('name', 'Unknown'),
        "collection_date": date,
        "collection_timestamp": datetime.now().isoformat(),
        "data_range": {
            "from": date_from,
            "to": date_to
        },
        "ccu_readings": ccu_readings,
        "num_readings": len(ccu_readings),
        "summary": {
            "avg_ccu": round(float(np.mean(arr)), 2),
            "max_ccu": int(np.max(arr)),
            "min_ccu": int(np.min(arr)),
            "std_ccu": round(float(np.std(arr)), 2),
            "median_ccu": round(float(np.median(arr)), 2)
        }
    }
    
    # Save to file
    snapshot_file = map_dir / f"{date}.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    return True


def get_historical_data(map_code: str, days: int = 30) -> List[Dict]:
    """
    Load historical data for a map.
    
    Args:
        map_code: Map code
        days: Number of days to load
    
    Returns:
        List of daily snapshots, sorted by date
    """
    map_dir = HISTORICAL_DATA_DIR / map_code.replace("-", "")
    if not map_dir.exists():
        return []
    
    snapshots = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for file in sorted(map_dir.glob("*.json")):
        try:
            date_str = file.stem  # YYYY-MM-DD
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date >= cutoff_date:
                with open(file) as f:
                    snapshots.append(json.load(f))
        except Exception:
            continue
    
    return sorted(snapshots, key=lambda x: x.get('collection_date', ''))


def get_combined_ccu_series(map_code: str, days: int = 30) -> List[float]:
    """
    Get combined CCU series from historical data.
    Useful for anomaly detection with longer context.
    
    Args:
        map_code: Map code
        days: Number of days to include
    
    Returns:
        Combined CCU readings list
    """
    snapshots = get_historical_data(map_code, days)
    
    combined = []
    for snapshot in snapshots:
        combined.extend(snapshot.get('ccu_readings', []))
    
    return combined


# ============================================
# Main Collection Function
# ============================================

async def collect_daily_data(map_codes: Optional[List[str]] = None, verbose: bool = True) -> Dict:
    """
    Collect daily CCU data for specified maps (or all tracked maps).
    
    Args:
        map_codes: List of map codes to collect (None = all tracked)
        verbose: Print progress
    
    Returns:
        Summary of collection results
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    if map_codes is None:
        map_codes = get_tracked_maps()
    
    if verbose:
        print(f"📅 Daily CCU Collection - {today}")
        print(f"📊 Maps to collect: {len(map_codes)}")
        print("=" * 50)
    
    results = {
        "date": today,
        "total_maps": len(map_codes),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    for i, map_code in enumerate(map_codes, 1):
        try:
            if verbose:
                print(f"  [{i}/{len(map_codes)}] {map_code}...", end=" ")
            
            # Check if already collected today
            map_dir = HISTORICAL_DATA_DIR / map_code.replace("-", "")
            today_file = map_dir / f"{today}.json"
            
            if today_file.exists():
                if verbose:
                    print("⏭️  Already collected")
                results["skipped"] += 1
                continue
            
            # Fetch map data
            map_data = await fetch_map_from_api(map_code)
            
            if not map_data:
                if verbose:
                    print("❌ Not found")
                results["failed"] += 1
                results["errors"].append({"map_code": map_code, "error": "Map not found"})
                continue
            
            # Save snapshot
            success = save_daily_snapshot(map_code, map_data, today)
            
            if success:
                if verbose:
                    print("✅ Saved")
                results["successful"] += 1
            else:
                if verbose:
                    print("❌ No CCU data")
                results["failed"] += 1
                results["errors"].append({"map_code": map_code, "error": "No CCU data"})
                
        except Exception as e:
            if verbose:
                print(f"❌ Error: {e}")
            results["failed"] += 1
            results["errors"].append({"map_code": map_code, "error": str(e)})
    
    if verbose:
        print("=" * 50)
        print(f"✅ Successful: {results['successful']}")
        print(f"⏭️  Skipped: {results['skipped']}")
        print(f"❌ Failed: {results['failed']}")
    
    # Save collection log
    logs_dir = HISTORICAL_DATA_DIR / "_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"collection_{today}.json"
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


# ============================================
# CLI Entry Point
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Collect daily CCU data for maps")
    parser.add_argument(
        "--maps", 
        type=str, 
        help="Comma-separated list of map codes (default: all tracked maps)"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Suppress output"
    )
    
    args = parser.parse_args()
    
    map_codes = None
    if args.maps:
        map_codes = [m.strip() for m in args.maps.split(",")]
    
    asyncio.run(collect_daily_data(map_codes, verbose=not args.quiet))


if __name__ == "__main__":
    main()

