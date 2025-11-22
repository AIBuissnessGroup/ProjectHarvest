"""
Fetch Maps with Pagination from FNCreate.gg API
================================================
Uses pagination to fetch hundreds of maps ranked by player count
"""

import asyncio
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import re

BASE_URL = "https://fncreate.gg"
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
MAX_PAGES = 50  # Fetch up to 50 pages to get ~987 maps!
MAPS_PER_PAGE = 20


async def fetch_maps_page(page: int) -> List[str]:
    """Fetch map codes from a specific page"""
    print(f"📄 Fetching page {page}...")
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            r = await client.get(
                f"{BASE_URL}/api/maps",
                params={"page": page}  # Try without noepic filter
            )
            r.raise_for_status()
            response_data = r.json()
            
            # Handle both response formats
            if isinstance(response_data, dict) and 'data' in response_data:
                maps = response_data.get('data', [])
            else:
                maps = response_data if isinstance(response_data, list) else []
            
            # Filter for creative map codes only (format: ####-####-####)
            codes = [m['id'] for m in maps if re.match(r'^\d{4}-\d{4}-\d{4}$', m.get('id', ''))]
            
            if codes:
                print(f"   ✅ Got {len(codes)} creative maps from page {page}")
            else:
                print(f"   ⚠️  No maps on page {page} (end of data)")
            
            return codes
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"   ⚠️  Page {page} not found (end of data)")
            else:
                print(f"   ❌ HTTP Error {e.response.status_code}")
            return []
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []


async def fetch_map_details(code: str) -> Dict:
    """Fetch detailed map information"""
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            r = await client.get(f"{BASE_URL}/api/maps/{code}", params={"cs": "true"})
            r.raise_for_status()
            return r.json()
        except:
            return None


async def fetch_map_stats(code: str) -> Dict:
    """Fetch 7-day stats for a map"""
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            # Fetch 24h stats
            r_24h = await client.post(f"{BASE_URL}/api/maps/{code}/v2/stats", json={"type": "24h"})
            stats_24h = r_24h.json() if r_24h.status_code == 200 else None
            
            # Fetch 7d stats
            r_7d = await client.post(f"{BASE_URL}/api/maps/{code}/v2/stats", json={"type": "7d"})
            stats_7d = r_7d.json() if r_7d.status_code == 200 else None
            
            return {
                "stats_24h": stats_24h,
                "stats_7d": stats_7d
            }
        except:
            return {"stats_24h": None, "stats_7d": None}


async def save_map_data(code: str, map_data: Dict, stats: Dict):
    """Save complete map data to JSON file"""
    file_path = DATA_DIR / f"map_{code.replace('-', '_')}.json"
    complete_data = {
        "map_code": code,
        "map_data": map_data.get('data') if map_data else None,
        "stats_24h": stats.get('stats_24h'),
        "stats_7d": stats.get('stats_7d'),
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }
    with open(file_path, 'w') as f:
        json.dump(complete_data, f, indent=2)


async def clear_old_data():
    """Clear old map data files"""
    print("\n🗑️  Clearing old map data...")
    for file in DATA_DIR.glob("map_*.json"):
        file.unlink()
    print("   ✅ Old data cleared\n")


async def main():
    print("\n" + "="*70)
    print("🌾 PROJECT HARVEST - PAGINATED MAP COLLECTION")
    print("="*70)
    print(f"Fetching up to {MAX_PAGES} pages ({MAX_PAGES * MAPS_PER_PAGE} maps max)")
    print(f"Maps ranked by player count (most popular first)")
    print("="*70 + "\n")
    
    # Clear old data
    await clear_old_data()
    
    # Collect map codes from all pages
    all_codes: Set[str] = set()
    
    for page in range(1, MAX_PAGES + 1):
        codes = await fetch_maps_page(page)
        
        if not codes:
            print(f"\n✋ Stopped at page {page} (no more data)\n")
            break
        
        all_codes.update(codes)
        await asyncio.sleep(0.5)  # Rate limiting between pages
    
    print("\n" + "="*70)
    print(f"📊 TOTAL UNIQUE MAPS FOUND: {len(all_codes)}")
    print("="*70 + "\n")
    
    # Fetch detailed data for each map
    print(f"🔄 Fetching detailed data for {len(all_codes)} maps...\n")
    
    saved_count = 0
    skipped_count = 0
    
    for i, code in enumerate(sorted(all_codes), 1):
        print(f"[{i}/{len(all_codes)}] Processing {code}...", end=" ")
        
        # Fetch map details
        map_details = await fetch_map_details(code)
        if not map_details or not map_details.get('success'):
            print("❌ No details")
            skipped_count += 1
            await asyncio.sleep(0.3)
            continue
        
        # Check if map has CCU record (required for ML training)
        map_data = map_details.get('data', {})
        if not map_data.get('ccu_record') or map_data.get('ccu_record') == 0:
            print("⏭️  No CCU record")
            skipped_count += 1
            await asyncio.sleep(0.3)
            continue
        
        # Fetch stats
        stats = await fetch_map_stats(code)
        
        # Save
        await save_map_data(code, map_details, stats)
        print(f"✅ Saved (Peak: {map_data.get('ccu_record'):,})")
        saved_count += 1
        
        await asyncio.sleep(0.3)  # Rate limiting
    
    # Summary
    print("\n" + "="*70)
    print("✅ DATA COLLECTION COMPLETE!")
    print("="*70)
    print(f"Pages fetched:     {min(page, MAX_PAGES)}")
    print(f"Unique maps found: {len(all_codes)}")
    print(f"Maps saved:        {saved_count}")
    print(f"Maps skipped:      {skipped_count}")
    print(f"Data location:     {DATA_DIR}")
    print("="*70)
    print(f"\n🎯 Ready to retrain with {saved_count} maps!\n")
    
    # Create summary file
    summary = {
        "collection_date": datetime.utcnow().isoformat() + "Z",
        "total_maps_found": len(all_codes),
        "maps_saved": saved_count,
        "maps_skipped": skipped_count,
        "pages_fetched": min(page, MAX_PAGES)
    }
    with open(DATA_DIR / "collection_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())

