#! /usr/bin/python3
import time,requests,argparse,os,shutil
import sys,subprocess,re
from json import loads,dumps,load,dump
from re import search
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.core.utils import ChromeType

import tqdm

start = time.perf_counter()

current_system_os = str(sys.platform) #get current os


class Banners():
    def header():
        # os.system('cls' if current_system_os.lower() == 'windows' else 'clear' )
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
    def getting_eps(episode  = None):
        print(f'''
        ----------------------------------------
            Getting episode {episode} links...
        ----------------------------------------
        ''')
    def start_dl(eps = None):
        print(f'''
        ----------------------------------------
            Starting Downloads for episode {eps}..
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
        
# def get_terminal_size():
#     terminal_size = shutil.get_terminal_size((80, 20))  # Default size if unable to get actual size
#     if os.name == 'posix':  # Unix/Linux/Mac systems
#         try:
#             terminal_size = shutil.get_terminal_size()
#         except Exception:
#             pass
#     elif os.name == 'nt':  # Windows systems
#         try:
#             terminal_size = shutil.get_terminal_size((80, 20))
#         except Exception:
#             pass
#     return terminal_size



def n():
    print()


n()
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



# driver handling function
def browser(barg):
    global driver

    if barg == "chrome":

        serv = Service(executable_path=ChromeDriverManager().install())
        option = webdriver.ChromeOptions()

        option.headless = False

        option.add_experimental_option("detach", False)

        driver = webdriver.Chrome(service = serv,options=option)

    elif barg == "ffgui":

        options = Options()
        options.headless = False
        driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(),options=options)
        
    elif barg == "firefox":

        options = Options()
        options.headless = True
        driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(),options=options)


    elif barg == "brave":
        serv = Service(ChromeDriverManager().install())
        
        options = Options()
        
        options.headless = False
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()))
    else:
        pass
        
    def close():
        driver.quit()
        
    
# =======================================================================================================


def lookup(arg):
    # search banner
    Banners.search(arg)
    n()
    # url pattern requested when anime is searched
    animepahe_search_pattern = f'https://animepahe.com/api?m=search&q={arg}'

    global search_response_dict

    search_response = requests.get(animepahe_search_pattern).text
    
        #return if no anime found
    if not search_response:
        Banners.header()
        print("No matching anime found. Retry!")
        return
    
    # converting response json data to python dictionary for operation
    search_response_dict = loads(search_response)
    # all animepahe has a session url and the url will be https://animepahe.com/anime/[then the session id]

    resultlen = len(search_response_dict['data'])

    print(f'{resultlen} results were found and are as follows --> ')

    n()

    for el in range(len(search_response_dict['data'])):
        name = search_response_dict['data'][el]['title']

        episodenum = search_response_dict['data'][el]['episodes']

        status = search_response_dict['data'][el]['status']

        session = search_response_dict['data'][el]['session']
        

        print(f'''
        [{el}] : {name}
        ---------------------------------------------------------
                Number of episodes contained : {episodenum}
                Current status of the anime : {status}
                session id of the anime : {session}
        ''')

    n()
    n()

def search_hidden(arg):
    # search banner
    Banners.search(arg)
    n()
    # url pattern requested when anime is searched
    animepahe_search_pattern = f'https://animepahe.com/api?m=search&q={arg}'

    global search_response_dict
    
    # converting response json data to python dictionary for operation
    search_response_dict = loads(requests.get(animepahe_search_pattern).text)
    # all animepahe has a session url and the url will be https://animepahe.com/anime/[then the session id]




# =========================================== handling the single download utility ========================

    


        

def index(arg):

    n()
    global jsonpage_dict,episto,session_id,animepicked,episode_page_format
    
    animepicked = search_response_dict['data'][arg]['title']
    
    #session id of the whole session with the anime
    session_id = search_response_dict['data'][arg]['session']

    # anime episode page url format and url
    
    episode_page_format = f'https://animepahe.com/anime/{session_id}'
    
    # now the anime_json_data url format
    anime_url_format = f'https://animepahe.com/api?m=release&id={session_id}&sort=episode_asc&page=1'
    
    jsonpage_dict = loads(requests.get(anime_url_format).text)
    
    episto = jsonpage_dict['total']
    year = search_response_dict['data'][arg]['year']
    type = search_response_dict['data'][arg]['type']
    image = search_response_dict['data'][arg]['poster']
    stat = search_response_dict['data'][arg]['status']
    
    Banners.select(animepicked,eps=episto,year=year,
                   atype = type,img = image,status=stat)

    
    n()
    

def about():
        #extract the anime info from a div with class anime-synopsis
        soup = BeautifulSoup((requests.get(episode_page_format).text),'lxml')
        abt = soup.select('.anime-synopsis')
        return abt[0].text.strip()

# USING tqdm to simulate download progress
def progress(size):
    size = int(''.join(filter(str.isdigit,str(size))))
    # Simulating the download
    
    with tqdm.tqdm(total=size, unit='B', unit_scale=True, desc='Downloading') as pbar:
        bytes_downloaded = 0
        
        while bytes_downloaded < size:
            # Simulating downloading some data
            time.sleep(0.5)  # Simulating time delay
            update = 60 * 1024
            bytes_downloaded += update # Simulating downloaded bytes

            pbar.update(update)  # Update the progress bar with the number of downloaded bytes

    # File download completed
    driver.quit()
    print("Download completed.")


def download(arg: int = 1):
    # using return value of the search function to get the page
    # using the json data from the page url to get page where the episodes to watch are

    print()

    #session string of the stream episode
    episode_session = jsonpage_dict['data'][arg-1]['session']
    
    #stream page url format
    stream_page_url = f'https://animepahe.com/play/{session_id}/{episode_session}'
    n()
    
    stream_page_soup = BeautifulSoup(requests.get(f'{stream_page_url}').content,'lxml')
    
    dload = stream_page_soup.find_all('a',class_='dropdown-item',target="_blank")
    
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
    pahe_win = requests.get(f'{[ch for ch in linkpahe][0]}').content
    
    #getting the link to the kwik download page
    kwik = (pahe_soup:=BeautifulSoup(pahe_win,'lxml')).find('a', class_='redirect')['href']
    
    Banners.getting_eps(arg)
    
    # ---------------------------Using selenium to render and clickk the download button------------------------

    # going to the download page
    driver.get(kwik)
    
    # getting the title
    kwik_soup = BeautifulSoup((requests.get(kwik).text),'lxml')
    # filename = kwik_soup.find('h1',class_ = 'title').text.strip()
    size = (kwik_soup.find('abbr')['title'])

    # Starting download banner
    Banners.start_dl(arg)
    
    WebDriverWait(driver, 15).until(EC.presence_of_element_located(
        (By.XPATH, "//form[@method = 'POST']/button[contains(@class, 'button')]")))

    element = driver.find_element(
        By.XPATH, "//form[@method = 'POST']/button[contains(@class, 'button')]")

    # the first click will click on the ad on the screeen
    try:
        ad=driver.find_element(By.XPATH, '/html/body/div[2]/a')
        
        ad.click()
        element.click()
        # the second click will download the content
    except:    
        element.click()
        n()

    
    Banners.downloading(animepicked,arg)
    progress(size)
    





def multi_download_verbose(arg):
    print("To make efficient use of the multi download function,\nit is advised you have a very fast and stable internet connection")
    
    
    n()
    
    # given arg specifies '-' for range
    if '-'in str(arg):
        # parsing the arg to get individial eps
        epr = list(x for x in arg.split('-'))

        # list of the range of eps
        episodes_list = list(range(int(epr[0]),int(epr[1]) + 1))
        
    else:
        # classic arg separated by comma
        episodes_list = [int(x) for x in arg.split(',')]
        
        
            
    for elem in episodes_list:
                
        episode_session = jsonpage_dict['data'][elem]['session']
            

        #stream page url format
        stream_page_url = f'https://animepahe.com/play/{session_id}/{episode_session}'
        n()
        
        stream_page_soup = BeautifulSoup(requests.get(f'{stream_page_url}').content,'lxml')
        
        dload = stream_page_soup.find_all('a',class_='dropdown-item',target="_blank")
        
        from re import search


        # for link in dload:
        #     stlink = str(link)
        #     match = if not (search(r'(360p|1080p|eng)', stlink))
        #     if match:
        #         for link in stlink:
        #             soup = BeautifulSoup(link, 'html.parser')
        #             href = soup.a['href']
        #             print(href)
        
        # i am sure u are not wise enough to know what is going on
        #but the code above was shortened to the code below
        #using walrus operator and list comprehension
        #and it return a list of chars which when combined will return the link
        linkpahe = [(BeautifulSoup(stlink, 'html.parser').a['href']) for link in dload if not (search(r'(360p|1080p|eng)', stlink:=str(link)))]
        
        #the linkpahe variable carries a list of the characters of the link
        #so the pahewin variable will return the link webpage content
        pahe_win = requests.get(f'{[ch for ch in linkpahe][0]}').content
        
        #getting the link to the kwik download page
        kwik = (BeautifulSoup(pahe_win,'lxml')).find('a', class_='redirect')['href']

        Banners.getting_eps(arg)
        #--------------------------------------making a__init__ new tab to efficiently multithread the program---------------------
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        # ---------------------------Using selenium to render and clickk the download button------------------------

        
        # going to the download page
        driver.get(kwik)
        
        # getting the title
        kwik_soup = BeautifulSoup((requests.get(kwik).text),'lxml')
        # filename = kwik_soup.find('h1',class_ = 'title').text.strip()
        size = kwik_soup.find('abbr')['title']
        
        WebDriverWait(driver, 15).until(EC.presence_of_element_located(
            (By.XPATH, "//form[@method = 'POST']/button[contains(@class, 'button')]")))

        element = driver.find_element(
            By.XPATH, "//form[@method = 'POST']/button[contains(@class, 'button')]")


        Banners.start_dl(arg)
    
        try:
            # the first click will click on the ad on the screeen
            ad=driver.find_element(By.XPATH,"/html/body/div[2]/a")
            ad.click()
            # the second click will download the content
            
            n()
        except:
            pass
        n()
        
        #to click the download btton
        element.click()
        Banners.downloading(animepicked,elem)
        progress(size)
        
        
        #return to original window
        driver.switch_to.window(driver.window_handles[0])
        # already downloading
        print(f'Downloading Episode {elem} of {animepicked} NOW!!!!!!!')
        print(f'Already Aired episode : {episto}')
        n()






    
# This function unlike the one above downloads (if there is stable and fast connection) anime concurrently 
def multi_download_optimized(arg):
    arg = str(arg)
    print("\n\nTo make efficient use of the multi download function,\nit is advised you have a very fast and stable internet connection\n")

    print(f'Already aired Episodes : {episto}')

    if '-' in arg:
        # parsing the arg to get individial eps
        epr = list(x for x in arg.split('-'))

        # list of the range of eps
        episodes_list = list(range(int(epr[0]),int(epr[1]) + 1))
        # list of all the pahe win pages in html
        pahe_win_pages= [BeautifulSoup(requests.get(f"https://animepahe.com/play/{session_id}/{jsonpage_dict['data'][int(x)-1]['session']}").content,'lxml')for x in episodes_list]   
        
        
    else:   
        pahe_win_pages= [BeautifulSoup(requests.get(f"https://animepahe.com/play/{session_id}/{jsonpage_dict['data'][int(x)-1]['session']}").content,'lxml')for x in arg.split(',') ]

    ddownlinks = [page.find_all('a',class_='dropdown-item',target="_blank",limit=3) for page in pahe_win_pages]
    # print(ddownlinks)
    
    n()
    
    
    # for link in ddownlinks:
    #     for url in link:
    #         if not (search(r'(360p|1080p|eng)', str(url))):
    #             soup = BeautifulSoup(str(url),'lxml')

    #             href=soup.a['href']
    #             print(href)
    #             n()

    # n()
    
    linkpahe =[BeautifulSoup(str(url),'lxml').a['href'] for link in ddownlinks for url in link if not (search(r'(360p|1080p|eng)', str(url)))]
    
    kwik_link = [(BeautifulSoup(requests.get(link).content,'lxml').find('a',class_ = "redirect"))['href'] for link in linkpahe ]
    
    # print(kwik_link)
    
    # getting the title
    kwik_soup = BeautifulSoup((requests.get(kwik_link).text),'lxml')
    # filename = kwik_soup.find('h1',class_ = 'title').text.strip()
    size = kwik_soup.find('abbr')['title']
    
    
    Banners.getting_eps(arg)
    
    for i,url in enumerate(kwik_link):    
        
        # ---------------------------Using selenium to render and click the download button------------------------
        elem = (arg.split(','))[i]
        
        # going to the download page
        driver.get(url)
        
        Banners.start_dl(arg)
        
        
        WebDriverWait(driver, 15).until(EC.presence_of_element_located(
            (By.XPATH, "//form[@method = 'POST']/button[contains(@class, 'button')]")))

        element = driver.find_element(
            By.XPATH, "//form[@method = 'POST']/button[contains(@class, 'button')]")
        
        
        
        try:
            Banners.downloading(animepicked,elem)
            # the first click will click on the ad on the screeen
            ad=driver.find_element(By.XPATH,"/html/body/div[2]/a")
            print(f"ad clicked for ep {elem}\n")
            ad.click()
            # the second click will download the content
            element.click()
            print(f"element clicked for ep {elem}\n")
            
            n()
        except:
            print(f"click in exception for ep {elem}\n")
            
            element.click()
        
        
        #to click the download btton
        # element.click()


        # already downloading
        progress(size)
        print(f'{animepicked} ep-{elem} Downloading ... ')
        n()
        
        
        
    # wait = WebDriverWait(driver, 10)
    # wait.until(EC.presence_of_element_located((By.XPATH, f'//a[text()="{file_name}"]')))

    # Close the driver
    driver.quit()
    print(f'Downloaded Episode {arg} of {animepicked} !!!!!')

            
def multi_download_classic(eps: str):
    # given arg specifies '-' for range
    if '-'in str(eps):
        # parsing the eps to get individial eps
        epr = list(x for x in eps.split('-'))

        # list of the range of eps
        episodes = list(range(int(epr[0]),int(epr[1]) + 1))
        
    else:
        # classic eps separated by comma, stlink:=str(link)))]
        episodes = [int(x) for x in eps.split(',')]
    
    for ep in episodes:
        download(ep)
        print(f"{animepicked} ep-{ep} downloading")


 

if current_system_os.lower() == "windows": # we need this only in windows
    # get list of currently running firefox processes (for in case -- keyboardInterrupt occurs)
    tasklist = subprocess.check_output(['tasklist', '/fi', 'imagename eq firefox.exe'], shell=True).decode()
    currentFFIDs = re.findall(r"firefox.exe\s+(\d+)", tasklist)

def winKeyInterruptHandler():
    #exit progress bar if initiated
    # close_progress_bar()
        
    #find new firefox processes
    tasklist = subprocess.check_output(['tasklist', '/fi', 'imagename eq firefox.exe'], shell=True).decode()
    newFFIDs = set(re.findall(r"firefox.exe\s+(\d+)", tasklist)).difference(currentFFIDs)

    #kills spawned firefox drivers -- (may also crash some tabs in other firefox sessions)
    taskkill = 'taskkill /f '+''.join(["/pid "+f+" " for f in newFFIDs]).strip()
    subprocess.check_output(taskkill.split(), shell=True)

    print("\nKeyboardInterrupt : Exiting with dirty hands..")
    print("You may experience a tab-crash in your open firefox sessions")  
    


# ----------------------------------------------End of All the Argument Handling----------------------------------------------------------

# To enable interaction with the program instead of command line argument    
def interactive_main():
    
    # Search prompt for search function
    lookup_anime = str(input("Search an anime [e.g 'one piece'] >> "))

    # searching anime with the lookup function
    lookup(lookup_anime)
    
    # selection prompt for the anime search
    select_index = int(input("Select anime index [default : 0] >> "))
    
    # handling the selected anime metadata
    index(select_index)
    
    # summary info on the selected anime
    info = about()
    Banners.i_info(info)
    
    # # browser handling prompt
    browse = str(input("Enter the browser favorite browser [ff,chrome,firefox e.t.c] >> "))
    browser(browse)
    
    # Handling episode to download prompt
    download_type = str(input("""
    Enter the type of download facilty you want
    
    1. s or single_download for single episode download
    2. md or multi_download for multi episode download
    3. v or md_verbose for a verbose variant of the md function
    4. c or md_classic for a classic variant of the md function
    5. i for more in -depth info on the options above 
    
    >> """)
    )
    print("\n")
    ep_to_download = int(input("    Enter episode(s) to download >> "))
    
    switch = {
        1:download(ep_to_download),
        2:multi_download_optimized(ep_to_download),
        3:multi_download_verbose(ep_to_download),
        4:multi_download_classic(ep_to_download),
        5:info,
        's':switch[1],
        'md':switch[2],
        'v':switch[3],
        'c':switch[4],
        'i':switch[5],
        'single_download':download(ep_to_download),
        'multi_download':switch[2],
        'md_verbose':switch[3],
        'md_classic':switch[4],
        'info':switch[5]
    }
    
    # initiating the action for the choice
    switch[download_type]

def command_main(args):

    barg = args.browser
    sarg = args.search
    sharg = args.search_hidden
    iarg = args.index
    sdarg = args.single_download
    mdarg = args.multi_download_optimized
    mdvarg = args.multi_download_verbose
    mdcarg = args.multi_download_classic
    abtarg = args.about
    
    # browser
    if barg:
        browser(barg)
    
    # search function
    if sarg != None:
        lookup(sarg)
    elif type(sarg) == float:
        print("The search argument does not accept a float value")
    else:
        pass

    if bool(sharg) == True:
        search_hidden(sharg)
    elif type(sarg) == float:
        print("The search argument does not accept a float value")
    else:
        pass
    
    # index function
    if iarg != None:
        index(iarg)
    else:
        pass
    
    # About function
    
    if abtarg:
        info = about()
        Banners.anime_info(animepicked,info)
    else:
        pass
    
    # Single_Download function
    if sdarg != None:
        download(sdarg)
    else:
        pass
    
    # Multi_download function(s)
        
    if mdcarg:
        multi_download_classic(mdcarg)
        
    if mdarg:
        multi_download_optimized(mdarg)

        

def main():
    # ===================================== Handling Arguments and other involved function============================================
    parser = argparse.ArgumentParser()

    # Adding all the required arguments

    parser.add_argument(
        '-b', '--browser', help='To select the dglobalesired requests either chrome or firefox. default is chrome')

    parser.add_argument(
        '-s', '--search',type=str, 
        help='Specify the search keyword or Anime name e.g jujutsu kaisen.it returns a match of available anime related to the search word')

    parser.add_argument(
        '-sh', '--search_hidden', help='Less Verbose search function,should be used only the anime and index is known')

    parser.add_argument('-i', '--index', type=int,
                        help='Specify the index of the desired anime from the search results')


    parser.add_argument('-d', '--single_download', type=int,
                        help='Used to download a single episode of an anime')

    parser.add_argument('-md', '--multi_download_optimized',
                        help='Used to download multiple episodes of an anime concurrently,a string of ints separated by commas[FASTER]')

    parser.add_argument('-mdv', '--multi_download_verbose',
                        help='Used to download multiple episodes of an anime and show verbose,a string of ints separated by commas[SLOWER]')

    parser.add_argument('-mdc', '--multi_download_classic',
                        help='[SLOW]Used to download multiple episodes of an anime and show verbose,a string of ints separated by commas,simply uses SD in a loop')

    parser.add_argument('-a', '--about',
                        help='Outputs an overview information on the anime',action='store_true')



    args = parser.parse_args()
    
    if any(vars(args).values()):
        # Command line arguments are present
        command_main(args)
    else:
        # No command line arguments, run interactive mode
        interactive_main()




if __name__ == '__main__':
    # INTRO BANNER
    Banners.header() 
    main()


final_data = {**search_response_dict,**jsonpage_dict}

n()
def data_report(filepath = "autopahe_data.json",data = None):
    if data:
        # Read existing JSON data from file
        with open(filepath, 'r') as json_file:
            existing_data = load(json_file)

        existing_data.update(data)
            
        with open(filepath,"w") as st:
            dump(existing_data,st)


finish = time.perf_counter()

print(f'Finish time is {round(finish-start,2)}\n')


