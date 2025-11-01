"""
Disk cache for API responses to speed up repeated queries
"""
import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta


def get_cache_dir():
    """Get or create cache directory"""
    home = Path.home()
    cache_dir = home / ".cache" / "autopahe"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _hash_key(url: str) -> str:
    """Generate cache key from URL"""
    return hashlib.md5(url.encode()).hexdigest()


def cache_get(url: str, max_age_hours: int = 24):
    """
    Get cached response if available and not expired
    
    Args:
        url: URL to check cache for
        max_age_hours: Maximum age in hours before cache expires
    
    Returns:
        Cached content bytes or None if not found/expired
    """
    cache_dir = get_cache_dir()
    key = _hash_key(url)
    cache_file = cache_dir / f"{key}.cache"
    meta_file = cache_dir / f"{key}.meta"
    
    if not cache_file.exists() or not meta_file.exists():
        return None
    
    try:
        with open(meta_file, 'r') as f:
            meta = json.load(f)
        
        cached_time = datetime.fromisoformat(meta['timestamp'])
        age = datetime.now() - cached_time
        
        if age > timedelta(hours=max_age_hours):
            # Expired
            cache_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
            return None
        
        with open(cache_file, 'rb') as f:
            return f.read()
    except Exception:
        return None


def cache_set(url: str, content: bytes):
    """
    Store content in cache
    
    Args:
        url: URL key
        content: Response content bytes
    """
    cache_dir = get_cache_dir()
    key = _hash_key(url)
    cache_file = cache_dir / f"{key}.cache"
    meta_file = cache_dir / f"{key}.meta"
    
    try:
        with open(cache_file, 'wb') as f:
            f.write(content)
        
        meta = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'size': len(content)
        }
        
        with open(meta_file, 'w') as f:
            json.dump(meta, f)
    except Exception:
        pass


def cache_clear(max_age_days: int = 7):
    """
    Clear old cache entries
    
    Args:
        max_age_days: Delete entries older than this many days
    """
    cache_dir = get_cache_dir()
    cutoff = datetime.now() - timedelta(days=max_age_days)
    
    for meta_file in cache_dir.glob("*.meta"):
        try:
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            
            cached_time = datetime.fromisoformat(meta['timestamp'])
            if cached_time < cutoff:
                # Delete both files
                key = meta_file.stem
                cache_file = cache_dir / f"{key}.cache"
                cache_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
        except Exception:
            continue


def get_cache_stats():
    """Get cache statistics"""
    cache_dir = get_cache_dir()
    cache_files = list(cache_dir.glob("*.cache"))
    
    total_size = sum(f.stat().st_size for f in cache_files)
    count = len(cache_files)
    
    return {
        'count': count,
        'size_bytes': total_size,
        'size_mb': round(total_size / (1024 * 1024), 2),
        'path': str(cache_dir)
    }
