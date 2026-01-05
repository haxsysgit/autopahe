import os
import logging
import requests
import json as jsonlib
import subprocess
import sys
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

def install_playwright_browsers():
    """Install Playwright browsers automatically."""
    # Check if auto-install is disabled
    if os.environ.get("AUTOPAHE_SKIP_AUTO_INSTALL", "").lower() in ("1", "true", "yes"):
        print("⚠️  Auto-install disabled via AUTOPAHE_SKIP_AUTO_INSTALL")
        return False
        
    print("🔧 Playwright browsers not found. Installing automatically...")
    print("This may take a few minutes on first run...")
    
    try:
        # Check available disk space (need ~500MB for browsers)
        try:
            home_dir = Path.home()
            if hasattr(os, 'statvfs'):  # Unix-like systems
                stat = os.statvfs(home_dir)
                free_space_mb = (stat.f_bavail * stat.f_frsize) // (1024 * 1024)
            else:  # Windows
                import shutil
                free_space_mb = shutil.disk_usage(home_dir).free // (1024 * 1024)
            
            if free_space_mb < 500:
                print(f"❌ Insufficient disk space: {free_space_mb}MB available, need ~500MB")
                return False
        except Exception as space_error:
            # If we can't check disk space, continue anyway and let the install fail if needed
            logging.warning(f"Could not check disk space: {space_error}")
            
        # Try to install browsers using the same Python executable
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "--with-deps"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully!")
            return True
        else:
            error_msg = result.stderr.lower()
            if "permission" in error_msg or "access denied" in error_msg:
                print("❌ Permission denied during installation.")
                print("   Try running with appropriate privileges or check install directory permissions.")
            elif "network" in error_msg or "connection" in error_msg:
                print("❌ Network connection failed during installation.")
                print("   Check your internet connection and try again.")
            else:
                print(f"❌ Failed to install Playwright browsers: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out. Please run 'playwright install' manually.")
        return False
    except PermissionError:
        print("❌ Permission denied during installation.")
        print("   Try running with appropriate privileges or check install directory permissions.")
        return False
    except Exception as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        return False


