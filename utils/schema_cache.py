"""
Schema caching module for metadata persistence
Implements local caching with 24-hour TTL
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class SchemaCache:
    """Manage local schema cache with TTL"""
    
    DEFAULT_TTL_HOURS = 24
    
    def __init__(self, cache_dir: Path):
        """Initialize cache manager"""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_file_path(self, key: str) -> Path:
        """Get cache file path for a given key"""
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def _is_expired(self, timestamp: float, ttl_hours: int = DEFAULT_TTL_HOURS) -> bool:
        """Check if cache entry has expired"""
        expiry_time = datetime.fromtimestamp(timestamp) + timedelta(hours=ttl_hours)
        return datetime.now() > expiry_time
    
    def get(self, key: str, ttl_hours: int = DEFAULT_TTL_HOURS) -> Optional[Dict]:
        """
        Get cached data if not expired
        Returns None if cache miss or expired
        """
        cache_file = self._get_cache_file_path(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)
            
            timestamp = cache_entry.get("timestamp", 0)
            
            if self._is_expired(timestamp, ttl_hours):
                # Cache expired, delete file
                cache_file.unlink(missing_ok=True)
                return None
            
            return cache_entry.get("data")
        
        except Exception as e:
            # Invalid cache file, delete it
            cache_file.unlink(missing_ok=True)
            return None
    
    def set(self, key: str, data: Any) -> bool:
        """
        Store data in cache with current timestamp
        Returns True on success
        """
        cache_file = self._get_cache_file_path(key)
        
        try:
            cache_entry = {
                "timestamp": time.time(),
                "data": data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2)
            
            return True
        
        except Exception as e:
            return False
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate (delete) a specific cache entry
        Returns True if file was deleted
        """
        cache_file = self._get_cache_file_path(key)
        
        try:
            if cache_file.exists():
                cache_file.unlink()
                return True
            return False
        except Exception:
            return False
    
    def clear_all(self) -> int:
        """
        Clear all cache entries
        Returns number of files deleted
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1
        except Exception:
            pass
        
        return count
    
    def get_cache_info(self, key: str) -> Optional[Dict]:
        """
        Get cache metadata (timestamp, age) without returning data
        Returns None if cache miss
        """
        cache_file = self._get_cache_file_path(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)
            
            timestamp = cache_entry.get("timestamp", 0)
            age_seconds = time.time() - timestamp
            
            return {
                "timestamp": timestamp,
                "age_seconds": age_seconds,
                "age_hours": age_seconds / 3600,
                "is_expired": self._is_expired(timestamp)
            }
        
        except Exception:
            return None
