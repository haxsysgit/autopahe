#! /usr/bin/python3
"""AutoPahe - Anime downloader with advanced features"""

# Standard library imports
import os
import sys
import time
import logging
import atexit
import subprocess
from pathlib import Path
import json
import re
from typing import Optional

# Third-party imports
import requests
import typer
from colorama import Fore, Style, init
init()
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

# Get version dynamically from package metadata
try:
    from importlib.metadata import version
    AUTOPAHE_VERSION = version("autopahe")
except (ImportError, Exception):
    AUTOPAHE_VERSION = "dev"  # Development fallback

# Initialize rich console
console = Console()

class LoadingSpinner:
    """Context manager for showing loading spinner during operations"""
    def __init__(self, text="Searching...", spinner_style="dots"):
        self.text = text
        self.spinner_style = spinner_style
        self.spinner = Spinner(spinner_style, text=text)
        self.live = Live(self.spinner, console=console, refresh_per_second=10)
        
    def __enter__(self):
        self.live.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.live.stop()
        
    def update_text(self, text):
        """Update spinner text"""
        self.spinner.text = text

# Local imports - Core functionality
from ap_core.banners import Banners
from ap_core.browser import driver_output, cleanup_browsers, get_request_session, get_pw_context, batch_driver_output
from ap_core.cache import cache_get, cache_set, cache_clear, display_cache_stats, get_cache_stats
from ap_core.fuzzy_search import fuzzy_search_anime, fuzzy_engine
from ap_core.resume_manager import resume_manager
from collection import get_collection_manager, handle_collection_command, WatchStatus
from ap_core.notifications import notify_download_complete, notify_download_failed
# Cookie clearing functionality removed - handled by Playwright context
from ap_core.config import write_sample_config
from state import AutoPaheState

# Local imports - Features
from kwikdown import kwik_download, kwik_stream, detect_available_player, stream_video, _build_safe_filename
from features.manager import (
    process_record,
    load_database,
    print_all_records,
    search_record,
    delete_record,
    update_progress,
    rate_record,
    rename_title,
    set_keyword,
    list_by_status,
    export_records,
    import_records,
)
from features.pahesort import rename_anime, organize_anime


########################################### GLOBAL VARIABLES ######################################

# Default download path (OS-specific)
DOWNLOADS = Path.home() / "Downloads"

########################################### LOGGING ################################################

# Configure logging (level will be adjusted based on CLI args)
# Default to ERROR level to suppress WARNING messages for clean user output
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)

# Runtime state container (Typer ctx.obj is preferred; this is a safe fallback)
_fallback_state = AutoPaheState()


def get_runtime_state(ctx: Optional[typer.Context] = None) -> AutoPaheState:
    """Return CLI runtime state from Typer context or fallback storage."""
    if ctx is not None and isinstance(ctx.obj, AutoPaheState):
        return ctx.obj

    current_ctx = typer.get_current_context(silent=True)
    if current_ctx is not None and isinstance(current_ctx.obj, AutoPaheState):
        return current_ctx.obj

    return _fallback_state

# Cache dictionaries - combined for better memory management
_cache_store = {
    'episodes': {},  # Episode data cache
    'pages': {},     # Prefetched HTML pages
    'anime': {}      # Complete anime data cache
}

# Aliases for backward compatibility
_episode_cache = _cache_store['episodes']
_prefetched_pages = _cache_store['pages']
_anime_cache = _cache_store['anime']

def get_anime_cache_key(session_id):
    """Generate cache key for anime-specific data"""
    return f"anime_complete_{session_id}"


def fetch_episode_page(session_id, page_num=1, use_cache=True):
    """Fetch a specific page of episodes for an anime.
    
    Args:
        session_id: The anime session ID
        page_num: Page number to fetch (1-indexed)
        use_cache: Whether to use cached data if available
        
    Returns:
        dict: Episode data for the requested page
    """
    base_url = f'https://animepahe.com/api?m=release&id={session_id}&sort=episode_asc'
    page_url = f"{base_url}&page={page_num}"
    
    # Check memory cache first
    if use_cache and page_url in _episode_cache:
        logging.debug(f"✓ Loaded page {page_num} from memory cache")
        return _episode_cache[page_url]
    
    # Check disk cache
    if use_cache:
        cached = cache_get(page_url, max_age_hours=24)
        if cached:
            try:
                page_data = json.loads(cached.decode()) if isinstance(cached, bytes) else cached
                _episode_cache[page_url] = page_data
                logging.debug(f"✓ Loaded page {page_num} from disk cache")
                return page_data
            except Exception as e:
                logging.debug(f"Failed to parse cached page data: {e}")
    
    # Fetch the page
    try:
        session = get_request_session()
        response = session.get(page_url, timeout=10)
        if response.status_code == 200:
            page_data = response.json()
            _episode_cache[page_url] = page_data
            cache_set(page_url, json.dumps(page_data).encode())
            logging.debug(f"✓ Fetched page {page_num} via HTTP")
            return page_data
    except Exception as e:
        logging.warning(f"HTTP request failed: {e}")
        # Fall back to Playwright
        page_data = driver_output(page_url, driver=True, json=True, wait_time=5)
        if page_data:
            _episode_cache[page_url] = page_data
            cache_set(page_url, json.dumps(page_data).encode())
            return page_data
    
    return None


def get_episode_session(session_id, episode_num, use_cache=True):
    """Get the session ID for a specific episode number (handles pagination).
    
    This function lazily fetches only the page needed for the requested episode.
    
    Args:
        session_id: The anime session ID
        episode_num: The episode number (1-indexed)
        use_cache: Whether to use cached data
        
    Returns:
        tuple: (episode_session, episode_data) or (None, None) if not found
    """
    # First, get page 1 to understand pagination
    first_page = fetch_episode_page(session_id, page_num=1, use_cache=use_cache)
    if not first_page:
        return None, None
    
    per_page = first_page.get('per_page', 30)
    total = first_page.get('total', 0)
    last_page = first_page.get('last_page', 1)
    
    # Check if episode is within valid range
    if episode_num < 1 or episode_num > total:
        logging.error(f"Episode {episode_num} out of range (1-{total})")
        return None, None
    
    # Calculate which page this episode is on
    # Episodes are sorted ascending, so episode 1-30 on page 1, 31-60 on page 2, etc.
    page_num = ((episode_num - 1) // per_page) + 1
    
    # Calculate index within the page
    index_in_page = (episode_num - 1) % per_page
    
    # Fetch the appropriate page
    if page_num == 1:
        page_data = first_page
    else:
        logging.debug(f"Episode {episode_num} is on page {page_num}, fetching...")
        page_data = fetch_episode_page(session_id, page_num=page_num, use_cache=use_cache)
        if not page_data:
            return None, None
    
    # Get the episode from the page
    episodes = page_data.get('data', [])
    if index_in_page < len(episodes):
        episode = episodes[index_in_page]
        return episode.get('session'), episode
    
    return None, None

def cache_anime_data(session_id, episode_data, play_links_data):
    """Cache complete anime data for instant future access"""
    cache_key = get_anime_cache_key(session_id)
    anime_data = {
        'episode_data': episode_data,
        'play_links': play_links_data,
        'timestamp': time.time()
    }
    _anime_cache[cache_key] = anime_data
    # Also persist to disk cache
    cache_set(cache_key, json.dumps(anime_data).encode())

def get_cached_anime_data(session_id):
    """Get cached anime data if available"""
    cache_key = get_anime_cache_key(session_id)
    
    # Check memory cache first
    if cache_key in _anime_cache:
        return _anime_cache[cache_key]
    
    # Check disk cache
    cached = cache_get(cache_key, max_age_hours=24)
    if cached:
        try:
            anime_data = json.loads(cached.decode())
            _anime_cache[cache_key] = anime_data
            return anime_data
        except Exception:
            pass
    
    return None

############################################ CLEANUP ##########################################################

# Register cleanup on exit to close any open browsers
atexit.register(cleanup_browsers)




############################################ HELPER FUNCTIONS ##########################################



def setup_environment():
    """First-time setup to make the CLI runnable system-wide."""
    import subprocess
    import sys
    from ap_core.platform_paths import get_config_dir, is_windows
    
    # Write sample config to platform-appropriate location
    try:
        config_dir = get_config_dir()
        default_path = config_dir / 'config.ini'
        write_sample_config(str(default_path))
        print(f"✓ Sample config written to: {default_path}")
    except Exception as e:
        print(f"Config setup skipped: {e}")
    
    # Install Playwright browser
    print("🔧 Installing browser for automation...")
    try:
        # Try to install chrome first, fall back to chromium
        os.environ['AUTOPAHE_BROWSER'] = 'chrome'
        print("   Installing Chrome browser...")
        rc = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chrome'],
            check=False,
            capture_output=True
        )
        if rc.returncode != 0:
            print("   Chrome not available, trying Chromium...")
            rc = subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', 'chromium'],
                check=False,
                capture_output=True
            )
            if rc.returncode != 0:
                print("❌ Failed to install browser. Please run manually:")
                print("   python -m playwright install chromium")
                return False
            os.environ['AUTOPAHE_BROWSER'] = 'chromium'
        
        print("✅ Setup completed successfully!")
        print(f"\n📁 Config location: {default_path}")
        print("   Edit with: autopahe config edit")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\nPlease install Playwright manually:")
        print("   pip install playwright")
        print("   python -m playwright install chromium")
        return False

