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


def _run_playwright_install(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "playwright", "install", *args],
        capture_output=True,
        text=True,
        timeout=300,
    )


def install_playwright_browser(browser: str = "chromium") -> bool:
    """Install a Playwright browser engine in the active Python environment."""
    if os.environ.get("AUTOPAHE_SKIP_AUTO_INSTALL", "").lower() in ("1", "true", "yes"):
        print("⚠️  Auto-install disabled via AUTOPAHE_SKIP_AUTO_INSTALL")
        return False

    browser = (browser or "chromium").lower()
    if browser in {"chrome", "msedge", "edge"}:
        print(f"Using bundled Chromium for setup instead of external browser channel: {browser}")
        browser = "chromium"
    elif browser not in {"chromium", "firefox", "webkit"}:
        print(f"Unknown browser '{browser}', using Chromium.")
        browser = "chromium"

    print(f"🔧 Installing Playwright {browser} browser engine...")

    try:
        result = _run_playwright_install([browser])
        if result.returncode == 0:
            print(f"✅ Playwright {browser} browser engine installed successfully.")
            return True

        print(result.stderr.strip() or result.stdout.strip())
        if sys.platform.startswith("linux"):
            print("\nBrowser engine install failed. If the error mentions missing system libraries, run:")
            print(f"   {sys.executable} -m playwright install-deps {browser}")
            print(f"   {sys.executable} -m playwright install {browser}")
        else:
            print("\nManual fallback:")
            print(f"   {sys.executable} -m playwright install {browser}")
        return False

    except subprocess.TimeoutExpired:
        print("❌ Playwright browser installation timed out.")
        return False
    except Exception as exc:
        print(f"❌ Playwright browser installation failed: {exc}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers automatically."""
    return install_playwright_browser("chromium")


def open_verification_session(url: str, browser_choice: str = None) -> bool:
    """Open a headed persistent browser session so the user can complete site verification."""
    if not url:
        url = "https://kwik.cx"
    if "://" not in url:
        url = f"https://{url}"

    browser = (browser_choice or os.environ.get("AUTOPAHE_BROWSER") or "chromium").lower()
    print("Opening AutoPahe's persistent browser profile.")
    print("Complete any verification in the browser window, then return here.")
    print(f"URL: {url}")

    close_pw_context()
    context = get_pw_context(browser, headless=False)
    if context is None:
        return False

    page = None
    try:
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if sys.stdin.isatty():
            input("Press Enter after verification is complete...")
        else:
            print("Non-interactive terminal detected; keeping the browser open for 60 seconds.")
            page.wait_for_timeout(60000)
        print("Verification session saved to the persistent browser profile.")
        return True
    except Exception as exc:
        print(f"Verification session failed: {exc}")
        return False
    finally:
        try:
            if page is not None:
                page.close()
        except Exception:
            pass
        close_pw_context()


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
        if install_playwright_browser("chromium"):
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
        choice = (browser_choice or os.environ.get("AUTOPAHE_BROWSER") or "chromium").lower()
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
                            close_pw_context()
                            return None
                    except (EOFError, KeyboardInterrupt):
                        print("\n\nSetup cancelled. Run 'autopahe --setup' when ready.")
                        close_pw_context()
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
                    close_pw_context()
                    return None
            else:
                # Different type of error
                logging.error(f"Failed to start Playwright context: {e}")
                print(f"❌ Browser error: {e}")
                close_pw_context()
                return None
                
    except Exception as e:
        logging.error(f"Unexpected error in Playwright setup: {e}")
        print(f"❌ Setup error: {e}")
        close_pw_context()
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

    Uses the AUTOPAHE_BROWSER env var to choose 'chromium' (default), 'chrome', or 'firefox'.
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
        browser_choice = (os.environ.get("AUTOPAHE_BROWSER") or "chromium").lower()
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
    browser_choice = (os.environ.get("AUTOPAHE_BROWSER") or "chromium").lower()
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
