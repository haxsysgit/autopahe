#! /usr/bin/python3
"""AutoPahe - Anime downloader with advanced features"""

# Standard library imports
import os
import sys
import time
import argparse
import logging
import subprocess
import atexit
from pathlib import Path
from json import loads,dumps
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# Color imports for terminal output
from colorama import Fore, Style, init
init()

# Third-party imports
import requests
from bs4 import BeautifulSoup

# Rich imports for loading spinner
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
import threading
import time

# Get version dynamically from package metadata
try:
    from importlib.metadata import version
    AUTOPAHE_VERSION = version("autopahe")
except ImportError:
    # Fallback for older Python versions
    try:
        import pkg_resources
        AUTOPAHE_VERSION = pkg_resources.get_distribution("autopahe").version
    except:
        # Development fallback
        AUTOPAHE_VERSION = "dev"

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
from ap_core.cache import cache_get, cache_set, cache_clear, display_cache_stats, cache_warm, export_cache, import_cache, get_cache_stats
from ap_core.fuzzy_search import fuzzy_search_anime, fuzzy_engine
from ap_core.resume_manager import resume_manager, can_resume_download
from ap_core.collection_manager import collection_manager, WatchStatus
from ap_core.cookies import clear_cookies
from ap_core.config import load_app_config, write_sample_config

# Local imports - Features
from kwikdown import kwik_download
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
from features.execution_tracker import log_execution_time, reset_run_count, get_execution_stats


########################################### GLOBAL VARIABLES ######################################

# Default download path (OS-specific)
DOWNLOADS = Path.home() / "Downloads"

########################################### LOGGING ################################################

# Configure logging (level will be adjusted based on CLI args)
# Default to ERROR level to suppress WARNING messages for clean user output
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('autopahe.log')
    ]
)


#######################################################################################################################

# Global record list for tracking downloads
records = []

# Global search response dictionary
search_response_dict = {}

# Global anime selection
animepicked = ""

# Global episode page format
episode_page_format = None

# In-memory cache for episode data (faster than disk cache)
_episode_cache = {}
_prefetched_pages = {}

############################################ CLEANUP ##########################################################

# Register cleanup on exit to close any open browsers
atexit.register(cleanup_browsers)




############################################ HELPER FUNCTIONS ##########################################