def get_performance_stats():
    """Get performance statistics for the current session."""
    stats = {
        'cache_efficiency': 0,
        'memory_usage_mb': 0,
        'cached_items': 0,
    }
    
    try:
        # Cache statistics
        cache_stats = get_cache_stats()
        stats['cache_efficiency'] = cache_stats.get('hit_rate', 0)
        stats['cached_items'] = len(_cache_store['episodes']) + len(_cache_store['anime'])
        
        # Memory usage (approximate)
        import sys
        total_size = 0
        for cache_dict in _cache_store.values():
            total_size += sys.getsizeof(cache_dict)
            for key, val in cache_dict.items():
                total_size += sys.getsizeof(key) + sys.getsizeof(val)
        stats['memory_usage_mb'] = total_size / (1024 * 1024)
    except Exception:
        pass
        
    return stats

def apply_search_filters(results, year_filter=None, status_filter=None):
    """Apply year and status filters to search results."""
    if year_filter:
        try:
            year = int(year_filter)
            results = [r for r in results if r.get('year') == year]
            logging.debug(f"Filtered by year={year}, {len(results)} results remain")
        except ValueError:
            pass
    
    if status_filter:
        status_lower = status_filter.lower()
        results = [r for r in results if status_lower in str(r.get('status', '')).lower()]
        logging.debug(f"Filtered by status={status_filter}, {len(results)} results remain")
    
    return results

def lookup(arg, year_filter=None, status_filter=None, enable_fuzzy=True):
    """Search for anime using AnimePahe API with filters and fuzzy matching.
    
    Tries disk cache FIRST for instant results, then direct HTTP request, falls back to Playwright only if needed.
    This avoids unnecessary browser launches for better performance.
    
    Args:
        arg: Search query string (supports typos with fuzzy matching)
        year_filter: Optional year to filter results
        status_filter: Optional status string to filter results
        enable_fuzzy: Enable fuzzy search for typo tolerance (default: True)
    """
    state = get_runtime_state()
    search_response_dict = state.search_results if isinstance(state.search_results, dict) else {}
    global _from_cache
    _from_cache = False
    
    # Apply fuzzy search preprocessing for better matching
    if enable_fuzzy:
        original_query = arg
        arg = fuzzy_engine.preprocess_query(arg)
        if arg != original_query.lower():
            print(f"🔍 Search corrected: '{original_query}' → '{arg}'")

    # Display progress indicator and search banner
    Banners.progress_indicator("searching")

    # API endpoint for search (prefer .si, fallback to .com)
    api_url = f'https://animepahe.si/api?m=search&q={arg}'
    search_response = None

    try:
        # Step 1: Check disk cache FIRST for instant results
        print(f"        🔍 Checking cache...")
        cached = cache_get(api_url, max_age_hours=24)
        if cached:
            print(f"        ✅ Found cached data: {len(cached)} bytes")
            search_response = cached
            _from_cache = True
            logging.debug("✓ Loaded from disk cache")
            
            try:
                # Parse cached response and return immediately (INSTANT ACCESS)
                search_response_dict = json.loads(search_response)
                state.search_results = search_response_dict
                print(f"        ✅ Parsed cached JSON successfully")
                logging.debug(f"Found {len(search_response_dict.get('data', []))} cached results")
                
                # Apply filters to cached results if provided
                results = apply_search_filters(search_response_dict['data'], year_filter, status_filter)
                
                if not results:
                    print(f"\n❌ No anime found matching your search with the given filters.\n")
                    print("💡 Tips:")
                    print("   - Try different spelling or formatting")
                    print("   - Check if the anime name is correct")
                    print("   - Try searching with fewer keywords\n")
                    return None
                
                # Display cached results using structured design
                Banners.search_results(results, from_cache=True)
                
                print(f"        {Fore.YELLOW}⚡ Found cached result - No browser/API used!{Style.RESET_ALL}")
                return search_response_dict  # EARLY RETURN - INSTANT CACHE HIT
                
            except Exception as e:
                print(f"❌ Cache parsing error: {e}")
                print("🔄 Cache corrupted, proceeding with fresh search...")
        
        else:
            print("❌ No cached data found")
        
        # If not cached, proceed with network requests
        print("🔍 Searching (not cached)...")
        
        # Step 2: Try direct HTTP request (fast, no browser needed) with loading spinner
        logging.debug("Fetching from API...")
        
        with LoadingSpinner("Searching anime...", "dots") as spinner:
            session = get_request_session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
                'Accept': 'application/json'
            }
            for base in ("https://animepahe.si", "https://animepahe.com", "https://animepahe.ru"):
                try:
                    spinner.update_text(f"Searching on {base}...")
                    url = f"{base}/api"
                    response = session.get(url, params={"m":"search","q":arg}, headers=headers, timeout=15)
                    if response.status_code == 200 and response.content:
                        search_response = response.content
                        # Normalize api_url to the working domain for downstream/fallbacks
                        api_url = response.url
                        cache_set(api_url, search_response)
                        logging.debug(f"✓ Fetched from API and cached ({base})")
                        break
                    else:
                        logging.warning(f"API {base} returned status {response.status_code}")
                except Exception as _e:
                    logging.debug(f"Fetch attempt on {base} failed: {_e}")

        # Parse response if we got one
        if search_response:
            search_response_dict = json.loads(search_response)
            state.search_results = search_response_dict
            logging.debug(f"Found {len(search_response_dict.get('data', []))} results")
        else:
            # Step 3: Only use Playwright as last resort (slow, resource intensive)
            logging.warning("Direct API failed, falling back to Playwright...")
            with LoadingSpinner("Loading browser for search...", "dots") as spinner:
                spinner.update_text("Launching browser...")
                search_response = driver_output(api_url, driver=True, json=True, wait_time=5)
                if search_response:
                    search_response_dict = search_response
                    state.search_results = search_response_dict
                    # Cache the Playwright results as JSON bytes for future instant access
                    cache_set(api_url, json.dumps(search_response_dict).encode())
                    logging.debug(f"Playwright fallback succeeded and cached")
                    # Don't close browser yet - might need it for index/about operations
                else:
                    logging.error("All methods failed to retrieve search results")
                    search_response_dict = {'data': []}
                    state.search_results = search_response_dict

    except (requests.exceptions.RequestException, Exception) as e:
        # Any error - try Playwright fallback once
        logging.warning(f"Error ({type(e).__name__}: {e}), trying Playwright fallback...")
        try:
            search_response = driver_output(api_url, driver=True, json=True, wait_time=5)
            if search_response:
                search_response_dict = search_response
                state.search_results = search_response_dict
                cache_set(api_url, json.dumps(search_response_dict).encode())
            else:
                search_response_dict = {'data': []}
                state.search_results = search_response_dict
        except Exception:
            search_response_dict = {'data': []}
            state.search_results = search_response_dict

    # Check if results exist
    if not search_response_dict or 'data' not in search_response_dict or not search_response_dict['data']:
        logging.error("No results found. Please try a different search term.")
        print("\n❌ No anime found matching your search.\n")
        return None
    
    # Debug: Show we have results
    logging.info(f"Processing {len(search_response_dict['data'])} search results")
    
    # Apply filters if provided
    results = apply_search_filters(search_response_dict['data'], year_filter, status_filter)
    search_response_dict['data'] = results
    
    if not results:
        print(f"\n❌ No anime found matching your search with the given filters.\n")
        print("💡 Tips:")
        print("   - Try different spelling or formatting")
        print("   - Check if the anime name is correct")
        print("   - Try searching with fewer keywords\n")
        return None
    
    resultlen = len(search_response_dict['data'])
    
    # Pre-fetch episode data for all search results to make anime selection instant
    episode_urls = []
    for anime in search_response_dict['data']:
        session_id = anime['session']
        episode_url = f'https://animepahe.com/api?m=release&id={session_id}&sort=episode_asc&page=1'
        episode_urls.append(episode_url)
    
    # Check which episode URLs need fetching
    urls_to_fetch = []
    for url in episode_urls:
        if url not in _episode_cache:
            urls_to_fetch.append(url)
    
    if urls_to_fetch:
        print(f"        🚀 Pre-fetching episode data for {len(urls_to_fetch)} anime(s)...")
        try:
            # Fetch episode data in parallel
            episode_results = batch_driver_output(urls_to_fetch, json=True, wait_time=5)
            if episode_results:
                cached_count = 0
                for url, episode_data in episode_results.items():
                    if episode_data:
                        # Cache episode data to both memory and disk
                        _episode_cache[url] = episode_data
                        cache_set(url, json.dumps(episode_data).encode())
                        cached_count += 1
                print(f"        ✅ Cached episode data for {cached_count}/{len(urls_to_fetch)} anime(s)")
        except Exception as e:
            logging.debug(f"Episode pre-fetch failed: {e}")
            print(f"        ⚠ Episode pre-fetch failed, will fetch on demand")
    else:
        print(f"        ✅ Episode data already cached for all {len(episode_urls)} anime(s)")
    
    # Display results using structured design
    from_cache = '_from_cache' in globals() and _from_cache
    Banners.search_results(search_response_dict['data'], from_cache=from_cache)
    state.search_results = search_response_dict
    
    return search_response_dict




