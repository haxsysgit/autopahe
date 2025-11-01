import os
import time
import logging
import tempfile
import requests
from functools import lru_cache

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService

from ap_core.parser import parse_mailfunction_api

# Driver paths (defaults)
GECKO_PATH = "/snap/bin/geckodriver"
CHROME_PATH = "/snap/bin/chromedriver"


def make_firefox_driver():
    """
    Return a headless Firefox WebDriver with an isolated profile & unique port.
    Keeps the proven-stable config to preserve DDoS-Guard bypass behavior.
    """
    opts = webdriver.FirefoxOptions()
    opts.add_argument("--headless")

    # Isolated clean profile
    profile_dir = tempfile.mkdtemp(prefix="fw_profile_")
    opts.profile = profile_dir

    service = FirefoxService(executable_path=GECKO_PATH)
    return webdriver.Firefox(service=service, options=opts)


def browser(choice: str = "firefox"):
    chrome_guess = ["chrome", "Chrome", "google chrome", "google"]
    ff_guess = ["ff", "firefox", "ffgui", "ffox", "fire"]

    if choice.lower() in chrome_guess:
        logging.info("Launching Chrome")
        service = ChromeService(executable_path=CHROME_PATH)
        return webdriver.Chrome(service=service)

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

        # Critical for DDoS-Guard bypass: refresh then implicit wait
        driver_instance.refresh()
        driver_instance.implicitly_wait(wait_time)

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