def _run_interactive_setup():
    """Run setup interactively when browsers are missing on first run."""
    print("🔧 Installing Playwright browser engine...")
    print("Note: Playwright installs its own Chromium engine for automation")
    print("No existing browsers required - this is a standalone engine (~170MB)")
    print("This may take a few minutes...")
    print()
    
    try:
        # Install Chromium engine (smallest, most universal for automation)
        print("Installing Playwright's Chromium engine...")
        os.environ['AUTOPAHE_BROWSER'] = 'chromium'
        result = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chromium'],
            capture_output=False,
            timeout=300
        )
        
        if result.returncode == 0:
            print("\n✅ Chromium browser engine installed successfully!")
            return True
        
        # If Chromium fails, offer user choice
        print("\n❌ Could not install Chromium automatically.")
        print("Please choose a browser to install manually:")
        print("  firefox    - Install Firefox browser engine")
        print("  webkit     - Install WebKit browser engine (Safari)")
        print("  chrome     - Install Chrome browser engine")
        print("  chromium   - Install Chromium browser engine")
        print()
        print("Run one of these commands:")
        print("  playwright install firefox")
        print("  playwright install webkit")
        print("  playwright install chrome")
        print("  playwright install chromium")
        print()
        print("Then set AUTOPAHE_BROWSER environment variable:")
        print("  export AUTOPAHE_BROWSER=firefox  # Linux/Mac")
        print("  set AUTOPAHE_BROWSER=firefox     # Windows")
        print()
        print("Or use --browser flag: autopahe --browser firefox")
        
        return False
        
    except subprocess.TimeoutExpired:
        print("\n❌ Installation timed out.")
        return False
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        return False


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
            print("❌ Playwright not found. Please install dependencies first:")
            print("   Option 1: uv sync && uv run playwright install")
            print("   Option 2: pip install -r requirements.txt && playwright install")
            print("   Option 3: Run 'autopahe --setup' for automatic setup")
            return None
        
        _pw = sync_playwright().start()
        choice = (browser_choice or os.environ.get("AUTOPAHE_BROWSER") or "chrome").lower()
        # Normalize edge alias
        if choice == "edge":
            choice = "msedge"
        # Use platform-appropriate cache directory for browser data
        try:
            from ap_core.platform_paths import get_cache_dir
            user_data_dir = str(get_cache_dir() / "playwright" / choice)
        except ImportError:
            user_data_dir = str(Path.home() / ".cache" / "autopahe-pw" / choice)
        
        try:
            if choice == "firefox":
                _pw_context = _pw.firefox.launch_persistent_context(user_data_dir, headless=headless)
            elif choice == "chrome":
                try:
                    _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, channel="chrome", headless=headless)
                except Exception:
                    _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
            elif choice == "msedge":
                try:
                    _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, channel="msedge", headless=headless)
                except Exception:
                    _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
            else:
                _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
            return _pw_context
            
        except Exception as e:
            # Check if this is a missing browser executable error
            error_str = str(e).lower()
            if "executable doesn't exist" in error_str or "playwright install" in error_str:
                print("\n" + "="*60)
                print("🔍 SETUP REQUIRED: Playwright browsers not installed")
                print("="*60)
                
                # Check if running interactively
                import sys
                if sys.stdin.isatty():
                    # Interactive mode - prompt user
                    print("Browser engines (~500MB) are required for AutoPahe to work.")
                    print()
                    try:
                        response = input("Would you like to install them now? [Y/n]: ").strip().lower()
                        if response in ('', 'y', 'yes'):
                            print()
                            # Run setup
                            if _run_interactive_setup():
                                print("\n🔄 Retrying browser launch...")
                                # Retry the browser launch
                                try:
                                    if choice == "firefox":
                                        _pw_context = _pw.firefox.launch_persistent_context(user_data_dir, headless=headless)
                                    elif choice == "chrome":
                                        try:
                                            _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, channel="chrome", headless=headless)
                                        except Exception:
                                            _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
                                    elif choice == "msedge":
                                        try:
                                            _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, channel="msedge", headless=headless)
                                        except Exception:
                                            _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
                                    else:
                                        _pw_context = _pw.chromium.launch_persistent_context(user_data_dir, headless=headless)
                                    print("✅ Browser launched successfully!")
                                    return _pw_context
                                except Exception as retry_error:
                                    print(f"❌ Browser still failed after setup: {retry_error}")
                                    return None
                            else:
                                print("❌ Setup failed. Please try running: autopahe --setup")
                                return None
                        else:
                            print("\nYou can run setup later with: autopahe --setup")
                            return None
                    except (EOFError, KeyboardInterrupt):
                        print("\n\nSetup cancelled. Run 'autopahe --setup' when ready.")
                        return None
                else:
                    # Non-interactive mode - show instructions
                    print("Please run the setup command to install required browsers:")
                    print()
                    print("   autopahe --setup")
                    print()
                    print("This will install all dependencies and browser engines.")
                    print("After setup completes, run autopahe again.")
                    print("="*60)
                    return None
            else:
                # Different type of error
                logging.error(f"Failed to start Playwright context: {e}")
                print(f"❌ Browser error: {e}")
                return None
                
    except Exception as e:
        logging.error(f"Unexpected error in Playwright setup: {e}")
        print(f"❌ Setup error: {e}")
        return None


def print_manual_instructions():
    """Print manual setup instructions when auto-install fails."""
    print("\n📋 MANUAL SETUP INSTRUCTIONS:")
    print("-" * 40)
    print("Please run one of these commands in your terminal:")
    print()
    print("🔹 Option 1 - Using UV (recommended):")
    print("   uv sync")
    print("   uv run playwright install")
    print()
    print("🔹 Option 2 - Using pip:")
    print("   pip install -r requirements.txt")
    print("   playwright install")
    print()
    print("🔹 Option 3 - Direct playwright install:")
    print("   python -m playwright install")
    print()
    print("💡 TIPS:")
    print("   • If you're in a restricted environment, set AUTOPAHE_SKIP_AUTO_INSTALL=1")
    print("   • Installation requires ~500MB disk space and internet connection")
    print("   • Use --with-deps flag if system dependencies are missing")
    print()
    print("After installation, run autopahe again.")
    print("-" * 40)


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