# =========================================== handling the single download utility ============================
    

def index(arg):
    """Display information about the selected anime and prepare for downloads.
    
    Args:
        arg: Index of the anime in search results
    """
    print("\n")  # Don't clear screen, just add spacing

    state = get_runtime_state()
    search_response_dict = state.search_results if isinstance(state.search_results, dict) else {}

    try:
        # Get anime data from search results
        anime_data = search_response_dict['data'][int(arg)]
        
        # Set global variables
        state.anime_name = anime_data['title']
        state.session_id = anime_data['session']
        state.anime_id = state.session_id
        state.episode_page_format = f'https://animepahe.com/anime/{state.session_id}'
        
        # Fetch first page of episodes (for display). Additional pages fetched lazily on demand.
        state.episode_page_data = fetch_episode_page(state.session_id, page_num=1, use_cache=True) or {}
        jsonpage_dict = state.episode_page_data
        
        if not jsonpage_dict or 'data' not in jsonpage_dict:
            logging.error("Failed to fetch episode list. The server may be down or rate limiting requests.")
            # Still display basic anime info even if episode list fails
            anime_info = {
                'title': anime_data['title'],
                'episodes': anime_data.get('episodes', 'N/A'),
                'year': anime_data.get('year', 'N/A'),
                'type': anime_data.get('type', 'N/A'),
                'status': anime_data.get('status', 'N/A'),
                'image': f"https://animepahe.si{anime_data.get('poster', '')}" if anime_data.get('poster') and not anime_data.get('poster', '').startswith('http') else anime_data.get('poster', 'No image available'),
                'homepage': state.episode_page_format,
                'episode_count': 'N/A',
                'first_episode': 'N/A',
                'last_episode': 'N/A'
            }
        else:
            # Prepare anime info for display
            anime_info = {
                'title': anime_data['title'],
                'episodes': jsonpage_dict.get('total', anime_data.get('episodes', 'N/A')),
                'year': anime_data.get('year', 'N/A'),
                'type': anime_data.get('type', 'N/A'),
                'status': anime_data.get('status', 'N/A'),
                'image': f"https://animepahe.si{anime_data.get('poster', '')}" if anime_data.get('poster') and not anime_data.get('poster', '').startswith('http') else anime_data.get('poster', 'No image available'),
                'homepage': state.episode_page_format,
                'episode_count': len(jsonpage_dict.get('data', [])),
                'first_episode': jsonpage_dict['data'][0]['episode'] if jsonpage_dict.get('data') else 'N/A',
                'last_episode': jsonpage_dict['data'][-1]['episode'] if jsonpage_dict.get('data') else 'N/A'
            }
        
        # Display anime info using structured design
        Banners.anime_selection(anime_info)
        
        # Display available commands using structured design
        Banners.commands_table()
        
        # Combine response data for further processing
        if jsonpage_dict:
            final_data = {**search_response_dict, **jsonpage_dict}
        else:
            final_data = search_response_dict
        return final_data
        
    except IndexError:
        logging.error(f"Invalid anime index: {arg}. Please select a valid number.")
        return None
    except Exception as e:
        logging.error(f"Error in index function: {e}")
        if not search_response_dict:
            logging.error("No search results available. Please perform a search first.")
        return None

def about():
        state = get_runtime_state()
        episode_page_format = state.episode_page_format
        if not episode_page_format:
            return ''
        # Prefer prefetched HTML if available
        html = _prefetched_pages.get(episode_page_format)
        if not html:
            # Use Playwright to get synopsis directly
            browser_choice = (os.environ.get('AUTOPAHE_BROWSER') or 'chrome').lower()
            context = get_pw_context(browser_choice, headless=True)
            if context:
                page = context.new_page()
                page.goto(episode_page_format, wait_until='domcontentloaded', timeout=30000)
                synopsis = page.query_selector('.anime-synopsis')
                if synopsis:
                    return synopsis.inner_text().strip()
                page.close()
        else:
            # Parse from cached HTML using regex (faster than BeautifulSoup)
            import re
            match = re.search(r'<div[^>]*class=["\']anime-synopsis["\'][^>]*>([^<]*)</div>', html, re.DOTALL)
            if match:
                return match.group(1).strip()
        return ''





