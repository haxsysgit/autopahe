#! /usr/bin/python3
import time,argparse,os,sys,requests,tempfile
import re
from pathlib import Path
import logging
from json import loads,load,dump,dumps,JSONDecodeError
from bs4 import BeautifulSoup
from ap_core.banners import Banners, n
from ap_core.browser import browser, driver_output, get_request_session, cached_request, cleanup_browsers
from ap_core.config import load_app_config, write_sample_config, sample_config_text
from ap_core.cache import cache_get, cache_set, cache_clear, get_cache_stats
from ap_core.notifications import notify_download_complete, notify_download_failed
from ap_core.cookies import clear_cookies
from kwikdown import kwik_download
from manager import (
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
from pahesort import rename_anime, organize_anime, gather_anime
from execution_tracker import log_execution_time, reset_run_count, get_execution_stats
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import atexit

############################################## Selenium imports #################################################

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as chrome_service
from selenium.webdriver.chrome.service import Service as ff_service
from selenium.common.exceptions import WebDriverException


########################################### GLOBAL VARIABLES ######################################

# Paths to your driver executables
GECKO_PATH = "/snap/bin/geckodriver"
CHROME_PATH = "/snap/bin/chromedriver"

# Counter for unique Marionette ports
_port_counter = 2828

# Global browser pool for reuse
_browser_pool = []
_max_browsers = 3  # Limit concurrent browsers
_pool_lock = None

# Download path
system_name = sys.platform.lower()

if system_name == "win32":
    DOWNLOADS = Path.home() / "Downloads"

elif system_name == "darwin":  # macOS
    DOWNLOADS = Path.home() / "Downloads"

elif system_name == "linux":
    DOWNLOADS = Path.home() / "Downloads"

else:
    raise Exception("An Error Occurred, Unsupported Operating System")
    exit()

########################################### LOGGING ################################################

# Logging will be configured after CLI parsing to respect --verbose/--quiet
log_level = logging.INFO  # Default
logging.basicConfig(
    level=log_level,
    format='\n%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('autopahe.log')
    ]
)


#######################################################################################################################

#Record list
records = []


############################################ BROWSER HANDLING ##########################################################

# Register cleanup on exit for imported cleanup function
atexit.register(cleanup_browsers)




###############################################################################################


def parse_mailfunction_api(text):
    result = {}
    data_list = []
    current_item = None
    in_data = False

    def parse_value(val):
        # remove surrounding quotes
        val = val.strip()
        if m := re.match(r'^"(.*)"$', val):
            return m.group(1)
        # integer?
        if re.fullmatch(r'\d+', val):
            return int(val)
        # float?
        if re.fullmatch(r'\d+\.\d+', val):
            return float(val)
        return val

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Top-level until we see 'data'
        if not in_data:
            if line == "data":
                in_data = True
                continue
            if key_val := line.split(None, 1):
                key = key_val[0]
                if len(key_val) == 2:
                    val = parse_value(key_val[1])
                    result[key] = val
                continue

        # Inside data items
        # If line is only a number, start new item
        if re.fullmatch(r'\d+', line):
            if current_item is not None:
                data_list.append(current_item)
            current_item = {}
        else:
            # key and value
            parts = line.split(None, 1)
            if len(parts) == 2:
                key, raw_val = parts
                current_item[key] = parse_value(raw_val)

    # Append last item
    if current_item is not None:
        data_list.append(current_item)

    result["data"] = data_list
    return result



def data_report(data:dict,filepath = "autopahe_data.json",):
    if data:
        # Read existing JSON data from file
        if os.path.exists(filepath):
            with open(filepath, 'r') as json_file:
                existing_data = load(json_file)
        else:
            open(filepath,"x")
            existing_data={}

        new_data = {**existing_data,**data}
            
        with open(filepath,"w") as st:
            dump(new_data,st,indent=4)

current_system_os = str(sys.platform) #get current os


# Banner Header
Banners.header()


# ... (rest of the code remains the same)


