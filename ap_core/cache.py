"""
Advanced disk cache for API responses to speed up repeated queries
Features: auto-cleanup, compression, statistics, and smart management
"""
import os
import json
import hashlib
import time
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ap_core.platform_paths import get_cache_dir as _get_platform_cache_dir, ensure_dir


def get_cache_dir():
    """Get or create cache directory (cross-platform)"""
    cache_dir = _get_platform_cache_dir()
    ensure_dir(cache_dir)
    return cache_dir


def _hash_key(url: str) -> str:
    """Generate cache key from URL"""
    return hashlib.md5(url.encode()).hexdigest()


def cache_get(url: str, max_age_hours: int = 24, compressed: bool = True):
    """
    Get cached response if available and not expired
    
    Args:
        url: URL to check cache for
        max_age_hours: Maximum age in hours before cache expires
        compressed: Whether to use compressed cache files
    
    Returns:
        Cached content bytes or None if not found/expired
    """
    cache_dir = get_cache_dir()
    key = _hash_key(url)
    cache_file = cache_dir / f"{key}.cache.gz" if compressed else cache_dir / f"{key}.cache"
    meta_file = cache_dir / f"{key}.meta"
    
    if not cache_file.exists() or not meta_file.exists():
        return None
    
    try:
        with open(meta_file, 'r') as f:
            meta = json.load(f)
        
        cached_time = datetime.fromisoformat(meta['timestamp'])
        age = datetime.now() - cached_time
        
        if age > timedelta(hours=max_age_hours):
            # Expired - clean up
            cache_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
            return None
        
        # Update access statistics
        access_count = meta.get('access_count', 0) + 1
        meta['access_count'] = access_count
        meta['last_accessed'] = datetime.now().isoformat()
        
        with open(meta_file, 'w') as f:
            json.dump(meta, f, indent=2)
        
        # Read content (compressed or uncompressed)
        if compressed:
            with gzip.open(cache_file, 'rb') as f:
                return f.read()
        else:
            with open(cache_file, 'rb') as f:
                return f.read()
    except Exception:
        # If cache is corrupted, remove it
        cache_file.unlink(missing_ok=True)
        meta_file.unlink(missing_ok=True)
        return None


def cache_set(url: str, content: bytes, compressed: bool = True, tags: List[str] = None):
    """
    Store content in cache with compression and metadata
    
    Args:
        url: URL key
        content: Response content bytes
        compressed: Whether to compress the content
        tags: Optional tags for cache categorization
    """
    cache_dir = get_cache_dir()
    key = _hash_key(url)
    cache_file = cache_dir / f"{key}.cache.gz" if compressed else cache_dir / f"{key}.cache"
    meta_file = cache_dir / f"{key}.meta"
    
    try:
        # Store content (compressed or uncompressed)
        if compressed:
            with gzip.open(cache_file, 'wb') as f:
                f.write(content)
        else:
            with open(cache_file, 'wb') as f:
                f.write(content)
        
        # Enhanced metadata
        meta = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'size': len(content),
            'compressed': compressed,
            'compressed_size': cache_file.stat().st_size if compressed else len(content),
            'tags': tags or [],
            'access_count': 0,
            'last_accessed': datetime.now().isoformat()
        }
        
        with open(meta_file, 'w') as f:
            json.dump(meta, f, indent=2)
            
        # Auto-cleanup if cache is getting large
        auto_cleanup_if_needed()
        
    except Exception:
        # If storage fails, clean up any partial files
        cache_file.unlink(missing_ok=True)
        meta_file.unlink(missing_ok=True)


def cache_clear(max_age_days: int = 7, force: bool = False):
    """
    Clear old cache entries with enhanced options
    
    Args:
        max_age_days: Delete entries older than this many days
        force: If True, delete all cache regardless of age
    """
    cache_dir = get_cache_dir()
    
    if force:
        # Delete everything
        for file in cache_dir.glob("*"):
            file.unlink(missing_ok=True)
        return
    
    cutoff = datetime.now() - timedelta(days=max_age_days)
    
    for meta_file in cache_dir.glob("*.meta"):
        try:
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            
            cached_time = datetime.fromisoformat(meta['timestamp'])
            if cached_time < cutoff:
                # Delete both cache and meta files
                key = meta_file.stem
                cache_file = cache_dir / f"{key}.cache"
                cache_file_gz = cache_dir / f"{key}.cache.gz"
                cache_file.unlink(missing_ok=True)
                cache_file_gz.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
        except Exception:
            continue