def download(arg=1, download_file=True, res = "720", prefer_dub=False):
    """
    Download the specified episode by navigating with Playwright and extracting the download link.
    """
    
    state = get_runtime_state()
    try:
        # Convert the argument to an integer to ensure it is in the correct format
        arg = int(arg)

        # Check if anime is selected
        if not state.session_id:
            logging.error("No anime selected. Please select an anime first.")
            return
        
        # Get episode session using lazy loading (fetches correct page on demand)
        episode_session, episode_data = get_episode_session(state.session_id, arg)
        if not episode_session:
            # get_episode_session already logs the error with total count
            jsonpage_dict = state.episode_page_data
            total = jsonpage_dict.get('total', 'unknown') if jsonpage_dict else 'unknown'
            print(f"\n❌ Episode {arg} not found. This anime has {total} episodes available.")
            return

        # Construct the URL for the stream page for the specific episode using the session ID
        stream_page_url = f'https://animepahe.com/play/{state.session_id}/{episode_session}'

        # Navigate with shared Playwright context (headless) and extract links then the kwik page
        browser_choice = (os.environ.get('AUTOPAHE_BROWSER') or 'chrome').lower()
        context = get_pw_context(browser_choice, headless=True)
        if context is None:
            logging.error("Playwright context not available")
            return
        page = context.new_page()
        page.goto(stream_page_url, wait_until='domcontentloaded', timeout=60000)
        # Wait for dropdown links to be present
        try:
            page.wait_for_selector('a.dropdown-item[target="_blank"]', timeout=30000)
        except Exception:
            pass
        # Extract links with their text content (which contains resolution info)
        dload_items = page.eval_on_selector_all(
            'a.dropdown-item[target="_blank"]', 
            'els => els.map(e => ({href: e.href, text: e.textContent}))'
        ) or []
        
        # Debug: Log all found links
        logging.debug(f"Found {len(dload_items)} download links total")
        for item in dload_items[:5]:  # Log first 5 links
            logging.debug(f"  Link: {item.get('text', 'unknown')} -> {item.get('href', 'no-url')}")
        
        # Filter download links based on requested resolution
        # Parse resolution from text content, not URL
        min_resolution = 360 if res in ['360', '480'] else 720
        
        # Build list of (href, resolution) tuples
        link_tuples = []
        for item in dload_items:
            text = item.get('text', '')
            href = item.get('href', '')
            
            # Extract resolution from text (e.g., "360p", "720p", "1080p")
            res_match = re.search(r'(\d{3,4})p', text)
            if res_match and href:
                resolution = int(res_match.group(1))
                # Filter by audio preference: dub (eng) or sub (non-eng)
                has_eng = 'eng' in text.lower()
                if resolution >= min_resolution:
                    if prefer_dub and has_eng:
                        link_tuples.append((href, resolution))
                    elif not prefer_dub and not has_eng:
                        link_tuples.append((href, resolution))
        
        # Sort by resolution (lowest first)
        link_tuples.sort(key=lambda x: x[1])
        linkpahe = [href for href, _ in link_tuples]

        # Debug: Log filtered links
        logging.debug(f"After filtering (min_res={min_resolution}p): {len(linkpahe)} links")
        for link in linkpahe[:3]:  # Log first 3 filtered links
            res_match = re.search(r'(\d{3,4})p', link)
            res_val = res_match.group(0) if res_match else 'unknown'
            logging.debug(f"  Filtered link: {res_val} - {link[:80]}...")  # Truncate long URLs

        # If a valid download link is found, proceed with the next steps
        if not linkpahe:
            page.close()
            raise ValueError(f"No valid download link found for episode {arg}")

        # Navigate to the selected download link based on requested resolution
        res = str(res)
        
        # Find the best matching resolution
        if res == '360':
            # Get lowest resolution available
            page.goto(linkpahe[0], wait_until='domcontentloaded', timeout=60000)
        elif res == '480':
            # Try to find 480p or closest
            res_480 = [l for l in linkpahe if '480p' in l]
            target = res_480[0] if res_480 else linkpahe[0]
            page.goto(target, wait_until='domcontentloaded', timeout=60000)
        elif res == '720':
            # Try to find 720p or closest
            res_720 = [l for l in linkpahe if '720p' in l]
            target = res_720[0] if res_720 else linkpahe[0]
            page.goto(target, wait_until='domcontentloaded', timeout=60000)
        elif res == '1080':
            # Get highest resolution available
            page.goto(linkpahe[-1], wait_until='domcontentloaded', timeout=60000)
        elif res == 'best':
            # Get highest resolution
            page.goto(linkpahe[-1], wait_until='domcontentloaded', timeout=60000)
        elif res == 'worst':
            # Get lowest resolution
            page.goto(linkpahe[0], wait_until='domcontentloaded', timeout=60000)
        else:
            # Default to first available
            page.goto(linkpahe[0], wait_until='domcontentloaded', timeout=60000)

        # Wait for the kwik redirect anchor and extract href
        try:
            page.wait_for_selector('a.redirect', timeout=30000)
            kwik = page.eval_on_selector('a.redirect', 'el => el.href')
        except Exception:
            # Fallback to Playwright selector
            page.wait_for_timeout(5000)
            redirect_link = page.query_selector('a.redirect')
            kwik = redirect_link.get_attribute('href') if redirect_link else None
        page.close()

    except Exception as e:
        # Log general errors
        logging.error(f"Episode {arg} failed: {e}")
        return

    # Ensure we have a valid kwik link
    if not kwik:
        logging.error("Failed to locate kwik redirect link")
        return

    # Print the found download link to the terminal
    # print(f"\nEpisode {arg} Download link => {kwik}\n")

    if download_file:
        # Show download progress using structured design
        Banners.download_progress(state.anime_name or "Unknown Anime", arg)

        # Build a stable filename based on display title, episode and quality
        safe_name = _build_safe_filename(state.anime_name or "Unknown Anime", ep=arg, quality=res)
        episode_path = DOWNLOADS / safe_name

        # Add download to resume manager for tracking
        download_id = resume_manager.add_download(
            anime_title=state.anime_name or "Unknown Anime",
            episode_number=str(arg),
            download_url=kwik,
            file_path=str(episode_path),
            quality=res
        )

        # Trigger the download process using the kwik link and specify the download directory
        result = kwik_download(url=kwik, dpath=DOWNLOADS, ep=arg, animename=state.anime_name or "Unknown Anime", quality=res)
        
        # Track download in collection manager
        if result is not False:  # kwik_download returns False on failure
            # Mark download as completed in resume manager
            resume_manager.mark_completed(download_id)
            
            # Add to collection manager (without organizing - --sort handles that)
            cm = get_collection_manager()
            entry = cm.add_anime(state.anime_name or "Unknown Anime")
            episode_file = str(episode_path)
            cm.add_episode_file(state.anime_name or "Unknown Anime", arg, episode_file, organize=False)
            Banners.success_message(f"Added episode {arg} to collection for '{state.anime_name or 'Unknown Anime'}'")
        else:
            # Mark download as failed in resume manager
            resume_manager.mark_failed(download_id, "Download failed")
    else:
        return kwik


                
    # ========================================== Multi Download Utility ==========================================

    