# # TEXT wrap decorator
# def box_text(func):
#     def wrapper():
#         box_width = 70
#         padding = (box_width - len(func())) // 2
#         print('*' * box_width)
#         print('*' + ' ' * padding + func() + ' ' * (box_width - len(func()) - padding) + '*')
#         print('*' * box_width)

        
#     return wrapper

    
# =======================================================================================================



def lookup(arg, year_filter=None, status_filter=None):

    global search_response_dict

    # Search banner
    Banners.search(arg)
    n()

    # url pattern requested when anime is searched
    animepahe_search_pattern = f'https://animepahe.si/api?m=search&q={arg}'

    try:
        # Try disk cache first
        cached = cache_get(animepahe_search_pattern, max_age_hours=6)
        if cached:
            search_response = cached
            logging.debug("Loaded search results from disk cache")
        else:
            # Use HTTP request with in-memory cache
            search_response = cached_request(animepahe_search_pattern)
            if search_response:
                cache_set(animepahe_search_pattern, search_response)
                logging.debug("Saved search results to disk cache")

        #return if no anime found
        if not search_response:
            Banners.header()
            logging.info("No matching anime found. Retry!")
            return
        
        # converting response json data to python dictionary for operation
        search_response_dict = loads(search_response)
        
        logging.debug(f"Direct API call succeeded. Found {len(search_response_dict.get('data', []))} results")

    except Exception as e:
        logging.warning(f"Direct API request failed ({e}), falling back to Selenium browser...")
        search_response = driver_output(animepahe_search_pattern,driver=True,json=True, wait_time=30)
        if search_response:
            search_response_dict = search_response
            logging.debug(f"Selenium fallback succeeded. Found {len(search_response_dict.get('data', []))} results")
        else:
            logging.error("Both direct API and Selenium failed to retrieve search results")
            search_response_dict = {'data': []}

    # print(search_response)

    # print(animepahe_search_pattern)

    # all animepahe has a session url and the url will be https://animepahe.com/anime/[then the session id]




    # Check if results exist
    if not search_response_dict or 'data' not in search_response_dict or not search_response_dict['data']:
        Banners.header()
        logging.error("No results found. Please try a different search term.")
        print("\n❌ No anime found matching your search.\n")
        return
    
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
    n()
    print(f'{resultlen} results were found  ---> ')

    n()

    for el in range(len(search_response_dict['data'])):
        name = search_response_dict['data'][el]['title']

        episodenum = search_response_dict['data'][el]['episodes']

        status = search_response_dict['data'][el]['status']

        year = search_response_dict['data'][el]['year']

        

        print(f'''
        [{el}] : {name}
        ---------------------------------------------------------
                Number of episodes contained : {episodenum}
                Current status of the anime : {status}
                Year the anime aired : {year}
        ''')

    n()

    return search_response_dict




# =========================================== handling the single download utility ============================
    

def index(arg):

    n()

    global jsonpage_dict,session_id,animepicked,episode_page_format


    animepicked = search_response_dict['data'][arg]['title']
    
    #session id of the whole session with the anime
    session_id = search_response_dict['data'][arg]['session']

    # anime episode page url format and url
    
    episode_page_format = f'https://animepahe.com/anime/{session_id}'
    
    # now the anime_json_data url format
    anime_url_format = f'https://animepahe.com/api?m=release&id={session_id}&sort=episode_asc&page=1'


    try:
        session = get_request_session()
        jsonpage_dict = loads(session.get(anime_url_format, timeout=10).content)
    except:
        jsonpage_dict = driver_output(anime_url_format,driver=True,json=True, wait_time=20)


 
    episto = jsonpage_dict['total']
    year = search_response_dict['data'][arg]['year']
    type = search_response_dict['data'][arg]['type']
    image = search_response_dict['data'][arg]['poster']
    stat = search_response_dict['data'][arg]['status']
    
    Banners.select(animepicked,eps=episto, anipage=episode_page_format,year=year,
                   atype = type,img = image,status=stat)

    final_data = {**search_response_dict,**jsonpage_dict}
    data_report(data=final_data)
    n()
    

