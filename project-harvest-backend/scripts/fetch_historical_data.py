"""
Project Harvest - Data Collection Script
=========================================
This script fetches historical Fortnite island data from the Ecosystem API

What it does:
1. Fetches all islands (with pagination)
2. For each island, fetches all available metrics
3. Saves data as JSON files for ML training

Usage:
    python scripts/fetch_historical_data.py
"""

import httpx
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


# ============================================
# Configuration
# ============================================
FORTNITE_API_BASE = "https://api.fortnite.com/ecosystem/v1"
DATA_DIR = Path("data/raw")

# Metrics we want to collect (from the API you showed)
METRIC_TYPES = [
    "peak-ccu",                      # Peak concurrent users
    "favorites",                     # How many players favorited the map
    "minutes-played",                # Total playtime
    "average-minutes-per-player",    # Avg session length
    "recommendations",               # Algorithm recommendations
    "unique-players",                # Total unique players
    "plays",                         # Total play sessions
    "retention"                      # Player retention rate
]


# ============================================
# Helper Functions
# ============================================

async def fetch_all_islands(max_islands: Optional[int] = None) -> List[Dict]:
    """
    Fetch all islands using pagination
    
    Args:
        max_islands: Optional limit (useful for testing with smaller datasets)
    
    Returns:
        List of island objects
    """
    print("🔍 Fetching islands from Fortnite API...")
    
    islands = []
    cursor = None
    page = 1
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        while True:
            # Build request parameters
            params = {"size": 100}  # Max allowed per request
            if cursor:
                params["after"] = cursor
            
            try:
                # Make API request
                response = await client.get(
                    f"{FORTNITE_API_BASE}/islands",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Add islands from this page
                page_islands = data.get("data", [])
                islands.extend(page_islands)
                
                print(f"  📄 Page {page}: Fetched {len(page_islands)} islands (Total: {len(islands)})")
                
                # Check if we should stop
                if max_islands and len(islands) >= max_islands:
                    islands = islands[:max_islands]
                    print(f"  ⚠️  Reached limit of {max_islands} islands")
                    break
                
                # Get next cursor for pagination
                meta = data.get("meta", {})
                page_info = meta.get("page", {})
                cursor = page_info.get("nextCursor")
                
                # If no more pages, we're done
                if not cursor:
                    print("  ✅ Reached last page")
                    break
                
                page += 1
                
            except httpx.HTTPError as e:
                print(f"  ❌ Error fetching islands: {e}")
                break
    
    return islands


async def fetch_island_metrics(code: str, interval: str = "day") -> Dict:
    """
    Fetch all metrics for a specific island
    
    Args:
        code: Island code (e.g., "1234-1234-1234")
        interval: Time interval ("day", "hour", or "minute")
    
    Returns:
        Dictionary with all metrics
    """
    # Calculate date range (last 7 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # Format dates as ISO 8601
    from_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    to_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    
    metrics_data = {}
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for metric_type in METRIC_TYPES:
            # Skip metrics that aren't available for this interval
            if interval == "minute" and metric_type == "average-minutes-per-player":
                print(f"    ⏭️  {metric_type}: Not available for minute interval")
                metrics_data[metric_type] = None
                continue
            
            if interval in ["hour", "minute"] and metric_type == "retention":
                print(f"    ⏭️  {metric_type}: Only available for day interval")
                metrics_data[metric_type] = None
                continue
            
            try:
                # Build query parameters
                params = {
                    "from": from_date,
                    "to": to_date
                }
                
                # Fetch this metric
                response = await client.get(
                    f"{FORTNITE_API_BASE}/islands/{code}/metrics/{interval}/{metric_type}",
                    params=params
                )
                
                if response.status_code == 200:
                    metrics_data[metric_type] = response.json()
                elif response.status_code == 404:
                    # Metric not available for this island
                    metrics_data[metric_type] = None
                else:
                    print(f"    ⚠️  {metric_type}: HTTP {response.status_code}")
                    metrics_data[metric_type] = None
                    
            except httpx.HTTPError as e:
                print(f"    ❌ Error fetching {metric_type}: {e}")
                metrics_data[metric_type] = None
    
    return metrics_data


async def save_island_data(island: Dict, metrics: Dict):
    """
    Save island and its metrics to a JSON file
    
    Args:
        island: Island metadata
        metrics: Island metrics
    """
    # Create filename from island code (replace dashes with underscores)
    code = island["code"]
    filename = f"metrics_{code.replace('-', '_')}.json"
    filepath = DATA_DIR / filename
    
    # Combine island info and metrics
    combined_data = {
        "island": island,
        "metrics": metrics,
        "fetched_at": datetime.utcnow().isoformat(),
    }
    
    # Save to file
    with open(filepath, "w") as f:
        json.dump(combined_data, f, indent=2)


# ============================================
# Main Execution
# ============================================

async def main():
    """Main data collection workflow"""
    
    print("=" * 60)
    print("PROJECT HARVEST - DATA COLLECTION")
    print("=" * 60)
    print()
    
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # ========================================
    # Step 1: Fetch all islands
    # ========================================
    print("Step 1: Fetching island list...")
    print()
    
    # Fetch more islands to find active ones
    # We'll filter for islands with actual data later
    islands = await fetch_all_islands(max_islands=200)
    
    print()
    print(f"✅ Found {len(islands)} islands")
    print()
    
    # Save islands list
    islands_file = DATA_DIR / "islands.json"
    with open(islands_file, "w") as f:
        json.dump(islands, f, indent=2)
    print(f"💾 Saved islands list to: {islands_file}")
    print()
    
    # ========================================
    # Step 2: Fetch metrics for each island
    # ========================================
    print("Step 2: Fetching metrics and filtering for active islands...")
    print()
    
    active_islands = []
    
    for i, island in enumerate(islands, 1):
        code = island["code"]
        title = island.get("title", "Unknown")
        
        print(f"[{i}/{len(islands)}] {code} - {title}")
        
        # Fetch metrics
        metrics = await fetch_island_metrics(code)
        
        # Count how many metrics we got
        available_metrics = sum(1 for v in metrics.values() if v is not None)
        print(f"  📊 Collected {available_metrics}/{len(METRIC_TYPES)} metrics")
        
        # Check if this island has ANY actual data (non-null values)
        has_data = False
        for metric_name, metric_data in metrics.items():
            if metric_data and "intervals" in metric_data:
                for interval in metric_data["intervals"]:
                    if interval.get("value") is not None:
                        has_data = True
                        break
            if has_data:
                break
        
        if has_data:
            print(f"  ✅ Has active data - SAVING")
            await save_island_data(island, metrics)
            active_islands.append(island)
        else:
            print(f"  ⏭️  No data (inactive) - skipping")
        
        # Rate limiting - be nice to the API!
        # Wait 0.5 seconds between requests
        await asyncio.sleep(0.5)
    
    print()
    print("=" * 60)
    print("✨ DATA COLLECTION COMPLETE!")
    print("=" * 60)
    print()
    print(f"📁 Data saved to: {DATA_DIR.absolute()}")
    print(f"📊 Total islands checked: {len(islands)}")
    print(f"✅ Active islands (with data): {len(active_islands)}")
    print(f"⏭️  Inactive islands (skipped): {len(islands) - len(active_islands)}")
    print(f"📄 Total files saved: {len(list(DATA_DIR.glob('metrics_*.json')))}")
    print()
    if len(active_islands) > 0:
        print("Next step: Train ML model using this data!")
    else:
        print("⚠️  No active islands found. Try:")
        print("   - Increase max_islands to check more islands")
        print("   - Ask client for specific active island codes")
        print("   - Check if API requires special permissions")
    print()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())