def stream_episode(arg=1, player="default", res="720", prefer_dub=False):
    """
    Stream the specified episode by extracting the video URL and launching media player.
    """
    state = get_runtime_state()
    log_prefix = "        "
    
    try:
        # Convert the argument to an integer to ensure it is in the correct format
        arg = int(arg)

        # Check if anime is selected
        if not state.session_id:
            logging.error("No anime selected. Please select an anime first.")
            return False
        
        # Get episode session using lazy loading (fetches correct page on demand)
        episode_session, episode_data = get_episode_session(state.session_id, arg)
        if not episode_session:
            jsonpage_dict = state.episode_page_data
            total = jsonpage_dict.get('total', 'unknown') if jsonpage_dict else 'unknown'
            print(f"\n{log_prefix}❌ Episode {arg} not found. This anime has {total} episodes available.")
            return False

        # Resolve player once so cached paths don't hit "default"
        if player == "default":
            detected_player = detect_available_player()
            if not detected_player:
                print(f"{log_prefix}❌ No media player found. Please install mpv, vlc, or mplayer.")
                print(f"{log_prefix}💡 Installation commands:")
                print(f"{log_prefix}   Ubuntu/Debian: sudo apt install mpv vlc")
                print(f"{log_prefix}   macOS: brew install mpv vlc")
                print(f"{log_prefix}   Windows: Download from mpv.io or videolan.org")
                return False
            
            player = detected_player
            print(f"{log_prefix}📺 Using detected player: {player}")
        
        # Check if we have cached play page data for this anime
        cached_anime = get_cached_anime_data(state.anime_id)
        cache_available = bool(cached_anime and 'play_links' in cached_anime)
        if cache_available:
            print(f"{log_prefix}⚡ Using cached streaming data for instant access")
            play_links = cached_anime['play_links']
            
            # Find the specific episode's play links
            episode_key = f"{state.anime_id}_{episode_session}"
            if episode_key in play_links:
                dload_items = play_links[episode_key]
                
                # Filter download links based on requested resolution
                min_resolution = 360 if res in ['360', '480'] else 720
                
                # Build list of (href, resolution) tuples
                link_tuples = []
                for item in dload_items:
                    href = item.get('href', '')
                    text = item.get('text', '')
                    # Parse resolution from text content
                    resolution_match = re.search(r'(\d+)p', text)
                    if resolution_match:
                        resolution = int(resolution_match.group(1))
                        link_tuples.append((href, resolution))
                
                # Sort by resolution (highest first) and filter
                link_tuples.sort(key=lambda x: x[1], reverse=True)
                filtered_links = [href for href, res_val in link_tuples if res_val >= min_resolution]
                
                if filtered_links:
                    kwik_url = filtered_links[0]  # Use highest resolution that meets criteria
                    print(f"{log_prefix}🎯 Using cached kwik URL: {kwik_url}")
                    
                    # Stream using cached URL
                    video_url, headers = kwik_stream(kwik_url, ep=arg, animename=state.anime_name or "Unknown Anime")
                    if video_url:
                        success = stream_video(video_url, headers, player, indent=log_prefix)
                        if success:
                            print(f"{log_prefix}✅ Episode {arg} streaming completed")
                            return True
                        print(f"{log_prefix}❌ Cached stream failed for episode {arg}, retrying from play page...")
                    else:
                        print(f"{log_prefix}❌ Cached link failed for episode {arg}, retrying from play page...")
                else:
                    print(f"{log_prefix}❌ No cached links found for episode {arg} with resolution {res}p")
            else:
                print(f"{log_prefix}❌ Episode {arg} not found in cached streaming data")
            
            print(f"{log_prefix}🔄 Cached data incomplete, fetching from play page...")
        else:
            print(f"{log_prefix}🔄 No cached streaming data, fetching from play page...")
        
        # Construct the API URL to get the download page for the selected episode
        api_url = f'https://animepahe.si/api?m=release&id={state.anime_id}&session={episode_session}'
        
        # Construct the URL for the stream page for the specific episode using the session ID
        stream_page_url = f'https://animepahe.com/play/{state.anime_id}/{episode_session}'

        # Navigate with shared Playwright context (headless) and extract links then the kwik page
        browser_choice = (os.environ.get('AUTOPAHE_BROWSER') or 'chrome').lower()
        try:
            context = get_pw_context(browser_choice, headless=True)
            if context is None:
                logging.error("Playwright context not available")
                return False
            page = context.new_page()
            page.goto(stream_page_url, wait_until='domcontentloaded', timeout=60000)
        except Exception as e:
            logging.error(f"Playwright navigation failed: {e}")
            try:
                if 'page' in locals():
                    page.close()
            except Exception:
                pass
            return False
        
        # Wait for dropdown links to be present
        try:
            page.wait_for_selector('a.dropdown-item[target="_blank"]', timeout=30000)
        except Exception:
            pass
        
        # Extract links with their text content (which contains resolution info)
        dload_items = page.eval_on_selector_all(
            'a.dropdown-item[target="_blank"]', 
            'els => els.map(e => ({href: e.href, text: e.textContent}))'
        ) or []
        
        # Cache the play page data for future instant access
        if dload_items:
            episode_key = f"{state.anime_id}_{episode_session}"
            cached_anime = get_cached_anime_data(state.anime_id)
            if cached_anime:
                if 'play_links' not in cached_anime:
                    cached_anime['play_links'] = {}
                cached_anime['play_links'][episode_key] = dload_items
                cache_anime_data(state.anime_id, cached_anime['episode_data'], cached_anime['play_links'])
                logging.debug(f"Cached play page data for episode {arg}")
            else:
                # Create new anime cache entry using current episode data
                if state.episode_page_data:
                    episode_data = state.episode_page_data
                    play_links = {episode_key: dload_items}
                    cache_anime_data(state.anime_id, episode_data, play_links)
                    logging.debug(f"Created new anime cache entry for episode {arg}")
        
        # Debug: Log all found links
        logging.debug(f"Found {len(dload_items)} download links total")
        for item in dload_items[:5]:  # Log first 5 links
            logging.debug(f"  Link: {item.get('text', 'unknown')} -> {item.get('href', 'no-url')}")
        
        # Filter download links based on requested resolution
        # Parse resolution from text content, not URL
        min_resolution = 360 if res in ['360', '480'] else 720
        
        # Build list of (href, resolution) tuples
        link_tuples = []
        for item in dload_items:
            text = item.get('text', '')
            href = item.get('href', '')
            
            # Extract resolution from text (e.g., "360p", "720p", "1080p")
            res_match = re.search(r'(\d{3,4})p', text)
            if res_match and href:
                resolution = int(res_match.group(1))
                # Filter by audio preference: dub (eng) or sub (non-eng)
                has_eng = 'eng' in text.lower()
                if resolution >= min_resolution:
                    if prefer_dub and has_eng:
                        link_tuples.append((href, resolution))
                    elif not prefer_dub and not has_eng:
                        link_tuples.append((href, resolution))
        
        # Sort by resolution (lowest first)
        link_tuples.sort(key=lambda x: x[1])
        linkpahe = [href for href, _ in link_tuples]
        
        if not linkpahe:
            raise ValueError(f"No valid streaming link found for episode {arg}")
        
        # Navigate to the selected download link based on requested resolution
        res = str(res)
        
        # Find the best matching resolution
        if res == '360':
            # Get lowest resolution available
            kwik = linkpahe[0]
        elif res == '480':
            # Try to find 480p or closest
            kwik = linkpahe[0]  # Use lowest available
        elif res == '720':
            # Try to find 720p or closest
            if len(linkpahe) >= 2:
                kwik = linkpahe[1]  # Use second (usually 720p)
            else:
                kwik = linkpahe[-1]  # Use highest available
        elif res == '1080':
            # Try to find 1080p or closest
            kwik = linkpahe[-1]  # Use highest available
        elif res == 'best':
            # Get highest resolution available
            kwik = linkpahe[-1]
        elif res == 'worst':
            # Get lowest resolution available
            kwik = linkpahe[0]
        else:
            # Default to 720p
            if len(linkpahe) >= 2:
                kwik = linkpahe[1]
            else:
                kwik = linkpahe[-1]
        
        if not kwik:
            raise ValueError(f"No valid streaming link found for episode {arg}")

        print(f"{log_prefix}🎬 Preparing to stream episode {arg} of {state.anime_name or 'Unknown Anime'}")
        print(f"{log_prefix}🔗 Extracted kwik URL: {kwik[:50]}..." if len(kwik) > 50 else f"{log_prefix}🔗 Extracted kwik URL: {kwik}")
        
        # Close the Playwright page before streaming
        try:
            page.close()
        except:
            pass
        
        # Extract video URL and stream
        video_url, headers = kwik_stream(url=kwik, ep=arg, animename=state.anime_name or "Unknown Anime")
        
        if video_url:
            success = stream_video(video_url, headers, player, indent=log_prefix)
            if success:
                Banners.success_message(f"Episode {arg} streaming completed", compact=True)
                return True
            else:
                print(f"{log_prefix}❌ Failed to stream episode {arg}")
                return False
        else:
            print(f"{log_prefix}❌ Failed to extract video URL for episode {arg}")
            return False
            
    except Exception as e:
        print(f"{log_prefix}❌ Streaming failed for episode {arg}: {e}")
        return False


