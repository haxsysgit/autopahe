import os
import logging
import requests
import json as jsonlib
from pathlib import Path
 
from ap_core.parser import parse_mailfunction_api

 


# Request session with connection pooling (shared)
_request_session = None

def get_request_session():
    """Return a shared requests.Session with connection pooling."""
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


 


_pw = None
_pw_context = None
_driver_cache = {}

def get_pw_context(browser_choice: str = None, headless: bool = True):
    """Return a shared Playwright persistent context (single OS window).

    Creates it on first use and reuses it afterwards so repeated calls do not
    spawn multiple browser windows. Browser is selected via AUTOPAHE_BROWSER
    or the provided browser_choice.
    """
    global _pw, _pw_context
    if _pw_context is not None:
        return _pw_context
    try:
        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError:
            logging.error("Playwright is not installed in this environment. Run: 'uv sync' then 'uv run playwright install' or invoke the app with 'uv run autopahe ...'.")
            return None
        _pw = sync_playwright().start()
        choice = (browser_choice or os.environ.get("AUTOPAHE_BROWSER") or "chrome").lower()
        user_data_dir = str(Path.home() / ".cache" / "autopahe-pw" / choice)
        if choice == "firefox":
            _pw_context = _pw.firefox.launch_persistent_context(user_data_dir, headless=headless)
        elif choice == "chrome":
            try:
                _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, channel="chrome", headless=headless)
            except Exception:
                _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
        else:
            _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
        return _pw_context
    except Exception as e:
        logging.error(f"Failed to start Playwright context: {e}")
        return None


def close_pw_context():
    """Close the shared Playwright context and stop Playwright."""
    global _pw, _pw_context
    try:
        if _pw_context is not None:
            _pw_context.close()
    except Exception:
        pass
    finally:
        _pw_context = None
    try:
        if _pw is not None:
            _pw.stop()
    except Exception:
        pass
    finally:
        _pw = None


def driver_output(url: str, driver=False, content=False, json=False, wait_time=5):
    """Fetch content using Playwright.

    Args:
        url: Target URL to fetch.
        driver: Set True to enable browser fetch (kept for API compatibility).
        content: If True, return full HTML.
        json: If True, return parsed JSON (or fallback parse).
        wait_time: Seconds to wait after initial load.

    Uses the AUTOPAHE_BROWSER env var to choose 'chrome' (default), 'chromium', or 'firefox'.
    """
    if not driver:
        logging.error("Invalid arguments provided to driver_output function.")
        print("Use the 'content' argument to get page content or 'json' argument to get JSON response.")
        return None

    try:
        # In-process cache by URL
        key = (url, 'content' if content else 'json' if json else 'text')
        if key in _driver_cache:
            return _driver_cache[key]
        browser_choice = (os.environ.get("AUTOPAHE_BROWSER") or "chrome").lower()
        headless = True
        context = get_pw_context(browser_choice, headless=headless)
        if context is None:
            return None
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(int(wait_time or 10) * 1000)

        if content:
            html = page.content()
            page.close()
            _driver_cache[key] = html
            return html

        if json:
            body_text = page.evaluate("document.body.innerText")
            page.close()
            try:
                parsed = jsonlib.loads(body_text)
            except Exception:
                parsed = parse_mailfunction_api(body_text)
            _driver_cache[key] = parsed
            return parsed

    except Exception as e:
        logging.error(f"Playwright failed to load the page: {e}")
        return None


def cleanup_browsers():
    close_pw_context()


def batch_driver_output(urls, content=False, json=False, wait_time=5):
    """Fetch multiple URLs using a single Playwright context.

    Args:
        urls: Iterable of URL strings to fetch.
        content: If True, return HTML content per URL.
        json: If True, return parsed JSON per URL.
        wait_time: Seconds to wait after initial load per URL.

    Returns:
        dict mapping url -> result (str for content, dict for json). Missing entries map to None.
    """
    results = {}
    browser_choice = (os.environ.get("AUTOPAHE_BROWSER") or "chrome").lower()
    context = get_pw_context(browser_choice, headless=True)
    if context is None:
        for u in urls:
            results[u] = None
        return results
    for u in urls:
        try:
            key = (u, 'content' if content else 'json' if json else 'text')
            if key in _driver_cache:
                results[u] = _driver_cache[key]
                continue
            page = context.new_page()
            page.goto(u, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(int(wait_time or 10) * 1000)
            if content:
                html = page.content()
                page.close()
                _driver_cache[key] = html
                results[u] = html
            elif json:
                body_text = page.evaluate("document.body.innerText")
                page.close()
                try:
                    parsed = jsonlib.loads(body_text)
                except Exception:
                    parsed = parse_mailfunction_api(body_text)
                _driver_cache[key] = parsed
                results[u] = parsed
            else:
                text = page.evaluate("document.body.innerText")
                page.close()
                _driver_cache[key] = text
                results[u] = text
        except Exception:
            results[u] = None
    return results
