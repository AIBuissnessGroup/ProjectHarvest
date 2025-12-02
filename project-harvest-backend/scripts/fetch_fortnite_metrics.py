"""
Fetch Fortnite Ecosystem API metrics for our existing fncreate.gg maps.
This enriches our dataset with official retention, engagement, and virality data.
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Fortnite Ecosystem API base URL
FORTNITE_API_BASE = "https://api.fortnite.com/ecosystem/v1"

# Directories
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
FORTNITE_DATA_DIR = Path(__file__).parent.parent / "data" / "fortnite_metrics"
FORTNITE_DATA_DIR.mkdir(exist_ok=True, parents=True)


async def fetch_all_metrics(
    client: httpx.AsyncClient,
    map_code: str,
) -> Optional[Dict]:
    """
    Fetch all available metrics for a single map from Fortnite API.
    Returns a combined dict with all metrics.
    """
    
    # Calculate date range (last 7 days)
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=7)
    
    from_str = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_str = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Fetch the combined metrics endpoint (more efficient than individual calls)
    # We can get multiple metrics in one request
    url = f"{FORTNITE_API_BASE}/islands/{map_code}/metrics/day"
    params = {
        "from": from_str,
        "to": to_str,
        "metrics": [
            "peakCCU",
            "uniquePlayers", 
            "plays",
            "favorites",
            "recommendations",
            "minutesPlayed",
            "averageMinutesPerPlayer",
            "retention"
        ]
    }
    
    try:
        response = await client.get(url, params=params, follow_redirects=True, timeout=30.0)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "map_code": map_code,
                "fetched_at": datetime.utcnow().isoformat(),
                "status": "success",
                "metrics": data
            }
        elif response.status_code == 404:
            return {
                "map_code": map_code,
                "fetched_at": datetime.utcnow().isoformat(),
                "status": "not_found",
                "error": "Map not found in Fortnite API"
            }
        else:
            return {
                "map_code": map_code,
                "fetched_at": datetime.utcnow().isoformat(),
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "details": response.text[:200]
            }
            
    except Exception as e:
        return {
            "map_code": map_code,
            "fetched_at": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }


async def fetch_fortnite_metrics_for_existing_maps(batch_size: int = 10):
    """
    Fetch Fortnite API metrics for all maps in our fncreate.gg dataset.
    
    Args:
        batch_size: Number of concurrent requests (be respectful to API)
    """
    
    # Get all existing map files
    map_files = sorted(RAW_DATA_DIR.glob("map_*.json"))
    
    print(f"\n🔍 Found {len(map_files)} maps in fncreate.gg dataset")
    print(f"📊 Fetching Fortnite API metrics for each map...\n")
    
    # Extract map codes
    map_codes = []
    for map_file in map_files:
        # map_8530_0110_2817.json -> 8530-0110-2817
        filename = map_file.stem
        parts = filename.replace("map_", "").split("_")
        if len(parts) == 3:
            map_code = "-".join(parts)
            map_codes.append((map_code, map_file))
    
    print(f"✅ Extracted {len(map_codes)} valid map codes\n")
    
    # Stats
    stats = {
        "total": len(map_codes),
        "success": 0,
        "not_found": 0,
        "error": 0
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(map_codes), batch_size):
            batch = map_codes[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(map_codes) + batch_size - 1) // batch_size
            
            print(f"📦 Batch {batch_num}/{total_batches} (maps {i+1}-{min(i+batch_size, len(map_codes))})")
            
            # Fetch all maps in this batch concurrently
            tasks = [fetch_all_metrics(client, code) for code, _ in batch]
            results = await asyncio.gather(*tasks)
            
            # Save results and update stats
            for (map_code, map_file), result in zip(batch, results):
                if result:
                    # Save individual metric file
                    output_file = FORTNITE_DATA_DIR / f"fortnite_{map_code.replace('-', '_')}.json"
                    with open(output_file, "w") as f:
                        json.dump(result, f, indent=2)
                    
                    # Update stats
                    status = result.get("status", "error")
                    if status == "success":
                        stats["success"] += 1
                        print(f"  ✅ {map_code} - Success")
                    elif status == "not_found":
                        stats["not_found"] += 1
                        print(f"  ⚠️  {map_code} - Not found in Fortnite API")
                    else:
                        stats["error"] += 1
                        print(f"  ❌ {map_code} - Error: {result.get('error', 'Unknown')}")
            
            print()  # Blank line between batches
            
            # Small delay between batches to be respectful
            await asyncio.sleep(1.0)
    
    # Save summary
    summary = {
        "fetched_at": datetime.utcnow().isoformat(),
        "total_maps": stats["total"],
        "successful": stats["success"],
        "not_found": stats["not_found"],
        "errors": stats["error"],
        "success_rate": f"{(stats['success'] / stats['total'] * 100):.1f}%",
        "data_directory": str(FORTNITE_DATA_DIR)
    }
    
    summary_file = FORTNITE_DATA_DIR / "fetch_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    # Print final stats
    print("\n" + "="*60)
    print("📊 FETCH COMPLETE!")
    print("="*60)
    print(f"✅ Successful: {stats['success']}/{stats['total']} ({summary['success_rate']})")
    print(f"⚠️  Not Found: {stats['not_found']}")
    print(f"❌ Errors: {stats['error']}")
    print(f"📁 Data saved to: {FORTNITE_DATA_DIR}")
    print(f"📄 Summary: {summary_file}")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Fetch with batch size of 10 (10 concurrent requests at a time)
    asyncio.run(fetch_fortnite_metrics_for_existing_maps(batch_size=10))