def auto_cleanup_if_needed(max_size_mb: int = 500, max_count: int = 1000):
    """
    Automatically clean up cache if it exceeds thresholds
    
    Args:
        max_size_mb: Maximum cache size in MB
        max_count: Maximum number of cache entries
    """
    stats = get_detailed_cache_stats()
    
    if stats['size_mb'] > max_size_mb or stats['count'] > max_count:
        # Get all entries sorted by last accessed time
        entries = get_cache_entries_sorted()
        
        # Remove oldest entries until under limits
        while (stats['size_mb'] > max_size_mb * 0.8 or stats['count'] > max_count * 0.8) and entries:
            oldest = entries.pop(0)
            remove_cache_entry(oldest['key'])
            
            # Update stats
            stats = get_detailed_cache_stats()


def get_detailed_cache_stats() -> Dict:
    """Get comprehensive cache statistics"""
    cache_dir = get_cache_dir()
    entries = []
    
    total_size = 0
    total_original_size = 0
    access_count = 0
    
    for meta_file in cache_dir.glob("*.meta"):
        try:
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            
            key = meta_file.stem
            cache_file = cache_dir / f"{key}.cache"
            cache_file_gz = cache_dir / f"{key}.cache.gz"
            
            if cache_file_gz.exists():
                file_size = cache_file_gz.stat().st_size
            elif cache_file.exists():
                file_size = cache_file.stat().st_size
            else:
                continue
            
            entry = {
                'key': key,
                'url': meta.get('url', ''),
                'timestamp': meta.get('timestamp', ''),
                'size': meta.get('size', 0),
                'compressed_size': file_size,
                'compressed': meta.get('compressed', False),
                'tags': meta.get('tags', []),
                'access_count': meta.get('access_count', 0),
                'last_accessed': meta.get('last_accessed', meta.get('timestamp', ''))
            }
            
            entries.append(entry)
            total_size += file_size
            total_original_size += entry['size']
            access_count += entry['access_count']
            
        except Exception:
            continue
    
    compression_ratio = (1 - total_size / total_original_size) * 100 if total_original_size > 0 else 0
    
    return {
        'count': len(entries),
        'size_bytes': total_size,
        'size_mb': round(total_size / (1024 * 1024), 2),
        'original_size_mb': round(total_original_size / (1024 * 1024), 2),
        'compression_ratio': round(compression_ratio, 1),
        'total_accesses': access_count,
        'avg_accesses': round(access_count / len(entries), 1) if entries else 0,
        'path': str(cache_dir),
        'entries': entries
    }


def get_cache_entries_sorted(sort_by: str = 'last_accessed') -> List[Dict]:
    """Get cache entries sorted by specified criteria"""
    stats = get_detailed_cache_stats()
    entries = stats['entries']
    
    if sort_by == 'last_accessed':
        entries.sort(key=lambda x: x.get('last_accessed', ''))
    elif sort_by == 'size':
        entries.sort(key=lambda x: x.get('size', 0), reverse=True)
    elif sort_by == 'access_count':
        entries.sort(key=lambda x: x.get('access_count', 0), reverse=True)
    elif sort_by == 'timestamp':
        entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return entries


def remove_cache_entry(key: str):
    """Remove a specific cache entry"""
    cache_dir = get_cache_dir()
    cache_file = cache_dir / f"{key}.cache"
    cache_file_gz = cache_dir / f"{key}.cache.gz"
    meta_file = cache_dir / f"{key}.meta"
    
    cache_file.unlink(missing_ok=True)
    cache_file_gz.unlink(missing_ok=True)
    meta_file.unlink(missing_ok=True)


