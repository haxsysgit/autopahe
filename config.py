"""
Centralized configuration for AutoPahe data directories and paths.
Provides a unified way to manage all project data locations.
Cross-platform support for Windows, macOS, and Linux.
"""

import os
from pathlib import Path
from typing import Optional

from ap_core.platform_paths import (
    get_data_dir,
    get_config_dir,
    get_cache_dir,
    get_log_dir,
    is_windows,
)

def _get_data_dir() -> Path:
    """Get the appropriate data directory based on environment and platform."""
    if os.getenv('AUTO_PAHE_PORTABLE'):
        # Portable mode: use home directory
        return Path.home() / 'autopahe_data'
    elif os.getenv('AUTO_PAHE_DEV'):
        # Development mode: use local data directory
        return Path(__file__).parent / 'data'
    else:
        # Standard installation: use platform-appropriate location
        return get_data_dir()

# Base data directory - centralized location for all project data
DATA_DIR = _get_data_dir()

# Data subdirectories
RECORDS_DIR = DATA_DIR / 'records'
LOGS_DIR = get_log_dir() if not os.getenv('AUTO_PAHE_PORTABLE') else DATA_DIR / 'logs'
CACHE_DIR = get_cache_dir() if not os.getenv('AUTO_PAHE_PORTABLE') else DATA_DIR / 'cache'
COLLECTION_DIR = DATA_DIR / 'collection'
BACKUPS_DIR = DATA_DIR / 'backups'

# File paths
DATABASE_FILE = RECORDS_DIR / 'animerecord.json'
COLLECTION_METADATA_FILE = COLLECTION_DIR / 'collection.json'
LOG_FILE = LOGS_DIR / 'autopahe.log'
BACKUP_DATABASE_FILE = BACKUPS_DIR / 'animerecord_backup.json'

# Legacy paths for migration (check multiple locations)
LEGACY_DATABASE_FILE = Path(__file__).parent / 'json_data' / 'animerecord.json'
LEGACY_ROOT_DATABASE = Path(__file__).parent / 'animerecord.json'

# Platform-specific legacy collection paths
if is_windows():
    _legacy_cache_base = Path.home() / 'AppData' / 'Local' / 'autopahe'
else:
    _legacy_cache_base = Path.home() / '.cache' / 'autopahe'
LEGACY_COLLECTION_DIR = _legacy_cache_base / 'collection'

def ensure_data_directories():
    """Create all data directories if they don't exist."""
    for directory in [DATA_DIR, RECORDS_DIR, LOGS_DIR, CACHE_DIR, COLLECTION_DIR, BACKUPS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def migrate_legacy_data():
    """
    Migrate data from legacy locations to new centralized structure.
    Only moves data if it exists and target location is empty.
    """
    import shutil
    import json
    from datetime import datetime
    
    print("🔄 Checking for legacy data migration...")
    
    # Migrate root animerecord.json if it exists and we haven't already migrated
    if LEGACY_ROOT_DATABASE.exists() and not DATABASE_FILE.exists():
        print(f"Migrating legacy database from {LEGACY_ROOT_DATABASE}")
        shutil.copy2(LEGACY_ROOT_DATABASE, DATABASE_FILE)
        
        # Create backup of original
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUPS_DIR / f'animerecord_root_backup_{timestamp}.json'
        shutil.copy2(LEGACY_ROOT_DATABASE, backup_path)
        print(f"Created backup: {backup_path}")
    
    # Migrate collection data from ~/.cache/autopahe/collection
    if LEGACY_COLLECTION_DIR.exists() and not any(COLLECTION_DIR.iterdir()):
        print(f"Migrating collection data from {LEGACY_COLLECTION_DIR}")
        
        # Copy collection.json if it exists
        legacy_collection_file = LEGACY_COLLECTION_DIR / 'collection.json'
        if legacy_collection_file.exists():
            shutil.copy2(legacy_collection_file, COLLECTION_METADATA_FILE)
            print(f"Migrated collection metadata")
        
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUPS_DIR / f'collection_backup_{timestamp}.json'
        if legacy_collection_file.exists():
            shutil.copy2(legacy_collection_file, backup_path)
            print(f"Created collection backup: {backup_path}")
    
    # Check if migration was successful
    if DATABASE_FILE.exists():
        print(f"✅ Database ready: {DATABASE_FILE}")
        with open(DATABASE_FILE, 'r') as f:
            data = json.load(f)
            print(f"   Contains {len(data)} anime records")
    
    if COLLECTION_METADATA_FILE.exists():
        print(f"✅ Collection metadata ready: {COLLECTION_METADATA_FILE}")

def get_project_info():
    """Get information about the current project setup."""
    return {
        'data_dir': str(DATA_DIR),
        'database_file': str(DATABASE_FILE),
        'collection_file': str(COLLECTION_METADATA_FILE),
        'log_file': str(LOG_FILE),
        'portable_mode': bool(os.getenv('AUTO_PAHE_PORTABLE')),
        'directories_created': [str(d) for d in [DATA_DIR, RECORDS_DIR, LOGS_DIR, CACHE_DIR, COLLECTION_DIR, BACKUPS_DIR]]
    }

# Initialize data directories on import
ensure_data_directories()

# Auto-migrate legacy data if needed (only once)
MIGRATION_FLAG = DATA_DIR / '.migrated'
if not MIGRATION_FLAG.exists():
    migrate_legacy_data()
    MIGRATION_FLAG.touch()  # Create flag to prevent re-migration
