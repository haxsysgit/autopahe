#! /usr/bin/python3
import time,argparse,os,sys,requests
from re import search
from pathlib import Path
import logging
from json import loads,load,dump,dumps
from bs4 import BeautifulSoup
from kwikdown import kwik_download
from manager import process_record,load_database,print_all_records,search_record
from execution_tracker import log_execution_time, reset_run_count, get_execution_stats
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as chrome_service
from selenium.webdriver.chrome.service import Service as ff_service
import concurrent.futures as concur


########################################### GLOBAL VARIABLES ######################################

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

logging.basicConfig(
    level=logging.INFO,  # Set the minimum log level
    format='\n%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('autopahe.log')  # Output to a file
    ]
)


#######################################################################################################################

#Record list
records = []


############################################ BROWSER HANDLING ##########################################################

def browser(choice="firefox"):
    chrome_guess = ["chrome", "Chrome", "google chrome", "google"]

    ff_guess = ["ff", "firefox", "ffgui", "ffox", "fire"]

    if choice.lower() in chrome_guess:
        chserv = chrome_service("/snap/bin/geckodriver")
        
        driver = webdriver.Chrome(service=chserv)

        logging.info("Using Chrome browser")

    elif choice.lower() in ff_guess:
        ffserv = ff_service("/snap/bin/geckodriver")

        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(service=ffserv, options=options)

        logging.info("Using Firefox browser in headless mode\n")

    else:
        logging.error("Unsupported browser choice")
        return 0

    return driver



###############################################################################################


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


def driver_output(url: str, driver=False, content=False, json=False, wait_time=10):
    if driver: 
        # Initialize the browser
        driver_instance = browser()
        try:
            driver_instance.get(url)
        except Exception as e:
            # Log the error without exiting the program
            logging.error(f"Selenium failed to load the page: {e}")
            driver_instance.quit()
            return None  # Return None to indicate failure but allow the program to continue

        # Refresh page to ensure it's up-to-date
        driver_instance.refresh()
    
        # Wait for the page to load
        driver_instance.implicitly_wait(wait_time)

        if content:
            # Get the page content (HTML)
            page_source = driver_instance.page_source
            driver_instance.quit()
            return page_source

        elif json:
            # Get the JSON content
            json_data = driver_instance.execute_script("return document.body.textContent;")
            driver_instance.quit()
            dict_data = loads(json_data)
            return dict_data
    else:
        # Log an error if invalid parameters were provided
        logging.error("Invalid arguments provided to driver_output function.")
        print("Use the 'content' argument to get page content or 'json' argument to get JSON response.")
        return None  # Return None to indicate the invalid argument scenario



    

        

current_system_os = str(sys.platform) #get current os


class Banners():
    def header():
        os.system('cls' if current_system_os.lower() == 'windows' else 'clear' )
        print('''
              
             db    8    8 88888 .d88b.      888b.    db    8   8 8888 
            dPYb   8    8   8   8P  Y8 ____ 8  .8   dPYb   8www8 8www 
           dPwwYb  8b..d8   8   8b  d8      8wwP'  dPwwYb  8   8 8    
          dP    Yb `Y88P'   8   `Y88P'      8     dP    Yb 8   8 8888 
              
              ''')
        
                
    def search(anime = None):
        print(f'''
        ----------------------------------------
            Searching for {anime}..
        ----------------------------------------
        ''')

    def downloading(anime = None,eps = None):
        print(f'''
        ----------------------------------------
            Downloading episode {eps} of {anime}..
        ----------------------------------------
        ''')
        
    def select(anime,eps = None,year = None,
               atype = None,img = None,status = None):
        print(f'''
        ----------------------------------------
                Selected  {anime}..
        ----------------------------------------
        
        - Episodes Available : {eps}
        - Year released : {year}
        - Type of anime (TV or Movie) : {atype}
        - Cover image : {img}
        - Status : {status}
        
        ''')
    def anime_info(anim = None , abt = None):
        print(f'''
        ----------------------------------------
            ABOUT {anim}
        ----------------------------------------
        
        {abt}
        
        ''')
    def i_info(summary = None):
        print(f'''
        ----------------------------------------
            Summary on Anime
        ----------------------------------------
        
        {summary}
        
        ''')
        