def setup_environment():
    """First-time setup to make the CLI runnable system-wide."""
    try:
        default_path = Path.home() / '.config' / 'autopahe' / 'config.ini'
        write_sample_config(str(default_path))
        print(f"✓ Sample config written to: {default_path}")
    except Exception as e:
        print(f"Config setup skipped: {e}")
    try:
        os.environ['AUTOPAHE_BROWSER'] = 'chrome'
    except Exception:
        pass
    try:
        # Prefer Chrome CfT to match default; fallback to Chromium
        rc = subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chrome'], check=False)
        if getattr(rc, 'returncode', 1) != 0:
            subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], check=False)
    except Exception:
        print("Playwright not available; skipping browser install.")
    print("Setup complete.")
    return True


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
    global search_response_dict, _from_cache
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
                search_response_dict = loads(search_response)
                print(f"        ✅ Parsed cached JSON successfully")
                logging.debug(f"Found {len(search_response_dict.get('data', []))} cached results")
                
                # Apply filters to cached results if provided
                results = search_response_dict['data']
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
                
                # Update dict with filtered results
                search_response_dict['data'] = results
                
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
            search_response_dict = loads(search_response)
            logging.debug(f"Found {len(search_response_dict.get('data', []))} results")
        else:
            # Step 3: Only use Playwright as last resort (slow, resource intensive)
            logging.warning("Direct API failed, falling back to Playwright...")
            with LoadingSpinner("Loading browser for search...", "dots") as spinner:
                spinner.update_text("Launching browser...")
                search_response = driver_output(api_url, driver=True, json=True, wait_time=5)
                if search_response:
                    search_response_dict = search_response
                    # Cache the Playwright results as JSON bytes for future instant access
                    cache_set(api_url, dumps(search_response_dict).encode())
                    logging.debug(f"Playwright fallback succeeded and cached")
                    # Don't close browser yet - might need it for index/about operations
                else:
                    logging.error("All methods failed to retrieve search results")
                    search_response_dict = {'data': []}

    except requests.exceptions.RequestException as e:
        # Network error - try Playwright fallback
        logging.warning(f"Network error ({e}), trying Playwright...")
        try:
            search_response = driver_output(api_url, driver=True, json=True, wait_time=5)
            if search_response:
                search_response_dict = search_response
                # Cache the Playwright results as JSON bytes for future instant access
                cache_set(api_url, dumps(search_response_dict).encode())
            else:
                search_response_dict = {'data': []}
        except Exception:
            search_response_dict = {'data': []}
    except Exception as e:
        logging.warning(f"Parsing/API error ({e}); trying Playwright fallback...")
        try:
            search_response = driver_output(api_url, driver=True, json=True, wait_time=5)
            if search_response:
                search_response_dict = search_response
                # Cache the Playwright results as JSON bytes for future instant access
                cache_set(api_url, dumps(search_response_dict).encode())
            else:
                search_response_dict = {'data': []}
        except Exception:
            search_response_dict = {'data': []}

    # Check if results exist
    if not search_response_dict or 'data' not in search_response_dict or not search_response_dict['data']:
        logging.error("No results found. Please try a different search term.")
        print("\n❌ No anime found matching your search.\n")
        return None
    
    # Debug: Show we have results
    logging.info(f"Processing {len(search_response_dict['data'])} search results")
    
    # Apply filters if provided
    results = search_response_dict['data']
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
    
    # Update dict with filtered results
    search_response_dict['data'] = results
    
    if not results:
        print(f"\n❌ No anime found matching your search with the given filters.\n")
        print("💡 Tips:")
        print("   - Try different spelling or formatting")
        print("   - Check if the anime name is correct")
        print("   - Try searching with fewer keywords\n")
        return None
    
    resultlen = len(search_response_dict['data'])
    # Display results using structured design
    from_cache = '_from_cache' in globals() and _from_cache
    Banners.search_results(search_response_dict['data'], from_cache=from_cache)
    
    return search_response_dict




# =========================================== handling the single download utility ============================
    

def index(arg):
    """Display information about the selected anime and prepare for downloads.
    
    Args:
        arg: Index of the anime in search results
    """
    print("\n")  # Don't clear screen, just add spacing

    global jsonpage_dict, session_id, animepicked, episode_page_format, search_response_dict

    try:
        # Get anime data from search results
        anime_data = search_response_dict['data'][int(arg)]
        
        # Set global variables
        animepicked = anime_data['title']
        session_id = anime_data['session']
        episode_page_format = f'https://animepahe.com/anime/{session_id}'
        
        # Get episode list
        anime_url_format = f'https://animepahe.com/api?m=release&id={session_id}&sort=episode_asc&page=1'
        
        # Check in-memory cache first (fastest)
        if anime_url_format in _episode_cache:
            jsonpage_dict = _episode_cache[anime_url_format]
            logging.debug("✓ Loaded episode list from memory cache")
        else:
            # Initialize jsonpage_dict to avoid undefined error
            jsonpage_dict = None
            
            # Try disk cache next
            cached = cache_get(anime_url_format, max_age_hours=12)  # 12 hours for episode data
            if cached:
                jsonpage_dict = cached
                logging.debug("✓ Loaded episode list from disk cache")
                # Store in memory cache for even faster access
                _episode_cache[anime_url_format] = jsonpage_dict
            else:
                # Try direct HTTP request first (faster, no browser)
                try:
                    session = get_request_session()
                    response = session.get(anime_url_format, timeout=10)
                    if response.status_code == 200:
                        jsonpage_dict = response.json()
                        logging.debug("Successfully fetched episode list via HTTP")
                        # Cache the result
                        _episode_cache[anime_url_format] = jsonpage_dict
                        cache_set(anime_url_format, jsonpage_dict)
                except Exception as e:
                    logging.warning(f"HTTP request failed: {e}")
                    # Fall back to Playwright if HTTP fails
                    logging.info("Falling back to Playwright for episode list...")
                    jsonpage_dict = driver_output(anime_url_format, driver=True, json=True, wait_time=5)
                    if jsonpage_dict:
                        # Cache the result even from Playwright
                        _episode_cache[anime_url_format] = jsonpage_dict
                        cache_set(anime_url_format, jsonpage_dict)
        
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
                'homepage': episode_page_format,
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
                'homepage': episode_page_format,
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
        if 'search_response_dict' not in globals() or not search_response_dict:
            logging.error("No search results available. Please perform a search first.")
        return None

