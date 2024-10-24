#! /usr/bin/python3
import time,argparse,os,sys
from pathlib import Path
import sys
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


def driver_output(url:str,driver = False,content = False,json = False, wait_time = 10):

    if driver == True : 

        driver = browser()
        try:
            driver.get(url)
        except:
            print("Selenium crashed while getting this page, please check ur internet connection")
            driver.quit()
            exit()

        driver.refresh()
    
    # Wait for the page to reload
        driver.implicitly_wait(wait_time)  # Adjust the timeout as needed
    
        if content:
            # Get page source after reloading
            page_source = driver.page_source
            driver.quit()
            return page_source
        
        elif json == True:
            # Get the json response again after reloading
            json_data = driver.execute_script("return document.body.textContent;")
            driver.quit()
            return json_data
        
    else:
        logging.error("Invalid arguments for driver_output")
        print("Use the content( arg to get page_content or the json arg to get json response ")
        exit()


    

        

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


# TEXT wrap decorator
def box_text(func):
    def wrapper():
        box_width = 70
        padding = (box_width - len(func())) // 2
        print('*' * box_width)
        print('*' + ' ' * padding + func() + ' ' * (box_width - len(func()) - padding) + '*')
        print('*' * box_width)

        
    return wrapper

    
# =======================================================================================================


def lookup(arg):

    global search_response_dict

    # Search banner

    Banners.search(arg)
    n()

    # url pattern requested when anime is searched
    animepahe_search_pattern = f'https://animepahe.ru/api?m=search&q={arg}'

    try:
        search_response = driver_output(animepahe_search_pattern,driver=True,json=True)
    except:
        search_response = driver_output(animepahe_search_pattern,driver=True,json=True, wait_time = 30)


    # print(search_response)

    #return if no anime found
    if not search_response:
        Banners.header()
        logging.info("No matching anime found. Retry!")
        return


    # converting response json data to python dictionary for operation
    search_response_dict = loads(search_response)
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
        jsonpage_dict = loads(driver_output(anime_url_format,driver=True,json=True))
    except:
        jsonpage_dict = loads(driver_output(anime_url_format,driver=True,json=True, wait_time = 30))



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


def download(arg = 1):
    # using return value of the search function to get the page
    # using the json data from the page url to get page where the episodes to watch are

    arg = int(arg)


    #session string of the stream episode
    episode_session = jsonpage_dict['data'][arg-1]['session']

    
    #stream page url format
    stream_page_url = f'https://animepahe.com/play/{session_id}/{episode_session}'
    # print(stream_page_url)

    
    # get steampage 
    driver = browser()
    driver.get(stream_page_url)

    time.sleep(15)
    stream_page_soup = BeautifulSoup(driver.page_source,'lxml')
    
    dload = stream_page_soup.find_all('a',class_='dropdown-item',target="_blank")
    # print (dload)
    from re import search


    # for link in dload:
    #     stlink = str(link)
    #     match = re.search(r'720p', stlink)
    #     if match:
    #         for link in stlink:
    #             soup = BeautifulSoup(link, 'html.parser')
    #             href = soup.a['href']
    #             print(href)
    
    # i am sure u are not wise enough to know what is going on
    #but the code above was shortened to the code below
    #using walrus operator and list comprehension
    #and it return a list of chars which when combined will return the link

    linkpahe = [(href:=BeautifulSoup(stlink, 'html.parser').a['href']) for link in dload if not (search(r'(360p|1080p|eng)', stlink:=str(link)))]
    
    #the linkpahe variable carries a list of the characters of the link
    #so the pahewin variable will return the link webpage content
     
    # print(linkpahe)
    # print(stream_page_soup)
    driver.get(f"{linkpahe[0]}")
    # driver.implicitly_wait(10)
    time.sleep(10)
    kwik_page = driver.page_source
    driver.quit()

    #getting the link to the kwik download page

    kwik_cx=BeautifulSoup(kwik_page,'lxml')

    # print(kwik_cx)

    #getting kwik.cx f download link
    kwik = kwik_cx.find('a', class_='redirect')['href']

    # print(f"Download link => {kwik}")
    Banners.downloading(animepicked,arg)
    
    kwik_download(url=kwik, dpath=DOWNLOADS, ep=arg, animename = animepicked)




            
def multi_download(eps):
    eps = str(eps)
    # given arg specifies '-' for range
    # New format for list comprehension  
    episodes = [
        num
        for segment in eps.split(",")
        for num in (
            range(int(segment.split("-")[0]), int(segment.split("-")[1]) + 1)
            if "-" in segment
            else [int(segment)]
        )]
    
    Banners.downloading(animepicked,eps)

    
    with concur.ThreadPoolExecutor() as executor:
        executor.map(download, episodes)




# ----------------------------------------------End of All the Argument Handling----------------------------------------------------------

#
def interactive_main():
    # Selecting browser of choice
    choice = str(input("Enter your favorite browser [e.g chrome] >> "))

    # Search prompt for search function
    lookup_anime = str(input("\nSearch an anime [e.g 'one piece'] >> "))

    # searching anime with the lookup function
    lookup(lookup_anime)

    # selection prompt for the anime search
    select_index = int(input("Select anime index [default : 0] >> "))
    
    # handling the selected anime metadata
    index(select_index)
    
    # summary info on the selected anime
    info = about()
    Banners.i_info(info)

    # Handling episode to download prompt
    download_type = str(input("""
    Enter the type of download facility you want:
    
    1. s or single_download for single episode download
    2. md or multi_download for multi episode download
    3. v or md_verbose for a verbose variant of the md function [SLOW]
    4. i for more in-depth info on the options above 
    
    >> """))
    
    ep_to_download = (input("Enter episode(s) to download >> "))

    switch = {
        "1": download,
        "2": multi_download,
        "4": info,
        's': download,
        'md': multi_download,
        'i': info,
        'single_download': download,
        'multi_download': multi_download,
        'info': info
    }

    # initiating the action for the choice
    selected_function = switch.get(download_type)

    if selected_function:
        selected_function(ep_to_download)
    else:
        print("Invalid input. Please select a valid option.")

def command_main(args):
    global barg
    barg = args.browser
    sarg = args.search
    iarg = args.index
    sdarg = args.single_download
    mdarg = args.multi_download
    abtarg = args.about
    rarg = args.record
    dtarg = args.execution_data  # New argument for retrieving stats by date

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
        process_record(records, update=True)
        multi_download(mdarg)


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



def main():
    
    # Reset the run count
    reset_run_count()

    start_time = time.perf_counter()


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
            "Examples: ["
            "'today', 'yesterday', 'last 3 days', 'last week', "
            "'this week', '2 weeks ago', 'last month', '1 month ago'.]"
        )
    )


    args = parser.parse_args()

    if any(vars(args).values()):
        command_main(args)
    else:
        interactive_main()
    
    # Log execution time
    log_execution_time(start_time)

if __name__ == '__main__':
    main()
else:
    Banners.header()