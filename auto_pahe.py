#! /usr/bin/python3
"""AutoPahe - Anime downloader with advanced features"""

# Standard library imports
import os
import time
import argparse
import logging
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

# Local imports - Core functionality
from ap_core.banners import Banners, n
from ap_core.browser import driver_output, cleanup_browsers, get_request_session, get_pw_context, batch_driver_output
from ap_core.config import load_app_config, write_sample_config
from ap_core.cache import cache_get, cache_set, cache_clear, get_cache_stats
from ap_core.notifications import notify_download_complete, notify_download_failed
from ap_core.cookies import clear_cookies

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
logging.basicConfig(
    level=logging.INFO,
    format='\n%(asctime)s - %(levelname)s - %(message)s',
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
animepicked = None
episode_page_format = None

# In-memory cache for episode data (faster than disk cache)
_episode_cache = {}
_prefetched_pages = {}

############################################ CLEANUP ##########################################################

# Register cleanup on exit to close any open browsers
atexit.register(cleanup_browsers)




############################################ HELPER FUNCTIONS ##########################################



def lookup(arg, year_filter=None, status_filter=None):
    """Search for anime using AnimePahe API with filters.
    
    Tries disk cache first, then direct HTTP request, falls back to Playwright only if needed.
    This avoids unnecessary browser launches for better performance.
    
    Args:
        arg: Search query string
        year_filter: Optional year to filter results
        status_filter: Optional status string to filter results
    """
    global search_response_dict, _from_cache
    _from_cache = False

    # Display search banner
    Banners.search(arg)
    print()  # Use regular print instead of n() which might clear screen

    # API endpoint for search
    api_url = f'https://animepahe.si/api?m=search&q={arg}'
    search_response = None

    try:
        # Step 1: Check disk cache (24-hour expiry for better performance)
        cached = cache_get(api_url, max_age_hours=24)
        if cached:
            search_response = cached
            _from_cache = True
            logging.debug("✓ Loaded from disk cache")
        else:
            # Step 2: Try direct HTTP request (fast, no browser needed)
            logging.debug("Fetching from API...")
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                search_response = response.content
                # Save to disk cache for future use
                cache_set(api_url, search_response)
                logging.debug("✓ Fetched from API and cached")
            else:
                logging.warning(f"API returned status {response.status_code}")

        # Parse response if we got one
        if search_response:
            search_response_dict = loads(search_response)
            logging.debug(f"Found {len(search_response_dict.get('data', []))} results")
        else:
            # Step 3: Only use Playwright as last resort (slow, resource intensive)
            logging.warning("Direct API failed, falling back to Playwright...")
            search_response = driver_output(api_url, driver=True, json=True, wait_time=5)
            if search_response:
                search_response_dict = search_response
                logging.debug(f"Playwright fallback succeeded")
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
            else:
                search_response_dict = {'data': []}
        except Exception:
            search_response_dict = {'data': []}
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        search_response_dict = {'data': []}

    # Check if results exist
    if not search_response_dict or 'data' not in search_response_dict or not search_response_dict['data']:
        Banners.header()
        logging.error("No results found. Please try a different search term.")
        print("\n❌ No anime found matching your search.\n")
        return
    
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
        Banners.header()
        print(f"\n❌ No anime found matching your search with the given filters.\n")
        print("💡 Tips:")
        print("   - Try different spelling or formatting")
        print("   - Check if the anime name is correct")
        print("   - Try searching with fewer keywords\n")
        return None
    
    resultlen = len(search_response_dict['data'])
    print()  # Add spacing instead of clearing screen
    
    # Check if data came from cache
    cache_indicator = ""
    if '_from_cache' in globals() and _from_cache:
        cache_indicator = f" {Fore.GREEN}⚡{Style.RESET_ALL}"
    
    print(f'{Fore.GREEN}🎬 Found {resultlen} results{cache_indicator}{Style.RESET_ALL} {Fore.CYAN}--->{Style.RESET_ALL}')
    print()

    for el in range(len(search_response_dict['data'])):
        name = search_response_dict['data'][el]['title']
        episodenum = search_response_dict['data'][el]['episodes']
        status = search_response_dict['data'][el]['status']
        year = search_response_dict['data'][el]['year']
        anime_type = search_response_dict['data'][el].get('type', 'N/A')
        
        # Type emoji mapping
        type_emoji = {
            'TV': '📺',
            'Movie': '🎬',
            'ONA': '💻',
            'OVA': '📀'
        }.get(anime_type, '📺')
        
        # Status color mapping
        status_color = {
            'Finished Airing': Fore.GREEN,
            'Currently Airing': Fore.YELLOW,
            'Not yet aired': Fore.RED
        }.get(str(status), Fore.WHITE)
        
        print(f'{Fore.MAGENTA}[{el}]{Style.RESET_ALL} {type_emoji} {Fore.CYAN}{name}{Style.RESET_ALL}')
        print(f'   {Fore.BLUE}├─ Episodes:{Style.RESET_ALL} {Fore.YELLOW}{episodenum}{Style.RESET_ALL}')
        print(f'   {Fore.BLUE}├─ Status:{Style.RESET_ALL} {status_color}{status}{Style.RESET_ALL}')
        print(f'   {Fore.BLUE}├─ Year:{Style.RESET_ALL} {Fore.YELLOW}{year}{Style.RESET_ALL}')
        print(f'   {Fore.BLUE}└─ Type:{Style.RESET_ALL} {Fore.YELLOW}{anime_type}{Style.RESET_ALL}')
        print()

    print()  # Add spacing instead of clearing screen
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
                'episode_count': len(jsonpage_dict.get('data', [])),
                'first_episode': jsonpage_dict['data'][0]['episode'] if jsonpage_dict.get('data') else 'N/A',
                'last_episode': jsonpage_dict['data'][-1]['episode'] if jsonpage_dict.get('data') else 'N/A'
            }
        
        # Display anime info without clearing the screen to preserve search results
        Banners.select(
            anime=anime_info['title'],
            eps=anime_info['episodes'],
            anipage=episode_page_format,
            year=anime_info['year'],
            atype=anime_info['type'],
            status=anime_info['status'],
            img=anime_info['image']
        )
        
        # Display episode range information only if we have valid data
        if jsonpage_dict and 'data' in jsonpage_dict and jsonpage_dict['data']:
            print(f"\n{Fore.MAGENTA}📺 Available Episodes:{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}First:{Style.RESET_ALL} {anime_info['first_episode']}")
            print(f"   {Fore.GREEN}Last:{Style.RESET_ALL}  {anime_info['last_episode']}")
            print(f"   {Fore.GREEN}Total:{Style.RESET_ALL} {anime_info['episode_count']} episodes")
        else:
            print(f"\n{Fore.YELLOW}⚠️  Episode information temporarily unavailable{Style.RESET_ALL}")
        
        # Print available commands with better styling
        print(f"\n{Fore.BLUE}🔧 Available Commands:{Style.RESET_ALL}")
        print(f"   {Fore.CYAN}➤ Download:{Style.RESET_ALL} {Fore.YELLOW}-d{Style.RESET_ALL} <episode_number>  (e.g., {Fore.YELLOW}-d 1{Style.RESET_ALL})")
        print(f"   {Fore.CYAN}➤ Multi-download:{Style.RESET_ALL} {Fore.YELLOW}-md{Style.RESET_ALL} <range>  (e.g., {Fore.YELLOW}-md 1-12{Style.RESET_ALL})")
        print(f"   {Fore.CYAN}➤ Get links:{Style.RESET_ALL} {Fore.YELLOW}-l{Style.RESET_ALL} <episode>  (e.g., {Fore.YELLOW}-l 1{Style.RESET_ALL})")
        print(f"   {Fore.CYAN}➤ Back to search:{Style.RESET_ALL} {Fore.YELLOW}-s{Style.RESET_ALL} <new_search>")
        print()
        
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

        # Navigate with shared Playwright context and extract links then the kwik page
        browser_choice = (os.environ.get('AUTOPAHE_BROWSER') or 'chrome').lower()
        context = get_pw_context(browser_choice, headless=False)
        if context is None:
            logging.error("Playwright context not available")
            return
        page = context.new_page()
        page.goto(stream_page_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(15000)
        stream_page_soup = BeautifulSoup(page.content(), 'lxml')

        # Find all the download links in the page using the specified class name
        dload = stream_page_soup.find_all('a', class_='dropdown-item', target="_blank")

        # Filters download links with resolution >= 720p and excludes 'eng' versions,
        # then sorts them starting from 720p up to the highest resolution available.
        linkpahe = sorted(
            [
                BeautifulSoup(str(link), 'html.parser').a['href']
                for link in dload
                if (
                    (m := re.search(r'(\d{3,4})p', str(link))) and 
                    int(m.group(1)) >= 720 and 
                    'eng' not in str(link).lower()
                )
            ],
            key=lambda url: int(re.search(r'(\d{3,4})p', url).group(1)) if re.search(r'(\d{3,4})p', url) else float('inf')
        )

        print(linkpahe)

        # If a valid download link is found, proceed with the next steps
        if not linkpahe:
            page.close()
            raise ValueError(f"No valid download link found for episode {arg}")

        # Navigate to the selected download link
        res = str(res)
        if res == '720':
            page.goto(linkpahe[0], wait_until='domcontentloaded', timeout=60000)
        elif res == '1080':
            page.goto(linkpahe[-1], wait_until='domcontentloaded', timeout=60000)
        else:
            target = linkpahe[1] if len(linkpahe) > 1 else linkpahe[0]
            page.goto(target, wait_until='domcontentloaded', timeout=60000)

        page.wait_for_timeout(10000)
        kwik_page = page.content()
        page.close()

    except Exception as e:
        # Log general errors
        logging.error(f"Episode {arg} failed: {e}")
        return

    # Parse the page content to extract the actual download link (from kwik.cx)
    kwik_cx = BeautifulSoup(kwik_page, 'lxml')

    # Extract the direct download link from the page (looking for the 'redirect' class)
    kwik = kwik_cx.find('a', class_='redirect')['href']

    # Print the found download link to the terminal
    # print(f"\nEpisode {arg} Download link => {kwik}\n")

    if download_file:
        # Call the Banners.downloading method to display a download banner
        Banners.downloading(animepicked, arg)

        # Trigger the download process using the kwik link and specify the download directory
        kwik_download(url=kwik, dpath=DOWNLOADS, ep=arg, animename=animepicked)
    else:
        return kwik


                
    # ========================================== Multi Download Utility ==========================================

    
def multi_download(arg: str, download_file=True, resolution="720", max_workers=1, enable_notifications=False):
    """
    Downloads multiple episodes using ThreadPoolExecutor.
    Default is sequential (max_workers=1) for stability.
    Increase max_workers for parallel downloads if your system can handle it.
    """
    # Parse input like '2,3,5-7' into [2,3,5,6,7]
    eps = []
    for part in arg.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            eps.extend(range(start, end + 1))
        elif part.isdigit():
            eps.append(int(part))

    if max_workers == 1:
        logging.info(f"Starting sequential download of {len(eps)} episodes")
    else:
        logging.info(f"Starting parallel download of {len(eps)} episodes with {max_workers} workers")
    
    # Progress tracking
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False
    
    # Use ThreadPoolExecutor for downloads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, ep in enumerate(eps):
            # Small delay between launches to avoid port conflicts when parallel
            if i > 0 and max_workers > 1:
                time.sleep(2)
            future = executor.submit(download, arg=ep, download_file=download_file, res=str(resolution))
            futures[future] = ep
        
        # Wait for all downloads to complete with progress bar
        completed = 0
        failed = []
        
        if use_tqdm:
            progress = tqdm(total=len(eps), desc="Downloading", unit="ep")
        
        for future in as_completed(futures):
            ep = futures[future]
            try:
                future.result()
                completed += 1
                logging.info(f"Episode {ep} completed successfully ({completed}/{len(eps)})")
            except Exception as e:
                failed.append(ep)
                logging.error(f"Episode {ep} failed: {e}")
            
            if use_tqdm:
                progress.update(1)
        
        if use_tqdm:
            progress.close()
    
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
    
    print("\n=== Interactive Mode ===")
    print("Tip: Use command-line args for faster operation (try --help)\n")
    
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

    # Apply config-driven overrides
    global DOWNLOADS
    try:
        cfg = APP_CONFIG
    except NameError:
        cfg = None

    if cfg and cfg.get('download_dir'):
        DOWNLOADS = Path(cfg['download_dir'])

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
    
    # Search function with filters
    if sarg:
        records.append(sarg)
        result = lookup(sarg, year_filter=year_filter, status_filter=status_filter)
        if result is None:
            logging.error("Search failed. Exiting.")
            return

        # Ensure search results are visible before selection output when -i is also provided
        if iarg is not None and search_response_dict and 'data' in search_response_dict:
            print()
            print(f"{Fore.GREEN}🎬 Found {len(search_response_dict['data'])} results{Style.RESET_ALL} {Fore.CYAN}--->{Style.RESET_ALL}")
            print()
            for el in range(len(search_response_dict['data'])):
                name = search_response_dict['data'][el]['title']
                episodenum = search_response_dict['data'][el]['episodes']
                status = search_response_dict['data'][el]['status']
                year = search_response_dict['data'][el]['year']
                anime_type = search_response_dict['data'][el].get('type', 'N/A')
                type_emoji = {'TV': '📺', 'Movie': '🎬', 'ONA': '💻', 'OVA': '📀'}.get(anime_type, '📺')
                status_color = {
                    'Finished Airing': Fore.GREEN,
                    'Currently Airing': Fore.YELLOW,
                    'Not yet aired': Fore.RED
                }.get(str(status), Fore.WHITE)
                print(f"{Fore.MAGENTA}[{el}]{Style.RESET_ALL} {type_emoji} {Fore.CYAN}{name}{Style.RESET_ALL}")
                print(f"   {Fore.BLUE}├─ Episodes:{Style.RESET_ALL} {Fore.YELLOW}{episodenum}{Style.RESET_ALL}")
                print(f"   {Fore.BLUE}├─ Status:{Style.RESET_ALL} {status_color}{status}{Style.RESET_ALL}")
                print(f"   {Fore.BLUE}├─ Year:{Style.RESET_ALL} {Fore.YELLOW}{year}{Style.RESET_ALL}")
                print(f"   {Fore.BLUE}└─ Type:{Style.RESET_ALL} {Fore.YELLOW}{anime_type}{Style.RESET_ALL}")
                print()

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
        logging.info(f"Batch season {season_num}: downloading episodes {start_ep}-{end_ep}")
    
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
                logging.info(f"No record found at position {position}")
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
    
    # Set browser from command line args
    args = parser.parse_args(remaining)
    # Always set the browser environment variable
    os.environ['AUTOPAHE_BROWSER'] = args.browser or default_browser
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
    
    # Configure logging level based on --verbose/--quiet
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Verbose logging enabled")
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Propagate browser choice to Playwright via env
    try:
        if args.browser:
            os.environ['AUTOPAHE_BROWSER'] = str(args.browser).lower()
    except Exception:
        pass

    # If any arguments are provided, show banner and process them using command_main
    if any(vars(args).values()):
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
        print("  -s, --search <query>          Search for anime")
        print("  -i, --index <n>               Select anime index from search results")
        print("  -d, --single_download <ep>    Download a single episode")
        print("  -md, --multi_download <spec>  Download multiple episodes (e.g., 1-5 or 1,3,5)")
        print("  -a, --about                   Show anime overview")
        print("  -p, --resolution <720|1080>   Choose resolution")
        print("  -w, --workers <n>             Parallel downloads (use >1 with caution)")
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