def about():
        # Prefer prefetched HTML if available
        html = _prefetched_pages.get(episode_page_format)
        if not html:
            html = driver_output(episode_page_format, driver=True, content=True)
        soup = BeautifulSoup(html, 'lxml')
        abt = soup.select('.anime-synopsis')
        return abt[0].text.strip() if abt else ''





def download(arg=1, download_file=True, res = "720"):
    """
    Download the specified episode by navigating with Playwright and extracting the download link.
    """
    
    try:
        # Convert the argument to an integer to ensure it is in the correct format
        arg = int(arg)

        # Retrieve the session ID for the selected episode from the global jsonpage_dict
        episode_session = jsonpage_dict['data'][arg - 1]['session']

        # Construct the URL for the stream page for the specific episode using the session ID
        stream_page_url = f'https://animepahe.com/play/{session_id}/{episode_session}'

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
                # Filter by min resolution and exclude English dubs
                if resolution >= min_resolution and 'eng' not in text.lower():
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
            # Fallback to HTML parse
            page.wait_for_timeout(5000)
            kwik_page = page.content()
            kwik_cx = BeautifulSoup(kwik_page, 'lxml')
            a = kwik_cx.find('a', class_='redirect')
            kwik = a['href'] if a else None
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
        Banners.download_progress(animepicked, arg)

        # Add download to resume manager for tracking
        download_id = resume_manager.add_download(
            anime_title=animepicked,
            episode_number=str(arg),
            download_url=kwik,
            file_path=str(DOWNLOADS / f"{animepicked}_Episode_{arg}.mp4"),
            quality=res
        )

        # Trigger the download process using the kwik link and specify the download directory
        result = kwik_download(url=kwik, dpath=DOWNLOADS, ep=arg, animename=animepicked)
        
        # Track download in collection manager
        if result is not False:  # kwik_download returns False on failure
            # Mark download as completed in resume manager
            resume_manager.mark_completed(download_id)
            
            # Add to collection manager
            entry = collection_manager.add_anime(animepicked)
            episode_file = str(DOWNLOADS / f"{animepicked}_Episode_{arg}.mp4")
            collection_manager.add_episode_file(animepicked, arg, episode_file, organize=False)
            Banners.success_message(f"Added episode {arg} to collection for '{animepicked}'")
        else:
            # Mark download as failed in resume manager
            resume_manager.mark_failed(download_id, "Download failed")
    else:
        return kwik


                
    # ========================================== Multi Download Utility ==========================================

    
def multi_download(arg: str, download_file=True, resolution="720", max_workers=1, enable_notifications=False):
    """
    Downloads multiple episodes sequentially.
    Note: Parallel downloads disabled due to Playwright threading incompatibility.
    Playwright's sync API uses greenlets which cannot be shared across ThreadPoolExecutor threads.
    """
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
            download(arg=ep, download_file=download_file, res=str(resolution))
            completed += 1
            Banners.success_message(f"Episode {ep} completed successfully ({completed}/{len(eps)})")
        except Exception as e:
            failed.append(ep)
            logging.error(f"Episode {ep} failed: {e}")
    
    # Send notification if enabled
    if enable_notifications and download_file:
        if failed:
            notify_download_failed(animepicked, f"Failed: {', '.join(map(str, failed))}")
        else:
            notify_download_complete(animepicked, arg)




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


