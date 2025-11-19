"""
Fetch ALL Available Maps from FNCreate.gg API
==============================================
Uses multiple endpoints to maximize map collection
"""

import asyncio
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

BASE_URL = "https://fncreate.gg"
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)


async def fetch_maps_from_maps_endpoint() -> List[str]:
    """Fetch map codes from /api/maps"""
    print("🗺️  Fetching from /api/maps...")
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            r = await client.get(f"{BASE_URL}/api/maps", params={"noepic": "true"})
            r.raise_for_status()
            response_data = r.json()
            
            # Handle both old and new API response formats
            if isinstance(response_data, dict) and 'data' in response_data:
                maps = response_data.get('data', [])
            else:
                maps = response_data
            
            # Filter for creative map codes only (format: ####-####-####)
            import re
            codes = [m['id'] for m in maps if re.match(r'^\d{4}-\d{4}-\d{4}$', m.get('id', ''))]
            print(f"   ✅ Got {len(codes)} creative map codes")
            return codes
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []


async def fetch_maps_from_discovery_surface() -> List[str]:
    """Fetch map codes from /api/discovery/surface"""
    print("🗺️  Fetching from /api/discovery/surface...")
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            r = await client.get(f"{BASE_URL}/api/discovery/surface", params={"date": "latest"})
            r.raise_for_status()
            data = r.json()
            
            if data.get('success'):
                maps = data.get('data', {}).get('maps', [])
                # Filter for creative map codes
                import re
                codes = []
                for m in maps:
                    code = m.get('id') or m.get('map_id')
                    if code and re.match(r'^\d{4}-\d{4}-\d{4}$', code):
                        codes.append(code)
                print(f"   ✅ Got {len(codes)} creative map codes")
                return codes
            return []
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []


async def fetch_maps_from_discovery_top() -> List[str]:
    """Fetch map codes from /api/discovery/top"""
    print("🗺️  Fetching from /api/discovery/top...")
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            r = await client.get(f"{BASE_URL}/api/discovery/top", params={"date": "latest"})
            r.raise_for_status()
            data = r.json()
            
            if data.get('success'):
                results = data.get('data', {}).get('results', [])
                # Filter for creative map codes
                import re
                codes = [r.get('map_id') for r in results if re.match(r'^\d{4}-\d{4}-\d{4}$', r.get('map_id', ''))]
                print(f"   ✅ Got {len(codes)} creative map codes")
                return codes
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
    """Fetch map statistics"""
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            r = await client.post(f"{BASE_URL}/api/maps/{code}/v2/stats", json={"type": "7d"})
            r.raise_for_status()
            return {"stats_7d": r.json()}
        except:
            return {"stats_7d": None}


async def save_map_data(code: str, map_data: Dict, stats: Dict):
    """Save complete map data"""
    file_path = DATA_DIR / f"map_{code.replace('-', '_')}.json"
    complete_data = {
        "map_code": code,
        "map_data": map_data,
        "stats": stats,
        "fetched_at": datetime.utcnow().isoformat() + "Z"
    }
    with open(file_path, 'w') as f:
        json.dump(complete_data, f, indent=2)


async def main():
    print("\n" + "="*60)
    print("🌾 PROJECT HARVEST - COLLECTING ALL MAPS")
    print("="*60 + "\n")
    
    # Collect map codes from all endpoints
    all_codes: Set[str] = set()
    
    codes1 = await fetch_maps_from_maps_endpoint()
    all_codes.update(codes1)
    await asyncio.sleep(1)
    
    codes2 = await fetch_maps_from_discovery_surface()
    all_codes.update(codes2)
    await asyncio.sleep(1)
    
    codes3 = await fetch_maps_from_discovery_top()
    all_codes.update(codes3)
    
    print(f"\n📊 Total unique map codes found: {len(all_codes)}")
    
    # Fetch detailed data for each map
    print(f"\n🔄 Fetching detailed data for {len(all_codes)} maps...\n")
    
    saved_count = 0
    for i, code in enumerate(sorted(all_codes), 1):
        print(f"{i}/{len(all_codes)} - Processing {code}")
        
        map_details = await fetch_map_details(code)
        if not map_details or not map_details.get('success'):
            print(f"  ⏭️  No details available")
            await asyncio.sleep(0.3)
            continue
        
        stats = await fetch_map_stats(code)
        
        await save_map_data(code, map_details, stats)
        print(f"  ✅ Saved")
        saved_count += 1
        
        await asyncio.sleep(0.3)  # Rate limiting
    
    print("\n" + "="*60)
    print(f"✅ DATA COLLECTION COMPLETE")
    print("="*60)
    print(f"Unique maps found: {len(all_codes)}")
    print(f"Maps saved: {saved_count}")
    print(f"Data saved to: {DATA_DIR}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

