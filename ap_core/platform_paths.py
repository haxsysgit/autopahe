"""
Cross-platform path utilities for Windows/macOS/Linux compatibility.
Provides consistent directory locations across all operating systems.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_platform() -> str:
    """Get normalized platform name."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def get_config_dir(app_name: str = "autopahe") -> Path:
    """
    Get platform-appropriate configuration directory.
    
    - Windows: %APPDATA%/autopahe
    - macOS: ~/Library/Application Support/autopahe
    - Linux: ~/.config/autopahe
    
    Args:
        app_name: Application name for the config folder
        
    Returns:
        Path to configuration directory
    """
    platform = get_platform()
    
    if platform == "windows":
        # Use APPDATA on Windows
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / app_name
        # Fallback to user profile
        return Path.home() / "AppData" / "Roaming" / app_name
    
    elif platform == "macos":
        return Path.home() / "Library" / "Application Support" / app_name
    
    else:  # Linux and others
        # Respect XDG_CONFIG_HOME if set
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / app_name
        return Path.home() / ".config" / app_name


def get_cache_dir(app_name: str = "autopahe") -> Path:
    """
    Get platform-appropriate cache directory.
    
    - Windows: %LOCALAPPDATA%/autopahe/cache
    - macOS: ~/Library/Caches/autopahe
    - Linux: ~/.cache/autopahe
    
    Args:
        app_name: Application name for the cache folder
        
    Returns:
        Path to cache directory
    """
    platform = get_platform()
    
    if platform == "windows":
        # Use LOCALAPPDATA on Windows
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / app_name / "cache"
        # Fallback to user profile
        return Path.home() / "AppData" / "Local" / app_name / "cache"
    
    elif platform == "macos":
        return Path.home() / "Library" / "Caches" / app_name
    
    else:  # Linux and others
        # Respect XDG_CACHE_HOME if set
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache) / app_name
        return Path.home() / ".cache" / app_name


def get_data_dir(app_name: str = "autopahe") -> Path:
    """
    Get platform-appropriate data directory.
    
    - Windows: %LOCALAPPDATA%/autopahe/data
    - macOS: ~/Library/Application Support/autopahe
    - Linux: ~/.local/share/autopahe
    
    Args:
        app_name: Application name for the data folder
        
    Returns:
        Path to data directory
    """
    platform = get_platform()
    
    if platform == "windows":
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / app_name / "data"
        return Path.home() / "AppData" / "Local" / app_name / "data"
    
    elif platform == "macos":
        return Path.home() / "Library" / "Application Support" / app_name
    
    else:  # Linux and others
        # Respect XDG_DATA_HOME if set
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / app_name
        return Path.home() / ".local" / "share" / app_name


def get_log_dir(app_name: str = "autopahe") -> Path:
    """
    Get platform-appropriate log directory.
    
    - Windows: %LOCALAPPDATA%/autopahe/logs
    - macOS: ~/Library/Logs/autopahe
    - Linux: ~/.local/share/autopahe/logs
    
    Args:
        app_name: Application name for the log folder
        
    Returns:
        Path to log directory
    """
    platform = get_platform()
    
    if platform == "windows":
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / app_name / "logs"
        return Path.home() / "AppData" / "Local" / app_name / "logs"
    
    elif platform == "macos":
        return Path.home() / "Library" / "Logs" / app_name
    
    else:  # Linux and others
        return get_data_dir(app_name) / "logs"


def get_downloads_dir() -> Path:
    """
    Get user's Downloads directory.
    
    Returns:
        Path to Downloads directory
    """
    platform = get_platform()
    
    if platform == "windows":
        # Try to get from registry/known folders, fallback to default
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            ) as key:
                downloads = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
                return Path(downloads)
        except Exception:
            pass
        # Fallback to default location
        return Path.home() / "Downloads"
    
    else:
        # macOS and Linux
        return Path.home() / "Downloads"


def ensure_dir(path: Path) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        The same path for chaining
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_legacy_config_locations(app_name: str = "autopahe") -> list:
    """
    Get list of legacy config file locations for migration.
    
    Returns:
        List of possible legacy config paths
    """
    locations = [
        Path.home() / ".config" / app_name / "config.ini",
        Path.home() / f".{app_name}.ini",
        Path.cwd() / f"{app_name}.ini",
    ]
    
    # Add Windows-specific legacy locations
    if get_platform() == "windows":
        locations.extend([
            Path.home() / f"{app_name}.ini",
            Path.home() / "Documents" / f"{app_name}.ini",
        ])
    
    return locations


def sanitize_path(path_str: str) -> Path:
    """
    Sanitize a path string for the current platform.
    Handles both forward and backslashes.
    
    Args:
        path_str: Path string to sanitize
        
    Returns:
        Sanitized Path object
    """
    # Normalize path separators
    normalized = path_str.replace("\\", "/")
    return Path(normalized)


def is_windows() -> bool:
    """Quick check if running on Windows."""
    return sys.platform == "win32"


def is_macos() -> bool:
    """Quick check if running on macOS."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Quick check if running on Linux."""
    return sys.platform.startswith("linux")
