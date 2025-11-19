"""
Redis Cache Service
===================
Fast in-memory caching for API responses
"""

import json
import redis
from typing import Optional, Any
from app.core.config import settings


class CacheService:
    """
    Redis cache wrapper for storing and retrieving data
    
    Usage:
        cache = CacheService()
        await cache.set("islands", data, ttl=3600)
        data = await cache.get("islands")
    """
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,  # Auto-decode bytes to strings
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            print(f"✅ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except redis.ConnectionError as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("   Cache will be disabled - API will work but slower")
            self.redis_client = None
    
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache
        
        Args:
            key: Cache key (e.g., "islands", "island:1333-6845-4920")
        
        Returns:
            Cached data (parsed from JSON) or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                print(f"🎯 Cache HIT: {key}")
                return json.loads(data)
            else:
                print(f"❌ Cache MISS: {key}")
                return None
        except Exception as e:
            print(f"⚠️  Cache get error for {key}: {e}")
            return None
    
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Store data in cache
        
        Args:
            key: Cache key
            value: Data to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 1 hour)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(
                name=key,
                time=ttl,
                value=serialized
            )
            print(f"💾 Cached: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            print(f"⚠️  Cache set error for {key}: {e}")
            return False
    
    
    async def delete(self, key: str) -> bool:
        """
        Remove data from cache
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if deleted, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            if result:
                print(f"🗑️  Deleted cache: {key}")
            return bool(result)
        except Exception as e:
            print(f"⚠️  Cache delete error for {key}: {e}")
            return False
    
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern
        
        Args:
            pattern: Redis pattern (e.g., "island:*" deletes all island keys)
        
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                print(f"🗑️  Deleted {deleted} keys matching: {pattern}")
                return deleted
            return 0
        except Exception as e:
            print(f"⚠️  Cache clear pattern error for {pattern}: {e}")
            return 0
    
    
    async def flush_all(self) -> bool:
        """
        Clear entire cache (use with caution!)
        
        Returns:
            True if successful
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            print("🗑️  Flushed entire cache")
            return True
        except Exception as e:
            print(f"⚠️  Cache flush error: {e}")
            return False
    
    
    def is_connected(self) -> bool:
        """
        Check if Redis is connected
        
        Returns:
            True if connected and working
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False


# ============================================
# Global Cache Instance
# ============================================
# Single instance shared across the app

cache = CacheService()


# ============================================
# Cache Key Helpers
# ============================================

def make_island_key(code: str) -> str:
    """Generate cache key for specific island"""
    return f"island:{code}"


def make_islands_list_key() -> str:
    """Generate cache key for islands list"""
    return "islands:list"


def make_metrics_key(code: str, interval: str = "day") -> str:
    """Generate cache key for island metrics"""
    return f"metrics:{code}:{interval}"