def command_main(args):
    global barg
    barg = args.browser  # Selected browser
    sarg = args.search  # Search query for anime
    iarg = args.index  # Index of selected anime
    sdarg = args.single_download  # Argument for single episode download
    mdarg = args.multi_download  # Argument for multi-episode download
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

    if cfg and cfg.get('download_dir'):
        DOWNLOADS = Path(cfg['download_dir'])
    
    # Configure resume manager
    resume_manager.max_retries = max_retries

    # Reset the run count
    reset_run_count()

    # Note: Browser is only launched when actually needed (during downloads)
    # This avoids unnecessary resource usage and startup delays
    
    # Handle cache commands
    if cache_cmd:
        if cache_cmd == 'clear':
            cache_clear()
            clear_cookies()
            print("✓ Cache and cookies cleared")
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
    if collection_cmd:
        """Execute collection management commands."""
        if collection_cmd == 'stats':
            # Display collection statistics
            stats = collection_manager.get_statistics()
            print(f"\n📚 Collection Statistics:")
            print(f"  Total Anime: {stats['total_anime']}")
            print(f"  Total Episodes: {stats['total_episodes']}")
            print(f"  Total Size: {stats['total_size_gb']:.2f} GB")
            print(f"  Completion Rate: {stats['completion_rate']:.1f}%")
            print(f"  Missing Episodes: {stats['missing_episodes']}")
            if stats['average_rating'] > 0:
                print(f"  Average Rating: {stats['average_rating']:.1f}/10")
            
            print(f"\n📊 Watch Status:")
            for status, count in stats['watch_status'].items():
                if count > 0:
                    print(f"  {status.replace('_', ' ').title()}: {count}")
            
            if stats['top_rated']:
                print(f"\n⭐ Top Rated:")
                for title, rating in stats['top_rated']:
                    print(f"  • {title}: {rating}/10")
            
            if stats['recently_watched']:
                print(f"\n📅 Recently Watched:")
                for title, date in stats['recently_watched'][:3]:
                    print(f"  • {title}")
            return
        
        elif collection_cmd == 'organize':
            # Organize collection files
            print("\n🗂️ Organizing collection files...")
            for entry in collection_manager.collection.values():
                for ep_num, file_path in entry.file_paths.items():
                    if os.path.exists(file_path):
                        new_path = collection_manager.add_episode_file(
                            entry.title, ep_num, file_path, organize=True
                        )
                        if new_path != file_path:
                            print(f"  ✓ Organized: {entry.title} - Episode {ep_num}")
            print("✅ Collection organized")
            return
        
        elif collection_cmd == 'duplicates':
            # Find and optionally remove duplicate files
            print("\n🔍 Detecting duplicate files...")
            duplicates = collection_manager.detect_duplicates()
            if duplicates:
                print(f"Found {len(duplicates)} sets of duplicates:")
                for file_hash, paths in duplicates[:5]:  # Show first 5
                    print(f"  • {len(paths)} copies of same file:")
                    for path in paths[:2]:  # Show first 2 paths
                        print(f"    - {os.path.basename(path)}")
                
                # Offer to clean duplicates
                response = input("\nRemove duplicates (keep organized versions)? (y/n): ")
                if response.lower() == 'y':
                    removed = collection_manager.cleanup_duplicates(keep_organized=True)
                    print(f"✅ Removed {removed} duplicate files")
            else:
                print("✅ No duplicates found")
            return
        
        elif collection_cmd == 'export':
            # Export collection
            export_path = collection_path or 'collection_export.json'
            collection_manager.export_collection(export_path, format='json', include_stats=True)
            print(f"✅ Collection exported to: {export_path}")
            return
        
        elif collection_cmd == 'import':
            # Import collection (would need implementation)
            print("⚠️ Import functionality coming soon")
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
                    collection_manager.update_watch_status(anime_title, status, watch_progress)
                    print(f"✅ Updated watch status for '{anime_title}': {watch_status}")
                    if watch_progress:
                        print(f"   Progress: {watch_progress} episodes watched")
    
    # Handle rating updates
    if rating and sarg and iarg is not None:
        """Update rating for selected anime."""
        if search_response_dict and 'data' in search_response_dict:
            anime_title = search_response_dict['data'][iarg].get('title')
            if anime_title:
                if anime_title in collection_manager.collection:
                    entry = collection_manager.collection[anime_title]
                    entry.rating = rating
                    collection_manager.save_collection()
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

    # Index function
    if iarg is not None:
        if not search_response_dict or 'data' not in search_response_dict or len(search_response_dict['data']) <= iarg:
            logging.error(f"Invalid index {iarg}. Search returned no results or index out of range.")
            return

        # Prefetch episode JSON and anime page HTML using a shared Playwright context
        try:
            selected = search_response_dict['data'][iarg]
            # Set globals required by downstream functions
            global session_id, episode_page_format, animepicked
            animepicked = selected.get('title')
            session_id = selected.get('session')
            episode_page_format = f'https://animepahe.com/anime/{session_id}'
            anime_url_format = f'https://animepahe.com/api?m=release&id={session_id}&sort=episode_asc&page=1'

            # Prefetch JSON (episodes)
            json_results = batch_driver_output([anime_url_format], json=True, wait_time=5)
            if json_results and anime_url_format in json_results and json_results[anime_url_format]:
                _episode_cache[anime_url_format] = json_results[anime_url_format]
                cache_set(anime_url_format, json_results[anime_url_format])

            # Prefetch HTML (about page)
            html_results = batch_driver_output([episode_page_format], content=True, wait_time=5)
            if html_results and episode_page_format in html_results and html_results[episode_page_format]:
                _prefetched_pages[episode_page_format] = html_results[episode_page_format]
        except Exception as e:
            logging.debug(f"Prefetch skipped due to: {e}")

        # Now render index using the prefetched caches (no extra browser work)
        index(iarg)
        search_response_dict["data"][iarg]["anime_page"] = episode_page_format
        records.append(search_response_dict['data'][iarg])
        process_record(records, quiet=True)

    # About function
    if abtarg:
        info = about()
        if info:
            # Don't print the records list, just process it silently
            process_record(records, update=True, quiet=True)
            Banners.anime_info(animepicked, info)
        else:
            logging.error("Could not fetch anime information.")

    

    did_download = False
    # Single Download function
    if sdarg:
        records.append(sdarg)
        download(sdarg,res=parg)
        process_record(records, update=True, quiet=True)
        did_download = True

    if larg:
        records.append(larg)
        download(larg , download_file=False,res=parg)
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
        multi_download(mdarg,download_file=True,resolution=parg, max_workers=args.workers, enable_notifications=enable_notifications)
        process_record(records, update=True, quiet=True)
        did_download = True

    if mlarg:
        records.append(mlarg)
        multi_download(mlarg,download_file=False,resolution=parg, max_workers=args.workers, enable_notifications=enable_notifications)
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
                print(dumps(database[str(position)], indent=4))
            else:
                print(f"❌ No record found at position {position}")
        else:
            results = search_record(rarg)
            if results:
                print(dumps(results, indent=4))
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
                print(dumps(search_record(args_rest[0]), indent=4))
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

    # Date argument to retrieve execution stats
    if dtarg:
        stats = get_execution_stats(dtarg)
        # print(len(stats))
        # print(stats.keys())

        
        if len(stats) == 1:
            for stat in stats:
                # Convert total time from seconds to minutes
                total_time_minutes = stats[stat]['total_time_mins']

                total_time_hours = stats[stat]['total_time_hours']

                average_time_mins = stats[stat]['average_time_mins']

                average_time_hours = stats[stat]['average_time_hours']
                
                print(f"\nExecution stat for '{dtarg}' -->>\n")

                print(f"\n1.) Total Runs: {stats[stat]['run_count']}")
                print(f"\n2.) Total Execution Time (Minutes): {total_time_minutes:.2f} minutes")  # Print in minutes
                print(f"\n3.) Total Execution Time (Minutes): {total_time_hours:.2f} hours")  # Print in hours
                print(f"\n4.) Average Execution Time (Minutes): {average_time_mins:.2f} minutes")  # Print in minutes
                print(f"\n5.) Average Execution Time (Hours): {average_time_hours:.2f} hours")  # Print in hours 

        elif len(stats) > 1:
            for stat in stats:
                # Convert total time from seconds to minutes
                total_time_minutes = round(stats[stat]['total_time_mins'],1)

                total_time_hours = round(stats[stat]['total_time_hours'])

                average_time_mins = round(stats[stat]['average_time_mins'])

                average_time_hours = round(stats[stat]['average_time_hours']) 
                               
                print(f"\n\nExecution stats for '{stat}' -->>")

                print(f"\n1.) Total Runs: {stats[stat]['run_count']}")
                print(f"\n2.) Total Execution Time (Minutes): {total_time_minutes:.2f} minutes")  # Print in minutes
                print(f"\n3.) Total Execution Time (Minutes): {total_time_hours:.2f} hours")  # Print in hours
                print(f"\n4.) Average Execution Time (Minutes): {average_time_mins:.2f} minutes")  # Print in minutes
                print(f"\n5.) Average Execution Time (Hours): {average_time_hours:.2f} hours")  # Print in hours 

                print("=============================================================================")
        else:
            print(f"\n\nNo execution data found for '{dtarg}'.")

    # Summary combining execution stats and records
    if summary_arg:
        stats = get_execution_stats(summary_arg)
        if stats:
            print(dumps(stats, indent=4))
        db = load_database()
        total = len(db)
        completed = sum(1 for v in db.values() if 'Completed' in str(v.get('status','')))
        watching = sum(1 for v in db.values() if 'Watching' in str(v.get('status','')))
        not_started = sum(1 for v in db.values() if 'Not Started' in str(v.get('status','')))
        print(f"\nRecords summary: total={total}, completed={completed}, watching={watching}, not_started={not_started}")
    
    # Clean up browser after all operations are complete
    cleanup_browsers()



