import os
import sys
import time
import logging
import tempfile
import requests
import shutil
from functools import lru_cache

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService

from ap_core.parser import parse_mailfunction_api
from ap_core.cookies import load_cookies, save_cookies

# Cross-platform driver detection
def _find_driver(driver_name):
    """Find driver executable in system PATH or common locations"""
    # Try to find in PATH first
    driver_path = shutil.which(driver_name)
    if driver_path:
        return driver_path
    
    # Platform-specific common locations
    platform = sys.platform.lower()
    common_paths = []
    
    if platform == 'linux':
        common_paths = [
            f'/snap/bin/{driver_name}',
            f'/usr/local/bin/{driver_name}',
            f'/usr/bin/{driver_name}',
            f'~/.local/bin/{driver_name}',
        ]
    elif platform == 'darwin':  # macOS
        common_paths = [
            f'/usr/local/bin/{driver_name}',
            f'/opt/homebrew/bin/{driver_name}',
            f'~/bin/{driver_name}',
        ]
    elif platform == 'win32':  # Windows
        if not driver_name.endswith('.exe'):
            driver_name += '.exe'
        common_paths = [
            f'C:\\Program Files\\{driver_name}',
            f'C:\\Windows\\System32\\{driver_name}',
            f'{os.environ.get("USERPROFILE", "")}\\AppData\\Local\\Programs\\{driver_name}',
        ]
    
    # Check common locations
    for path in common_paths:
        expanded = os.path.expanduser(path)
        if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
            return expanded
    
    # Return None if not found (Selenium will try to find it)
    return None

# Try to locate drivers
GECKO_PATH = _find_driver('geckodriver')
CHROME_PATH = _find_driver('chromedriver')


def make_firefox_driver():
    """
    Return a headless Firefox WebDriver with an isolated profile & unique port.
    Keeps the proven-stable config to preserve DDoS-Guard bypass behavior.
    Cross-platform compatible.
    """
    opts = webdriver.FirefoxOptions()
    opts.add_argument("--headless")

    # Isolated clean profile
    profile_dir = tempfile.mkdtemp(prefix="fw_profile_")
    opts.profile = profile_dir

    # Create service with driver path if found, otherwise let Selenium find it
    if GECKO_PATH:
        service = FirefoxService(executable_path=GECKO_PATH)
        return webdriver.Firefox(service=service, options=opts)
    else:
        # Let Selenium/webdriver-manager handle it
        try:
            return webdriver.Firefox(options=opts)
        except Exception as e:
            logging.error(f"Firefox driver not found. Please install geckodriver: {e}")
            logging.info("Install guide: https://github.com/mozilla/geckodriver/releases")
            raise


def browser(choice: str = "firefox"):
    """Cross-platform browser initialization"""
    chrome_guess = ["chrome", "Chrome", "google chrome", "google"]
    ff_guess = ["ff", "firefox", "ffgui", "ffox", "fire"]

    if choice.lower() in chrome_guess:
        logging.info("Launching Chrome")
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless")
        
        if CHROME_PATH:
            service = ChromeService(executable_path=CHROME_PATH)
            return webdriver.Chrome(service=service, options=opts)
        else:
            try:
                return webdriver.Chrome(options=opts)
            except Exception as e:
                logging.error(f"Chrome driver not found. Please install chromedriver: {e}")
                logging.info("Install guide: https://chromedriver.chromium.org/downloads")
                raise

    if choice.lower() in ff_guess or not choice:
        logging.info("Launching optimized headless Firefox")
        return make_firefox_driver()

    logging.error("Unsupported browser choice")
    raise ValueError(f"Unsupported browser: {choice}")


# Request session with connection pooling (shared)
_request_session = None

def get_request_session():
    global _request_session
    if _request_session is None:
        _request_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False,
        )
        _request_session.mount('http://', adapter)
        _request_session.mount('https://', adapter)
    return _request_session


@lru_cache(maxsize=100)
def cached_request(url):
    session = get_request_session()
    try:
        response = session.get(url, timeout=10)
        return response.content
    except Exception:
        return None


def driver_output(url: str, driver=False, content=False, json=False, wait_time=10):
    if not driver:
        logging.error("Invalid arguments provided to driver_output function.")
        print("Use the 'content' argument to get page content or 'json' argument to get JSON response.")
        return None

    driver_instance = None
    try:
        driver_instance = browser("firefox")
        driver_instance.get(url)
        
        # Try to load persistent cookies for DDoS-Guard
        load_cookies(driver_instance)

        # Critical for DDoS-Guard bypass: refresh then implicit wait
        driver_instance.refresh()
        driver_instance.implicitly_wait(wait_time)
        
        # Save cookies for future use
        save_cookies(driver_instance)

        if content:
            page_source = driver_instance.page_source
            driver_instance.quit()
            return page_source

        if json:
            json_data = driver_instance.execute_script("return document.body.innerText;")
            driver_instance.quit()
            dict_data = parse_mailfunction_api(json_data)
            if dict_data is None:
                raise ValueError("Failed to parse malformed JSON.")
            return dict_data

    except Exception as e:
        logging.error(f"Selenium failed to load the page: {e}")
        if driver_instance:
            try:
                driver_instance.quit()
            except Exception:
                pass
        return None


# No-op for now; kept for API compatibility
_defunct_pool = []

def cleanup_browsers():
    for d in list(_defunct_pool):
        try:
            d.quit()
        except Exception:
            pass
    _defunct_pool.clear()
