"""
Fetch Map Data from FNCreate.gg API
====================================
Collects Fortnite Creative map data and stats from fncreate.gg
"""

import asyncio
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Base URL
BASE_URL = "https://fncreate.gg"

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)


async def fetch_all_maps(max_maps: int = 200) -> List[Dict]:
    """
    Fetch all maps from FNCreate API with pagination
    
    Args:
        max_maps: Maximum number of maps to fetch
    
    Returns:
        List of map data dictionaries
    """
    print(f"🗺️  Fetching up to {max_maps} maps from {BASE_URL}/api/maps...")
    
    all_maps = []
    page = 1
    
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        while len(all_maps) < max_maps:
            try:
                # Try pagination
                response = await client.get(
                    f"{BASE_URL}/api/maps", 
                    params={"noepic": "true", "page": page}
                )
                response.raise_for_status()
                
                maps_data = response.json()
                
                # Handle different response formats
                if isinstance(maps_data, list):
                    maps_list = maps_data
                elif isinstance(maps_data, dict) and 'maps' in maps_data:
                    maps_list = maps_data['maps']
                elif isinstance(maps_data, dict) and 'data' in maps_data:
                    maps_list = maps_data['data']
                else:
                    maps_list = [maps_data] if isinstance(maps_data, dict) else []
                
                # If no more maps, break
                if not maps_list:
                    print(f"   No more maps on page {page}")
                    break
                
                all_maps.extend(maps_list)
                print(f"   Page {page}: +{len(maps_list)} maps (total: {len(all_maps)})")
                
                page += 1
                
                # If we got less than expected, probably no more pages
                if len(maps_list) < 20:
                    break
                    
            except httpx.HTTPError as e:
                print(f"❌ Error fetching page {page}: {e}")
                break
    
    # Limit to max_maps
    all_maps = all_maps[:max_maps]
    
    print(f"✅ Fetched {len(all_maps)} total maps")
    return all_maps


async def fetch_map_details(mnemonic: str) -> Optional[Dict]:
    """
    Fetch detailed map information including creator
    
    Args:
        mnemonic: Map code (e.g., '8530-0110-2817')
    
    Returns:
        Map details dictionary or None
    """
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/maps/{mnemonic}",
                params={"cs": "true"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"    ⚠️  Error fetching details: {e}")
            return None


async def fetch_map_stats(mnemonic: str, time_type: str = "24h") -> Optional[Dict]:
    """
    Fetch map statistics
    
    Args:
        mnemonic: Map code
        time_type: Time range ('24h', '7d', '30d', 'all')
    
    Returns:
        Stats dictionary or None
    """
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/maps/{mnemonic}/v2/stats",
                json={"type": time_type}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"    ⚠️  Error fetching stats: {e}")
            return None


async def fetch_map_discovery(mnemonic: str) -> Optional[Dict]:
    """
    Fetch map discovery/ranking data
    
    Args:
        mnemonic: Map code
    
    Returns:
        Discovery data or None
    """
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/maps/{mnemonic}/discovery")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            # Discovery data may not exist for all maps
            return None


async def save_map_data(map_code: str, map_data: Dict, stats: Dict, discovery: Dict):
    """Save complete map data to JSON file"""
    file_path = DATA_DIR / f"map_{map_code.replace('-', '_')}.json"
    
    complete_data = {
        "map_code": map_code,
        "map_data": map_data,
        "stats": stats,
        "discovery": discovery,
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }
    
    with open(file_path, 'w') as f:
        json.dump(complete_data, f, indent=2)


async def main():
    """Main data collection workflow"""
    print("\n" + "="*60)
    print("🌾 PROJECT HARVEST - FNCREATE.GG DATA COLLECTION")
    print("="*60 + "\n")
    
    # Fetch all maps (target: 200)
    maps = await fetch_all_maps(max_maps=200)
    
    if not maps:
        print("❌ No maps fetched. Exiting.")
        return
    
    # Save maps list
    maps_file = DATA_DIR / "maps_list.json"
    with open(maps_file, 'w') as f:
        json.dump(maps, f, indent=2)
    print(f"💾 Saved maps list to: {maps_file}\n")
    
    # Fetch detailed data for each map
    print(f"🔄 Fetching detailed data for {len(maps)} maps...\n")
    
    active_maps = []
    
    for i, map_item in enumerate(maps, 1):
        # Get map code (handle different field names)
        map_code = map_item.get('id') or map_item.get('mnemonic') or map_item.get('code') or map_item.get('map_code')
        
        if not map_code:
            print(f"{i}/{len(maps)} - ⏭️  Skipping map (no code found): {map_item}")
            continue
        
        print(f"{i}/{len(maps)} - Processing map: {map_code}")
        
        # Fetch all data for this map
        map_details = await fetch_map_details(map_code)
        stats_24h = await fetch_map_stats(map_code, "24h")
        stats_7d = await fetch_map_stats(map_code, "7d")
        discovery = await fetch_map_discovery(map_code)
        
        # Check if map has any meaningful data
        has_data = (
            (map_details and map_details != {}) or
            (stats_24h and stats_24h != {}) or
            (stats_7d and stats_7d != {}) or
            (discovery and discovery != {})
        )
        
        if has_data:
            print(f"  ✅ Has data - SAVING")
            
            # Combine all stats
            combined_stats = {
                "stats_24h": stats_24h,
                "stats_7d": stats_7d
            }
            
            await save_map_data(map_code, map_details or map_item, combined_stats, discovery)
            active_maps.append({
                "map_code": map_code,
                "has_details": map_details is not None,
                "has_stats": stats_24h is not None or stats_7d is not None,
                "has_discovery": discovery is not None
            })
        else:
            print(f"  ⏭️  No data available - skipping")
        
        # Rate limiting
        await asyncio.sleep(0.3)
    
    # Summary
    print("\n" + "="*60)
    print(f"✅ DATA COLLECTION COMPLETE")
    print("="*60)
    print(f"Total maps processed: {len(maps)}")
    print(f"Maps with data saved: {len(active_maps)}")
    print(f"Success rate: {(len(active_maps)/len(maps)*100):.1f}%")
    print(f"\nData saved to: {DATA_DIR}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