def multi_stream(arg: str, player="default", resolution="720", prefer_dub=False):
    """
    Stream multiple episodes sequentially.
    """
    log_prefix = "        "
    # Parse input like '2,3,5-7' into [2,3,5,6,7]
    eps = []
    for part in arg.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            eps.extend(range(start, end + 1))
        elif part.isdigit():
            eps.append(int(part))

    Banners.info_message(f"🎬 Starting sequential streaming of {len(eps)} episodes")
    
    # Sequential streaming to avoid Playwright threading issues
    completed = 0
    failed = []
    
    for ep in eps:
        try:
            success = stream_episode(arg=ep, player=player, res=resolution, prefer_dub=prefer_dub)
            if success:
                completed += 1
                Banners.success_message(f"Episode {ep} completed successfully ({completed}/{len(eps)})", compact=True)
            else:
                failed.append(ep)
                logging.error(f"Episode {ep} failed to stream")
        except Exception as e:
            failed.append(ep)
            logging.error(f"Episode {ep} failed: {e}")
    
    # Report results
    if failed:
        print(f"\n{log_prefix}⚠️ Streaming completed with {len(failed)} failed episodes: {failed}")
    else:
        print(f"\n{log_prefix}✅ All {len(eps)} episodes streamed successfully!")
    
    return len(failed) == 0


def multi_download(arg: str, download_file=True, resolution="720", max_workers=1, enable_notifications=False, prefer_dub=False):
    """
    Downloads multiple episodes sequentially.
    Note: Parallel downloads disabled due to Playwright threading incompatibility.
    Playwright's sync API uses greenlets which cannot be shared across ThreadPoolExecutor threads.
    """
    state = get_runtime_state()
    # Force sequential downloads - Playwright is not thread-safe
    if max_workers > 1:
        Banners.info_message("⚠️ Parallel downloads disabled - Playwright requires sequential execution")
    max_workers = 1
    
    # Parse input like '2,3,5-7' into [2,3,5,6,7]
    eps = []
    for part in arg.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            eps.extend(range(start, end + 1))
        elif part.isdigit():
            eps.append(int(part))

    Banners.info_message(f"📥 Starting sequential download of {len(eps)} episodes")
    
    # Sequential downloads to avoid Playwright threading issues
    completed = 0
    failed = []
    
    for ep in eps:
        try:
            download(arg=ep, download_file=download_file, res=str(resolution), prefer_dub=prefer_dub)
            completed += 1
            Banners.success_message(f"Episode {ep} completed successfully ({completed}/{len(eps)})")
        except Exception as e:
            failed.append(ep)
            logging.error(f"Episode {ep} failed: {e}")
    
    # Send notification if enabled
    if enable_notifications and download_file:
        if failed:
            notify_download_failed(state.anime_name or "Unknown Anime", f"Failed: {', '.join(map(str, failed))}")
        else:
            notify_download_complete(state.anime_name or "Unknown Anime", arg)




# ----------------------------------------------End of All the Argument Handling----------------------------------------------------------

#
# Function to handle user interaction and guide them through the anime selection and download process
def interactive_main():
    """Interactive mode for users who prefer guided input.
    
    Prompts for search, selection, and download options step-by-step.
    """
    # Display header banner
    Banners.header()
    
    print("\n=== Interactive Mode ===", flush=True)
    print("Tip: Use command-line args for faster operation (try --help)\n", flush=True)
    
    # Search for anime
    lookup_anime = input("Search for anime: ").strip()
    if not lookup_anime:
        print("No search term provided. Exiting.")
        return
    
    lookup(lookup_anime)
    
    # Select anime from results
    try:
        select_index = int(input("\nSelect anime index [default: 0]: ") or "0")
        index(select_index)
    except (ValueError, IndexError) as e:
        print(f"Invalid selection: {e}")
        return
    
    # Display anime info
    info = about()
    Banners.i_info(info)
    
    # Initialize records list for tracking operations
    records = []
    
    # Download selection
    print("\nDownload Options:")
    print("  1 or 's'  - Single episode")
    print("  2 or 'md' - Multiple episodes")
    print("  3 or 'a'  - View about/info")
    
    download_type = input("\nSelect option: ").strip().lower()
    
    if download_type in ['1', 's', 'single']:
        ep = input("Episode number: ")
        if ep.isdigit():
            download(int(ep), download_file=True)
            process_record(records, update=True, quiet=True)
    elif download_type in ['2', 'md', 'multi']:
        eps = input("Episodes (e.g., 1-5 or 1,3,5): ")
        multi_download(eps, download_file=True)
        process_record(records, update=True, quiet=True)
    elif download_type in ['3', 'a', 'about']:
        # Info already displayed above
        pass
    else:
        print("Invalid option selected.")