# Banner Header
Banners.header()


def n():
    print()


n()

# ============================ The requests argument handler function===============================


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


def lookup(arg):

    global search_response_dict

    # Search banner

    Banners.search(arg)
    n()

    # url pattern requested when anime is searched
    animepahe_search_pattern = f'https://animepahe.ru/api?m=search&q={arg}'

    try:

        search_response = requests.get(animepahe_search_pattern).content

        #return if no anime found
        if not search_response:
            Banners.header()
            logging.info("No matching anime found. Retry!")
            return
        
        # converting response json data to python dictionary for operation
        search_response_dict = loads(search_response)

    except:

        search_response = driver_output(animepahe_search_pattern,driver=True,json=True, wait_time = 30)
        search_response_dict = search_response

    # print(search_response)

    # print(animepahe_search_pattern)

    # all animepahe has a session url and the url will be https://animepahe.com/anime/[then the session id]




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
        jsonpage_dict = loads(requests.get(anime_url_format).content)
    except:
        jsonpage_dict = driver_output(anime_url_format,driver=True,json=True, wait_time = 30)


 
    episto = jsonpage_dict['total']
    year = search_response_dict['data'][arg]['year']
    type = search_response_dict['data'][arg]['type']
    image = search_response_dict['data'][arg]['poster']
    stat = search_response_dict['data'][arg]['status']
    
    Banners.select(animepicked,eps=episto,year=year,
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


def download(arg=1):
    """
    Downloads the specified episode of the anime by navigating through the webpage using Selenium 
    and extracting the download link.
    """
    #Initializing driver
    driver = browser()

    # Convert the argument to an integer to ensure it is in the correct format
    arg = int(arg)
    
    # Retrieve the session ID for the selected episode from the global jsonpage_dict
    episode_session = jsonpage_dict['data'][arg-1]['session']

    # Construct the URL for the stream page for the specific episode using the session ID
    stream_page_url = f'https://animepahe.com/play/{session_id}/{episode_session}'

    # Open the stream page URL in the browser
    driver.get(stream_page_url)

    # Set an implicit wait for elements to load before interacting with the page
    driver.implicitly_wait(10)

    # Refresh the page to ensure it's fully loaded
    driver.refresh()

    # Pause briefly to ensure the page has time to load
    time.sleep(15)

    # Parse the page content into a BeautifulSoup object for easier scraping
    stream_page_soup = BeautifulSoup(driver.page_source, 'lxml')

    # Find all the download links in the page using the specified class name
    dload = stream_page_soup.find_all('a', class_='dropdown-item', target="_blank")

    # Use a list comprehension to filter out specific resolutions (e.g., 360p, 1080p, and English versions)
    # The `stlink` is the string version of the link element. We check for matching resolutions with a regex.
    linkpahe = [
        (href := BeautifulSoup(stlink, 'html.parser').a['href'])  # Extract the actual download link
        for link in dload if not (search(r'(360p|1080p|eng)', stlink := str(link)))  # Filter out unwanted links
    ]

    # If a valid download link is found, proceed with the next steps
    if linkpahe:
        # Navigate to the selected download link
        driver.get(linkpahe[0])
        
        # Pause to allow the new page to load
        time.sleep(10)
        
        # Retrieve the page source of the new page (now the actual download page)
        kwik_page = driver.page_source

        #Closing opened driver instance
        driver.quit()
    
        
        # Parse the page content to extract the actual download link (from kwik.cx)
        kwik_cx = BeautifulSoup(kwik_page, 'lxml')
        
        # Extract the direct download link from the page (looking for the 'redirect' class)
        kwik = kwik_cx.find('a', class_='redirect')['href']
        
        # Print the found download link to the terminal
        print(f"\nDownload link => {kwik}\n")
        
        # Call the Banners.downloading method to display a download banner
        Banners.downloading(animepicked, arg)
        
        # Trigger the download process using the kwik link and specify the download directory
        kwik_download(url=kwik, dpath=DOWNLOADS, ep=arg, animename=animepicked)



                
    # ========================================== Multi Download Utility ==========================================

def multi_download(eps):
    try:
        # Convert the eps argument into a string to handle both single numbers and ranges
        eps = str(eps)
        
        # Parse the input and create a list of episode numbers
        # The input format could either be a single episode (e.g., "3"), a range (e.g., "1-5"),
        # or a comma-separated list of both (e.g., "1-3,5,7")
        episodes = [
            num  # The current episode number
            for segment in eps.split(",")  # Split the input by commas for multiple entries
            for num in (
                # If the segment contains a range (e.g., "1-3"), generate the list of numbers
                range(int(segment.split("-")[0]), int(segment.split("-")[1]) + 1)
                if "-" in segment
                else [int(segment)]  # If not a range, just use the number itself
            )
        ]
        

        # Print a message for the start of the download, showing the anime name and episodes to be downloaded
        Banners.downloading(animepicked, eps)
        
        # Use ThreadPoolExecutor for parallel downloading of episodes
        with concur.ThreadPoolExecutor() as executor:
            # Use executor.map to download each episode in the episodes list concurrently
            executor.map(download, episodes)

    except Exception as e:
        # Catch any exceptions that occur during parsing or downloading
        logging.error(f"Error in multi_download: {e}")



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

    # Reset the run count
    reset_run_count()

    # Init browser
    if barg:
        browser(barg)

    # Search function
    if sarg:
        records.append(sarg)
        lookup(sarg)

    # Index function
    if iarg is not None:
        records.append(search_response_dict['data'][iarg])
        process_record(records)
        index(iarg)

    # About function
    if abtarg:
        info = about()
        records.append(info)
        process_record(records, update=True)
        Banners.anime_info(animepicked, info)

    # Single Download function
    if sdarg:
        records.append(sdarg)
        process_record(records, update=True)
        download(sdarg)

    # Multi Download function
    if mdarg:
        records.append(mdarg)
        multi_download(mdarg)
        process_record(records, update=True)

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
                total_time_minutes = stats[stat]['total_time_mins']

                total_time_hours = stats[stat]['total_time_hours']

                average_time_mins = stats[stat]['average_time_mins']

                average_time_hours = stats[stat]['average_time_hours']
                
                print(f"\n\nExecution stats for '{stat}' -->>")

                print(f"\n1.) Total Runs: {stats[stat]['run_count']}")
                print(f"\n2.) Total Execution Time (Minutes): {total_time_minutes:.2f} minutes")  # Print in minutes
                print(f"\n3.) Total Execution Time (Minutes): {total_time_hours:.2f} hours")  # Print in hours
                print(f"\n4.) Average Execution Time (Minutes): {average_time_mins:.2f} minutes")  # Print in minutes
                print(f"\n5.) Average Execution Time (Hours): {average_time_hours:.2f} hours")  # Print in hours 

                print("=============================================================================")
        else:
            print(f"\n\nNo execution data found for '{dtarg}'.")



# Main entry point for the script that processes arguments and triggers the appropriate actions
def main():


    # Reset the run count to start fresh
    reset_run_count()

    # Record the start time of the execution
    start_time = time.perf_counter()

    # Argument parser setup to handle command-line inputs
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--browser', help='Select the desired browser (chrome or firefox). Default is chrome.')
    parser.add_argument('-s', '--search', type=str, help='Search for an anime by name.')
    parser.add_argument('-i', '--index', type=int, help='Specify the index of the desired anime from the search results.')
    parser.add_argument('-d', '--single_download', type=int, help='Download a single episode of an anime.')
    parser.add_argument('-md', '--multi_download', help='Download multiple episodes of an anime.')
    parser.add_argument('-a', '--about', help='Output an overview of the anime', action='store_true')
    parser.add_argument('-r', '--record', help='Interact with the records/database (view, [index], [keyword]).')
    
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
    args = parser.parse_args()

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