def about():
        #extract the anime info from a div with class anime-synopsis
        ep_page = driver_output(episode_page_format,driver=True,content=True)
        soup = BeautifulSoup(ep_page,'lxml')
        abt = soup.select('.anime-synopsis')

        return abt[0].text.strip()





def download(arg=1, download_file=True, res = "720"):
    """
    Downloads the specified episode of the anime by navigating through the webpage using Selenium 
    and extracting the download link.
    """
    

    driver = None
    try:
        # Convert the argument to an integer to ensure it is in the correct format
        arg = int(arg)

        # Initializing driver
        driver = browser()

        # Retrieve the session ID for the selected episode from the global jsonpage_dict
        episode_session = jsonpage_dict['data'][arg - 1]['session']

        # Construct the URL for the stream page for the specific episode using the session ID
        stream_page_url = f'https://animepahe.com/play/{session_id}/{episode_session}'

        # Open the stream page URL in the browser
        driver.get(stream_page_url)

        # Set an implicit wait for elements to load before interacting with the page
        driver.implicitly_wait(10)

        # Pause briefly to ensure the page has time to load
        time.sleep(15)

        # Parse the page content into a BeautifulSoup object for easier scraping
        stream_page_soup = BeautifulSoup(driver.page_source, 'lxml')

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
            raise ValueError(f"No valid download link found for episode {arg}")

        # Navigate to the selected download link
        res = str(res)
        if res == "720":
            driver.get(linkpahe[0])
        elif res == '1080':
            driver.get(linkpahe[-1])
        else:
            driver.get(linkpahe[1])
        
        # Pause to allow the new page to load
        time.sleep(10)

        # Retrieve the page source of the new page (now the actual download page)
        kwik_page = driver.page_source

    except WebDriverException as e:
        # Log browser-related errors
        logging.error(f"Episode {arg} failed: {e}")
        if driver:
            driver.quit()
        return

    except Exception as e:
        # Log general errors
        logging.error(f"Episode {arg} failed: {e}")
        if driver:
            driver.quit()
        return

    finally:
        # Closing opened driver instance
        if driver:
            driver.quit()

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
def interactive_main(driver):
    # Prompt the user to select their preferred browser (e.g., chrome or firefox)
    choice = str(input("Enter your favorite browser [e.g chrome] >> "))

    # Prompt the user to search for an anime by name
    lookup_anime = str(input("\nSearch an anime [e.g 'one piece'] >> "))

    # Call the lookup function to search for the anime
    lookup(lookup_anime)

    # Prompt the user to select an anime index from the search results (default is 0)
    select_index = int(input("Select anime index [default : 0] >> "))
    
    # Call the index function to handle metadata of the selected anime
    index(select_index)
    
    # Get summary info about the selected anime
    info = about()
    # Display the anime information using the Banners class
    Banners.i_info(info)

    # Prompt the user for the type of download they want
    download_type = str(input("""
    Enter the type of download facility you want:
    
    1. s or single_download for single episode download
    2. md or multi_download for multi episode download
    3. v or md_verbose for a verbose variant of the md function [SLOW]
    4. i for more in-depth info on the options above 
    
    >> """))
    
    # Prompt for the episode(s) to download
    ep_to_download = (input("Enter episode(s) to download >> "))

    # A dictionary mapping the download type to the corresponding function
    switch = {
        "1": download,  # Single download
        "2": multi_download,  # Multi download
        "4": info,  # Display info
        's': download,  # Single download alias
        'md': multi_download,  # Multi download alias
        'i': info,  # Info alias
        'single_download': download,  # Single download alias
        'multi_download': multi_download,  # Multi download alias
        'info': info  # Info alias
    }

    # Retrieve the function based on the user's choice and execute it
    selected_function = switch.get(download_type)

    # If the function is valid, execute it, otherwise print an error
    if selected_function:
        selected_function(ep_to_download,driver)
    else:
        print("Invalid input. Please select a valid option.")


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

    # Init browser
    if barg:
        browser(barg)

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

    # Index function
    if iarg is not None:
        if not search_response_dict or 'data' not in search_response_dict or len(search_response_dict['data']) <= iarg:
            logging.error(f"Invalid index {iarg}. Search returned no results or index out of range.")
            return
        index(iarg)
        search_response_dict["data"][iarg]["anime_page"] = episode_page_format
        records.append(search_response_dict['data'][iarg])
        process_record(records)

    # About function
    if abtarg:
        info = about()
        records.append(info)
        print(records)

        process_record(records, update=True)
        Banners.anime_info(animepicked, info)

    

    did_download = False
    # Single Download function
    if sdarg:
        records.append(sdarg)
        download(sdarg,res=parg)
        process_record(records, update=True)
        did_download = True

    if larg:
        records.append(larg)
        download(larg , download_file=False,res=parg)
        process_record(records, update=True)


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
        process_record(records, update=True)
        did_download = True

    if mlarg:
        records.append(mlarg)
        multi_download(mlarg,download_file=False,resolution=parg, max_workers=args.workers, enable_notifications=enable_notifications)
        process_record(records, update=True)
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

    # Argument parser setup to handle command-line inputs
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--browser', default=cfg.get('browser','firefox'), help='Select the desired browser (chrome or firefox).')
    parser.add_argument('-s', '--search', type=str, help='Search for an anime by name.')
    parser.add_argument('-i', '--index', type=int, help='Specify the index of the desired anime from the search results.')
    parser.add_argument('-d', '--single_download', type=int, help='Download a single episode of an anime.')
    parser.add_argument('-md', '--multi_download', help='Download multiple episodes of an anime.')
    parser.add_argument('-l', '--link', help='Display the link to the kwik download page')
    parser.add_argument('-ml', '--multilinks', help='Display the multiple links to the kwik download page')
    parser.add_argument('-a', '--about', help='Output an overview of the anime', action='store_true')
    parser.add_argument('-p', '--resolution', type=str, default=str(cfg.get('resolution','720')), help='Provides resolution option for downloads')
    parser.add_argument('-w', '--workers', type=int, default=int(cfg.get('workers','1')), help='Number of parallel workers for multi-episode downloads (use >1 with caution)')
    parser.add_argument('-r', '--record', help='Interact with the records/database (view, [index], [keyword]).')
    parser.add_argument('-R', '--records', nargs='+', help='Robust records management. Examples: -R view | -R search naruto | -R delete 3 | -R progress 3 27 | -R rate 3 8.5 | -R rename 3 "New Title" | -R set-keyword 3 naruto | -R list-status completed | -R export out.json json | -R import in.json')
    parser.add_argument('--sort', choices=['all','rename','organize'], help='Sort downloaded files (integrates pahesort).')
    parser.add_argument('--sort-path', help='Path to sort; defaults to Downloads')
    parser.add_argument('--sort-dry-run', action='store_true', help='Dry-run sorting (no changes)')
    parser.add_argument('--summary', help='Show execution stats and records summary; accepts same formats as --execution_data')
    
    # Phase 2/3/4 enhancements
    parser.add_argument('--year', type=int, help='Filter search results by year (e.g., 2020)')
    parser.add_argument('--status', type=str, help='Filter search results by status (e.g., "Finished Airing")')
    parser.add_argument('--season', type=int, help='Download entire season (12-13 eps). Example: --season 1 downloads eps 1-12')
    parser.add_argument('--notify', action='store_true', help='Enable desktop notifications on download complete/fail')
    parser.add_argument('--cache', choices=['clear', 'stats'], help='Cache management: clear (remove all) or stats (show info)')
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

    # If any arguments are provided, process them using command_main
    if any(vars(args).values()):
        command_main(args)
    else:
        # If no arguments are provided, run the interactive main function
        interactive_main()

    # Log the execution time once the script has finished
    log_execution_time(start_time)





#================================================================ End of Arguments Handling =======================================================

# If the script is executed directly, call the main function
if __name__ == '__main__':
    main()
else:
    # If the script is imported as a module, display the header
    Banners.header()