def command_main(args, ctx: Optional[typer.Context] = None):
    state = get_runtime_state(ctx)
    search_response_dict = state.search_results if isinstance(state.search_results, dict) else {}
    records = []  # Initialize records list for tracking operations
    sarg = args.search  # Search query for anime
    iarg = args.index  # Index of selected anime
    sdarg = args.single_download  # Argument for single episode download
    mdarg = args.multi_download  # Argument for multi-episode download
    starg = args.stream  # Argument for streaming
    player_arg = args.player  # Media player for streaming
    abtarg = args.about  # Flag for displaying anime information
    rarg = args.record  # Argument for interacting with records
    dtarg = args.execution_data  # New argument for execution stats by date
    larg = args.link
    mlarg = args.multilinks
    parg = args.resolution
    rcmds = args.records
    sort_cmd = args.sort
    sort_path = args.sort_path
    sort_dry = args.sort_dry_run
    summary_arg = args.summary
    
    # New Phase 2/3/4 args
    year_filter = getattr(args, 'year', None)
    status_filter = getattr(args, 'status', None)
    enable_notifications = getattr(args, 'notify', False)
    batch_season = getattr(args, 'season', None)
    cache_cmd = getattr(args, 'cache', None)

    # Get new feature arguments
    enable_fuzzy = not getattr(args, 'no_fuzzy', False)
    fuzzy_threshold = getattr(args, 'fuzzy_threshold', 0.6)
    resume_downloads = getattr(args, 'resume', False)
    resume_stats_cmd = getattr(args, 'resume_stats', False)
    max_retries = getattr(args, 'max_retries', 3)
    collection_cmd = getattr(args, 'collection', None)
    collection_path = getattr(args, 'collection_path', None)
    watch_status = getattr(args, 'watch_status', None)
    watch_progress = getattr(args, 'watch_progress', None)
    rating = getattr(args, 'rate', None)
    
    # Apply config-driven overrides
    global DOWNLOADS
    try:
        cfg = APP_CONFIG
    except NameError:
        cfg = None

    # Check for custom download directory from environment variable (Docker)
    if os.getenv('AUTOPAHE_DOWNLOAD_DIR'):
        DOWNLOADS = Path(os.getenv('AUTOPAHE_DOWNLOAD_DIR'))
    elif cfg and cfg.get('download_dir'):
        DOWNLOADS = Path(cfg['download_dir'])
    
    # Configure resume manager
    resume_manager.max_retries = max_retries

    # Note: Browser is only launched when actually needed (during downloads)
    # This avoids unnecessary resource usage and startup delays
    
    # Handle cache commands
    if cache_cmd:
        if cache_cmd == 'clear':
            cache_clear()
            print("✓ Cache cleared")
            return
        elif cache_cmd == 'stats':
            stats = get_cache_stats()
            print(f"\nCache Statistics:")
            print(f"  Files: {stats['count']}")
            print(f"  Size: {stats['size_mb']} MB")
            print(f"  Path: {stats['path']}\n")
            return
    
    # Handle Resume System commands
    if resume_stats_cmd:
        """Display download resume statistics."""
        stats = resume_manager.get_download_stats()
        print(f"\n📊 Download Resume Statistics:")
        print(f"  Total downloads: {stats['total']}")
        print(f"  Pending: {stats.get('pending', 0)}")
        print(f"  Downloading: {stats.get('downloading', 0)}")
        print(f"  Completed: {stats.get('completed', 0)}")
        print(f"  Failed: {stats.get('failed', 0)}")
        print(f"  Resumable: {stats.get('resumable', 0)}")
        print(f"  Total downloaded: {stats.get('total_downloaded_mb', 0):.2f} MB")
        
        # Show resumable downloads
        resumable = resume_manager.get_resumable_downloads()
        if resumable:
            print(f"\n🔄 Resumable Downloads:")
            for download_id, state in resumable[:5]:  # Show first 5
                progress_pct = (state.downloaded_size / state.total_size * 100) if state.total_size else 0
                print(f"  • {state.anime_title} - Episode {state.episode_number}")
                print(f"    Progress: {progress_pct:.1f}% ({state.downloaded_size / (1024*1024):.1f} MB)")
                print(f"    Status: {state.status}, Retries: {state.retry_count}")
        return
    
    if resume_downloads:
        """Resume interrupted downloads from previous session."""
        resumable = resume_manager.get_resumable_downloads()
        if not resumable:
            print("✅ No downloads to resume")
            return
        
        print(f"\n🔄 Resuming {len(resumable)} interrupted downloads...")
        for download_id, state in resumable:
            print(f"  Resuming: {state.anime_title} - Episode {state.episode_number}")
            # TODO: Integrate with actual download function
            # For now, just mark as resumed
            resume_manager.update_progress(download_id, state.downloaded_size)
        print("✅ Resume initiated")
        return
    
    # Handle Collection Manager commands
    if collection_cmd is not None:
        handle_collection_command(collection_cmd, get_collection_manager())
        return
    
    # Handle watch status updates
    if watch_status and sarg and iarg is not None:
        """Update watch status for selected anime."""
        if search_response_dict and 'data' in search_response_dict:
            anime_title = search_response_dict['data'][iarg].get('title')
            if anime_title:
                status_map = {
                    'watching': WatchStatus.WATCHING,
                    'completed': WatchStatus.COMPLETED,
                    'on_hold': WatchStatus.ON_HOLD,
                    'dropped': WatchStatus.DROPPED,
                    'plan_to_watch': WatchStatus.PLAN_TO_WATCH
                }
                status = status_map.get(watch_status)
                if status:
                    get_collection_manager().update_watch_status(anime_title, status, watch_progress)
                    print(f"✅ Updated watch status for '{anime_title}': {watch_status}")
                    if watch_progress:
                        print(f"   Progress: {watch_progress} episodes watched")
    
    # Handle rating updates
    if rating and sarg and iarg is not None:
        """Update rating for selected anime."""
        if search_response_dict and 'data' in search_response_dict:
            anime_title = search_response_dict['data'][iarg].get('title')
            if anime_title:
                cm = get_collection_manager()
                entry = cm.get_anime(anime_title)
                if entry:
                    cm.set_rating(anime_title, rating)
                    print(f"⭐ Rated '{anime_title}': {rating}/10")
                else:
                    print(f"⚠️ '{anime_title}' not in collection. Download some episodes first.")
    
    # Search function with filters and fuzzy matching
    if sarg:
        # Configure fuzzy search threshold
        fuzzy_engine.threshold = fuzzy_threshold
        
        records.append(sarg)
        result = lookup(sarg, year_filter=year_filter, status_filter=status_filter, 
                       enable_fuzzy=enable_fuzzy)
        if result is None:
            logging.error("Search failed. Exiting.")
            return
        search_response_dict = result
        state.search_results = search_response_dict

    # Index function
    if iarg is not None:
        if not search_response_dict or 'data' not in search_response_dict or len(search_response_dict['data']) <= iarg:
            logging.error(f"Invalid index {iarg}. Search returned no results or index out of range.")
            return

        # Prefetch episode JSON and anime page HTML using a shared Playwright context
        try:
            selected = search_response_dict['data'][iarg]
            # Set runtime state required by downstream functions
            state.anime_name = selected.get('title')
            state.session_id = selected.get('session')
            state.anime_id = state.session_id
            state.episode_page_format = f'https://animepahe.com/anime/{state.session_id}'
            anime_url_format = f'https://animepahe.com/api?m=release&id={state.session_id}&sort=episode_asc&page=1'

            # Prefetch JSON (episodes) - check both memory and disk cache
            if anime_url_format not in _episode_cache:
                # Try disk cache first
                cached_data = cache_get(anime_url_format, max_age_hours=24)
                if cached_data:
                    try:
                        # Parse cached JSON data
                        episode_data = json.loads(cached_data.decode()) if isinstance(cached_data, bytes) else cached_data
                        _episode_cache[anime_url_format] = episode_data
                        logging.debug("✓ Loaded episode data from disk cache")
                    except Exception as e:
                        logging.debug(f"Failed to parse cached data: {e}")
                        # If cache is corrupted, fetch fresh data
                        json_results = batch_driver_output([anime_url_format], json=True, wait_time=5)
                        if json_results and anime_url_format in json_results and json_results[anime_url_format]:
                            _episode_cache[anime_url_format] = json_results[anime_url_format]
                            cache_set(anime_url_format, json.dumps(json_results[anime_url_format]).encode())
                else:
                    # No cache found, fetch fresh data
                    json_results = batch_driver_output([anime_url_format], json=True, wait_time=5)
                    if json_results and anime_url_format in json_results and json_results[anime_url_format]:
                        _episode_cache[anime_url_format] = json_results[anime_url_format]
                        cache_set(anime_url_format, json.dumps(json_results[anime_url_format]).encode())
            else:
                logging.debug("✓ Episode data already in memory cache, skipping all fetches")

            # Skip HTML prefetch unless specifically needed (e.g., for about command)
            # The anime information display doesn't need HTML content, only episode data
            logging.debug("✓ HTML prefetch skipped (not needed for basic anime info)")
        except Exception as e:
            logging.debug(f"Prefetch skipped due to: {e}")

        # Now render index using the prefetched caches (no extra browser work)
        index_result = index(iarg)
        search_response_dict["data"][iarg]["anime_page"] = state.episode_page_format
        state.search_results = search_response_dict
        records.append(search_response_dict['data'][iarg])
        process_record(records, quiet=True)

    # About function
    if abtarg:
        info = about()
        if info:
            # Don't print the records list, just process it silently
            process_record(records, update=True, quiet=True)
            Banners.anime_info(state.anime_name or "Unknown Anime", info)
        else:
            logging.error("Could not fetch anime information.")

    

    did_download = False
    # Single Download function
    if sdarg:
        records.append(sdarg)
        download(sdarg, res=parg, prefer_dub=args.dub)
        process_record(records, update=True, quiet=True)
        did_download = True

    if starg:
        if iarg is None and not state.session_id:
            print("❌ Error: Streaming requires anime selection. Use -s and -i first.")
            print("💡 Please use -i INDEX to select an anime before streaming.")
            print("   Example: autopahe -s 'anime name' -i 0 -st 1")
            return
        
        records.append(starg)
        # Handle streaming
        if '-' in starg or ',' in starg:
            # Multi-episode streaming
            multi_stream(starg, player=player_arg, resolution=parg, prefer_dub=args.dub)
        else:
            # Single episode streaming
            stream_episode(arg=starg, player=player_arg, res=parg, prefer_dub=args.dub)
        process_record(records, update=True, quiet=True)
        did_download = True

    if larg:
        records.append(larg)
        download(larg, download_file=False, res=parg, prefer_dub=args.dub)
        process_record(records, update=True, quiet=True)


    # Handle batch/season selection
    if batch_season and iarg is not None:
        # Convert season to episode range
        # Assuming 12-13 episodes per season
        season_num = int(batch_season)
        start_ep = (season_num - 1) * 12 + 1
        end_ep = season_num * 12
        mdarg = f"{start_ep}-{end_ep}"
        print(f"📺 Season {season_num}: downloading episodes {start_ep}-{end_ep}")
    
    # Multi Download function
    if mdarg:
        records.append(mdarg)
        multi_download(mdarg, download_file=True, resolution=parg, max_workers=args.workers, enable_notifications=enable_notifications, prefer_dub=args.dub)
        process_record(records, update=True, quiet=True)
        did_download = True

    if mlarg:
        records.append(mlarg)
        multi_download(mlarg, download_file=False, resolution=parg, max_workers=args.workers, enable_notifications=enable_notifications, prefer_dub=args.dub)
        process_record(records, update=True, quiet=True)
        did_download = True

    



    # Record argument
    if rarg:
        if rarg == "view":
            print_all_records()

        elif rarg.isdigit():
            position = int(rarg)
            database = load_database()
            
            if str(position) in database:
                print(json.dumps(database[str(position)], indent=4))
            else:
                print(f"❌ No record found at position {position}")
        else:
            results = search_record(rarg)
            if results:
                print(json.dumps(results, indent=4))
            else:
                print("No matching records found.")

    # Robust records management
    if rcmds:
        try:
            cmd = rcmds[0].lower()
            args_rest = rcmds[1:]
            if cmd == "view":
                print_all_records()
            elif cmd == "search" and len(args_rest) >= 1:
                print(json.dumps(search_record(args_rest[0]), indent=4))
            elif cmd == "delete" and len(args_rest) >= 1:
                delete_record(args_rest[0])
            elif cmd == "progress" and len(args_rest) >= 2:
                update_progress(args_rest[0], args_rest[1])
            elif cmd == "rate" and len(args_rest) >= 2:
                rate_record(args_rest[0], args_rest[1])
            elif cmd == "rename" and len(args_rest) >= 2:
                rename_title(args_rest[0], " ".join(args_rest[1:]))
            elif cmd == "set-keyword" and len(args_rest) >= 2:
                set_keyword(args_rest[0], " ".join(args_rest[1:]))
            elif cmd == "list-status" and len(args_rest) >= 1:
                list_by_status(" ".join(args_rest))
            elif cmd == "export" and len(args_rest) >= 1:
                out = args_rest[0]
                fmt = args_rest[1] if len(args_rest) >= 2 else "json"
                export_records(out, fmt)
            elif cmd == "import" and len(args_rest) >= 1:
                import_records(args_rest[0])
            else:
                print("Invalid -R usage. See --help for examples.")
        except Exception as e:
            print(f"Records error: {e}")

    # Sorting integration (pahesort)
    if sort_cmd:
        base_path = sort_path if sort_path else str(DOWNLOADS)
        if sort_cmd == 'all':
            rename_anime(base_path, animepahe=True, dry_run=sort_dry)
            organize_anime(base_path, animepahe=True, dry_run=sort_dry)
        elif sort_cmd == 'rename':
            rename_anime(base_path, dry_run=sort_dry)
        elif sort_cmd == 'organize':
            organize_anime(base_path, dry_run=sort_dry)

    # Config-driven auto sort after downloads
    if cfg and did_download and str(cfg.get('sort_on_complete', 'false')).lower() in {'1','true','yes','on'}:
        mode = (cfg.get('sort_mode') or 'all').lower()
        base_path = cfg.get('sort_path') or cfg.get('download_dir') or str(DOWNLOADS)
        if mode == 'rename':
            rename_anime(base_path, dry_run=False)
        elif mode == 'organize':
            organize_anime(base_path, dry_run=False)
        else:
            rename_anime(base_path, animepahe=True, dry_run=False)
            organize_anime(base_path, animepahe=True, dry_run=False)

    # Date argument to retrieve execution stats (removed for optimization)
    if dtarg:
        print("Execution stats tracking has been removed for performance optimization.")
        return  # Exit early to avoid unnecessary code execution

    # Summary combining records
    if summary_arg:
        db = load_database()
        if db:
            print(json.dumps(db, indent=4))
            total = len(db)
            completed = sum(1 for v in db.values() if 'Completed' in str(v.get('status','')))
            watching = sum(1 for v in db.values() if 'Watching' in str(v.get('status','')))
            not_started = sum(1 for v in db.values() if 'Not Started' in str(v.get('status','')))
            print(f"\nRecords summary: total={total}, completed={completed}, watching={watching}, not_started={not_started}")
    
    # Clean up browser after all operations are complete
    cleanup_browsers()

#================================================================ End of Arguments Handling =======================================================


def main():
    from cli import run

    run()


# If the script is executed directly, call the main function
if __name__ == '__main__':
    main()