# Main entry point for the script that processes arguments and triggers the appropriate actions
def main():
    # Reset the run count to start fresh
    reset_run_count()

    # Record the start time of the execution
    start_time = time.perf_counter()

    # Pre-parse config flags
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument('--config', help='Path to a config INI file')
    pre.add_argument('--write-config', nargs='?', const='', help='Write a sample config to the given path (or default) and exit')
    pre_args, remaining = pre.parse_known_args()

    # Load configuration
    cfg, cfg_path = load_app_config(pre_args.config)

    # Handle write-config
    if pre_args.write_config is not None:
        default_path = str(Path.home() / '.config' / 'autopahe' / 'config.ini')
        target = pre_args.write_config or default_path
        written = write_sample_config(target)
        print(f"Sample config written to: {written}")
        return

    # Stash config globally for command_main
    global APP_CONFIG
    APP_CONFIG = cfg

    # Set default browser from config or environment
    default_browser = cfg.get('browser', 'chrome')  # Config takes precedence over env
    # Only use env if no config setting
    if not cfg.get('browser') and os.environ.get('AUTOPAHE_BROWSER'):
        default_browser = os.environ.get('AUTOPAHE_BROWSER')
    
    # Argument parser setup to handle command-line inputs
    parser = argparse.ArgumentParser(description='AutoPahe - Anime downloader with advanced features')
    parser.add_argument('-v', '--version', action='store_true', help='Display AutoPahe version and exit')
    parser.add_argument('-b', '--browser', default=default_browser, 
                      choices=['chrome', 'chromium', 'firefox'],
                      help=f'Select Playwright browser (default: {default_browser})')
    parser.add_argument('-s', '--search', type=str, help='Search for an anime by name')
    parser.add_argument('-i', '--index', type=int, help='Specify the index of the desired anime from the search results')
    parser.add_argument('-d', '--single_download', type=int, help='Download a single episode of an anime')
    parser.add_argument('-md', '--multi_download', help='Download multiple episodes of an anime (e.g., 1-12)')
    parser.add_argument('-l', '--link', help='Display the link to the kwik download page')
    parser.add_argument('-ml', '--multilinks', help='Display multiple links to the kwik download pages')
    parser.add_argument('-a', '--about', help='Output an overview of the anime', action='store_true')
    parser.add_argument('-p', '--resolution', type=str, 
                      default=str(cfg.get('resolution', '720')), 
                      choices=['360', '480', '720', '1080', 'best', 'worst'],
                      help='Video resolution for downloads (default: 720)')
    parser.add_argument('-w', '--workers', type=int, 
                      default=int(cfg.get('workers', '1')), 
                      help='Number of parallel workers for multi-episode downloads (use >1 with caution)')
    
    # Records management
    parser.add_argument('-r', '--record', help='Interact with the records/database (view, [index], [keyword])')
    parser.add_argument('-R', '--records', nargs='+', 
                      help='Robust records management. Examples: -R view | -R search naruto | -R delete 3 | -R progress 3 27 | -R rate 3 8.5 | -R rename 3 "New Title" | -R set-keyword 3 naruto | -R list-status completed | -R export out.json json | -R import in.json')
    
    # File organization
    parser.add_argument('--sort', choices=['all', 'rename', 'organize'], 
                      help='Sort downloaded files (integrates pahesort)')
    parser.add_argument('--sort-path', help='Path to sort; defaults to Downloads')
    parser.add_argument('--sort-dry-run', action='store_true', help='Dry-run sorting (no changes)')
    
    # Additional features
    parser.add_argument('--summary', help='Show execution stats and records summary')
    parser.add_argument('--year', type=int, help='Filter search results by year (e.g., 2020)')
    parser.add_argument('--status', type=str, help='Filter search results by status (e.g., "Finished Airing")')
    parser.add_argument('--season', type=int, help='Download entire season (12-13 eps). Example: --season 1 downloads eps 1-12')
    parser.add_argument('--notify', action='store_true', help='Enable desktop notifications on download complete/fail')
    parser.add_argument('--cache', choices=['clear', 'stats'], help='Cache management: clear (remove all) or stats (show info)')
    parser.add_argument('--setup', action='store_true', help='Initial setup: write config and install browser')
    
    # Smart Search Features
    parser.add_argument('--no-fuzzy', action='store_true', 
                      help='Disable fuzzy search (exact match only)')
    parser.add_argument('--fuzzy-threshold', type=float, default=0.6, 
                      help='Fuzzy search similarity threshold (0.0-1.0, default: 0.6)')
    
    # Resume System Features
    parser.add_argument('--resume', action='store_true',
                      help='Resume interrupted downloads from previous session')
    parser.add_argument('--resume-stats', action='store_true',
                      help='Show download resume statistics')
    parser.add_argument('--max-retries', type=int, default=3,
                      help='Maximum retry attempts for failed downloads (default: 3)')
    
    # Collection Manager Features
    parser.add_argument('--collection', choices=['stats', 'organize', 'duplicates', 'export', 'import'],
                      help='Collection management: stats, organize files, find duplicates, export/import')
    parser.add_argument('--collection-path', type=str,
                      help='Path for collection operations (export/import file path)')
    parser.add_argument('--watch-status', choices=['watching', 'completed', 'on_hold', 'dropped', 'plan_to_watch'],
                      help='Update watch status for an anime (use with -s and -i)')
    parser.add_argument('--watch-progress', type=int,
                      help='Update watch progress (episodes watched) for an anime')
    parser.add_argument('--rate', type=int, choices=range(1, 11), metavar='[1-10]',
                      help='Rate an anime (1-10, use with -s and -i)')
    
    # Verbosity flags
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging (DEBUG level)')
    parser.add_argument('--quiet', action='store_true', help='Minimal logging (WARNING level only)')
    
    # Repeat config flags for help
    parser.add_argument('--config', help='Path to a config INI file')
    parser.add_argument('--write-config', nargs='?', const='', help='Write a sample config to the given path (or default) and exit')
    
    # Adding help message for exec_data
    parser.add_argument(
        '-dt', '--execution_data',
        help=(
            "Retrieve execution data for a specific date or date range. "
            "Format : YYYY-MM-DD (year-month-day)"
            "Examples: ['today', 'yesterday', 'last 3 days', 'last week', "
            "'this week', '2 weeks ago', 'last month', '1 month ago'.]"
        )
    )

    # Parse the command-line arguments
    args = parser.parse_args(remaining)

    # Handle version argument
    if args.version:
        print(f"AutoPahe v{AUTOPAHE_VERSION}")
        print("⚡ Anime Downloader with Advanced Features ⚡")
        return

    # Set browser env after final parse
    try:
        os.environ['AUTOPAHE_BROWSER'] = (args.browser or default_browser)
    except Exception:
        pass

    # One-shot setup
    if getattr(args, 'setup', False):
        setup_environment()
        return
    
    # Configure logging level based on --verbose/--quiet
    # Default to ERROR level to suppress WARNING messages for clean user output
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Verbose logging enabled")
    else:
        # Default: ERROR level (only errors) - completely clean user output
        logging.getLogger().setLevel(logging.ERROR)

    # AUTOPAHE_BROWSER already set above from args/defaults

    # Determine if the user provided any actionable flags (ignore defaults)
    has_action = any([
        bool(args.search),
        args.index is not None,
        args.single_download is not None,
        bool(args.multi_download),
        bool(args.link),
        bool(args.multilinks),
        bool(args.about),
        bool(args.record),
        bool(args.records),
        bool(args.sort),
        bool(args.sort_path),
        bool(args.sort_dry_run),
        bool(args.cache),
        bool(args.summary),
        args.year is not None,
        bool(args.status),
        args.season is not None,
        bool(args.notify),
        bool(args.execution_data),
        bool(args.config),
        args.write_config is not None,
        # New feature flags
        bool(args.resume),
        bool(args.resume_stats),
        bool(args.collection),
        bool(args.watch_status),
        args.watch_progress is not None,
        args.rate is not None,
    ])

    # If actionable flags are provided, process them; otherwise go interactive
    if has_action:
        try:
            Banners.header()
        except Exception:
            pass
        command_main(args)
    else:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except Exception:
            pass
        try:
            Banners.header()
        except Exception:
            pass
        print("\nNo arguments provided. Try these options:\n")
        print("  📺 BASIC OPERATIONS:")
        print("  -s, --search <query>          Search for anime (typos auto-corrected!)")
        print("  -i, --index <n>               Select anime index from search results")
        print("  -d, --single_download <ep>    Download a single episode")
        print("  -md, --multi_download <spec>  Download multiple episodes (e.g., 1-5 or 1,3,5)")
        print("  -a, --about                   Show anime overview")
        print("  -p, --resolution <720|1080>   Choose resolution")
        print("  -w, --workers <n>             Parallel downloads (use >1 with caution)")
        
        print("\n  🎯 SMART FEATURES (NEW!):")
        print("      --no-fuzzy                Disable fuzzy search (exact match only)")
        print("      --resume                  Resume interrupted downloads")
        print("      --resume-stats            Show download resume statistics")
        print("      --collection stats        View your anime collection statistics")
        print("      --collection organize     Organize collection files into folders")
        print("      --collection duplicates   Find and remove duplicate files")
        print("      --watch-status <status>   Update watch status (watching/completed/etc)")
        print("      --rate <1-10>             Rate an anime")
        
        print("\n  🔧 MANAGEMENT:")
        print("  -R, --records [...]           Manage records (view/search/delete/...)")
        print("      --sort [all|rename|organize]  Sort downloaded files")
        print("      --cache [clear|stats]     Manage cache and cookies")
        print("      --year <YYYY>             Filter by year")
        print("      --status <text>           Filter by status (e.g., Finished Airing)")
        print("      --season <n>              Download a whole season (12-13 eps)")
        print("      --notify                  Enable desktop notifications")
        print("      --verbose | --quiet       Adjust logging verbosity\n")
        print("Launching Interactive Mode...\n")
        interactive_main()

    # Log the execution time once the script has finished
    log_execution_time(start_time)





#================================================================ End of Arguments Handling =======================================================

# If the script is executed directly, call the main function
if __name__ == '__main__':
    main()

