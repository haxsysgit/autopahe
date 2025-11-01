"""
Persistent cookies jar to reduce DDoS-Guard friction between runs
"""
import os
import pickle
from pathlib import Path
from datetime import datetime, timedelta


def get_cookies_path():
    """Get cookies file path"""
    home = Path.home()
    cache_dir = home / ".cache" / "autopahe"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "cookies.pkl"


def save_cookies(driver):
    """
    Save browser cookies to disk
    
    Args:
        driver: Selenium WebDriver instance
    """
    try:
        cookies = driver.get_cookies()
        cookies_path = get_cookies_path()
        
        # Add timestamp
        data = {
            'timestamp': datetime.now().isoformat(),
            'cookies': cookies
        }
        
        with open(cookies_path, 'wb') as f:
            pickle.dump(data, f)
    except Exception:
        # Fail silently
        pass


def load_cookies(driver, max_age_hours: int = 24):
    """
    Load saved cookies into browser
    
    Args:
        driver: Selenium WebDriver instance
        max_age_hours: Maximum age of cookies in hours
    
    Returns:
        True if cookies loaded, False otherwise
    """
    try:
        cookies_path = get_cookies_path()
        if not cookies_path.exists():
            return False
        
        with open(cookies_path, 'rb') as f:
            data = pickle.load(f)
        
        # Check age
        saved_time = datetime.fromisoformat(data['timestamp'])
        age = datetime.now() - saved_time
        
        if age > timedelta(hours=max_age_hours):
            # Expired
            cookies_path.unlink(missing_ok=True)
            return False
        
        # Load cookies
        for cookie in data['cookies']:
            try:
                driver.add_cookie(cookie)
            except Exception:
                # Skip invalid cookies
                continue
        
        return True
    except Exception:
        return False


def clear_cookies():
    """Clear saved cookies"""
    try:
        cookies_path = get_cookies_path()
        cookies_path.unlink(missing_ok=True)
    except Exception:
        pass