def cache_warm(urls: List[str], tags: List[str] = None):
    """
    Warm up cache with specified URLs (for favorites/popular content)
    
    Args:
        urls: List of URLs to cache
        tags: Tags to mark these cached entries
    """
    from ap_core.browser import get_request_session, driver_output
    
    session = get_request_session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
        'Accept': 'application/json'
    }
    
    warmed = 0
    failed = 0
    
    for url in urls:
        try:
            if not cache_get(url, max_age_hours=1):  # Check if already cached
                # Try direct HTTP first
                response = session.get(url, headers=headers, timeout=15)
                if response.status_code == 200 and response.content:
                    cache_set(url, response.content, tags=tags)
                    print(f"✓ Cached: {url}")
                    warmed += 1
                else:
                    # Fallback to Playwright for failed requests
                    print(f"⚠ HTTP failed for {url}, trying browser fallback...")
                    content = driver_output(url, driver=True, content=True, wait_time=5)
                    if content:
                        cache_set(url, content.encode(), tags=tags)
                        print(f"✓ Cached via browser: {url}")
                        warmed += 1
                    else:
                        print(f"✗ Failed to cache {url}: All methods failed")
                        failed += 1
            else:
                print(f"⚡ Already cached: {url}")
        except Exception as e:
            print(f"✗ Failed to cache {url}: {e}")
            failed += 1
    
    print(f"\n🔥 Cache warming complete: {warmed} cached, {failed} failed")


def export_cache(export_path: str, include_content: bool = False):
    """
    Export cache metadata and optionally content to a file
    
    Args:
        export_path: Path to export file
        include_content: Whether to include actual cached content
    """
    stats = get_detailed_cache_stats()
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'stats': {k: v for k, v in stats.items() if k != 'entries'},
        'entries': []
    }
    
    for entry in stats['entries']:
        entry_data = {k: v for k, v in entry.items() if k != 'key'}
        if include_content:
            try:
                content = cache_get(entry['url'])
                if content:
                    entry_data['content'] = content.hex()  # Store as hex
            except Exception:
                pass
        export_data['entries'].append(entry_data)
    
    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✓ Exported {len(export_data['entries'])} cache entries to {export_path}")


def import_cache(import_path: str, overwrite: bool = False):
    """
    Import cache from an export file
    
    Args:
        import_path: Path to import file
        overwrite: Whether to overwrite existing cache entries
    """
    with open(import_path, 'r') as f:
        import_data = json.load(f)
    
    imported = 0
    for entry in import_data['entries']:
        try:
            if not overwrite and cache_get(entry['url'], max_age_hours=1):
                continue  # Skip if already exists
            
            if 'content' in entry:
                content = bytes.fromhex(entry['content'])
                cache_set(entry['url'], content, tags=entry.get('tags'))
                imported += 1
        except Exception as e:
            print(f"✗ Failed to import {entry.get('url', 'unknown')}: {e}")
    
    print(f"✓ Imported {imported} cache entries from {import_path}")


def display_cache_stats():
    """Display formatted cache statistics"""
    stats = get_detailed_cache_stats()
    
    print(f"\n📊 Cache Statistics:")
    print(f"   Entries: {stats['count']}")
    print(f"   Size: {stats['size_mb']} MB")
    if stats['original_size_mb'] > 0:
        print(f"   Original Size: {stats['original_size_mb']} MB")
        print(f"   Compression: {stats['compression_ratio']}% saved")
    print(f"   Total Accesses: {stats['total_accesses']}")
    print(f"   Avg Accesses: {stats['avg_accesses']}")
    print(f"   Location: {stats['path']}")
    
    # Show top entries by access count
    if stats['entries']:
        top_entries = sorted(stats['entries'], key=lambda x: x.get('access_count', 0), reverse=True)[:5]
        print(f"\n🔥 Most Accessed:")
        for i, entry in enumerate(top_entries, 1):
            url = entry.get('url', '')[:60] + '...' if len(entry.get('url', '')) > 60 else entry.get('url', '')
            print(f"   {i}. {url} ({entry.get('access_count', 0)} times)")


def get_cache_stats():
    """Legacy function for backward compatibility"""
    stats = get_detailed_cache_stats()
    return {
        'count': stats['count'],
        'size_bytes': stats['size_bytes'],
        'size_mb': stats['size_mb'],
        'path': stats['path']
    }
