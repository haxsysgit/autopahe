#! /usr/bin/python3
import time,requests,argparse,os
import sys
from json import loads,load,dump
from re import search
from bs4 import BeautifulSoup
from kwikdown import kwik_download
import concurrent.futures as concur



start = time.perf_counter()

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
            dump(new_data,st)

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
        

# Banner Header
Banners.header()


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

    final_data = {**search_response_dict,**jsonpage_dict}
    data_report(data=final_data)
    n()
    

def about():
        #extract the anime info from a div with class anime-synopsis
        soup = BeautifulSoup((requests.get(episode_page_format).text),'lxml')
        abt = soup.select('.anime-synopsis')
        return abt[0].text.strip()


def download(arg = 1,barg:str = "firefox"):
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
    down_url = kwik.replace("/f/","/d/")
    
    Banners.getting_eps(arg)

    Banners.downloading(animepicked,arg)
    
    kwik_download(url=kwik,posturl=down_url,dpath="/home/haxsys/Downloads",ep=arg)
    
    





# def multi_download_verbose(arg):
#     print("      To make efficient use of the multi download function,\nit is advised you have a very fast and stable internet connection")
    
    
#     n()
    
#     # given arg specifies '-' for range
#     if '-'in str(arg):
#         # parsing the arg to get individial eps
#         epr = list(x for x in arg.split('-'))

#         # list of the range of eps
#         episodes_list = list(range(int(epr[0]),int(epr[1]) + 1))
        
#     else:
#         # classic arg separated by comma
#         episodes_list = [int(x) for x in arg.split(',')]

        
#     for elem in episodes_list:
                
#         episode_session = jsonpage_dict['data'][elem]['session']
            

#         #stream page url format
#         stream_page_url = f'https://animepahe.com/play/{session_id}/{episode_session}'
#         n()
        
#         stream_page_soup = BeautifulSoup(requests.get(f'{stream_page_url}').content,'lxml')
        
#         dload = stream_page_soup.find_all('a',class_='dropdown-item',target="_blank")
        
#         from re import search


#         # for link in dload:
#         #     stlink = str(link)
#         #     match = if not (search(r'(360p|1080p|eng)', stlink))
#         #     if match:
#         #         for link in stlink:
#         #             soup = BeautifulSoup(link, 'html.parser')
#         #             href = soup.a['href']
#         #             print(href)
        
#         # i am sure u are not wise enough to know what is going on
#         #but the code above was shortened to the code below
#         #using walrus operator and list comprehension
#         #and it return a list of chars which when combined will return the link
#         linkpahe = [(BeautifulSoup(stlink, 'html.parser').a['href']) for link in dload if not (search(r'(360p|1080p|eng)', stlink:=str(link)))]
        
#         #the linkpahe variable carries a list of the characters of the link
#         #so the pahewin variable will return the link webpage content
#         pahe_win = requests.get(f'{[ch for ch in linkpahe][0]}').content
        
#         #getting the link to the kwik download page
#         kwik = (BeautifulSoup(pahe_win,'lxml')).find('a', class_='redirect')['href']
#         down_url = kwik.replace("/f/","/d/")

#         Banners.getting_eps(arg)
        
#         Banners.downloading(animepicked,arg)

#         kwik_download(url=kwik,posturl=down_url,dpath="/home/haxsys/Downloads")
        



# This function unlike the one above downloads (if there is stable and fast connection) anime concurrently 
def multi_download_optimized(arg):
    
    arg = str(arg)

    # A new format for list comprehension
    pahe_win_pages = [
        
    num
    for segment in arg.split(",")
    for num in (
        range(int(segment.split("-")[0]), int(segment.split("-")[1]) + 1)
        if "-" in segment
        else [int(segment)]
    )]
    
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
    
    Banners.getting_eps(arg)
    
    Banners.downloading(animepicked,arg)
    # for i,url in enumerate(kwik_link):
    #     down_url = url.replace("/f/","/d/")
        
    #     ep = arg.split(",")[i]
        
    #     Banners.downloading(animepicked,ep)
        
    #     kwik_download(url,down_url,dpath="/home/haxsys/Downloads")
        
    with concur.ThreadPoolExecutor(max_workers=len(kwik_link)) as executor:
        futures = []
        
        for i,url in enumerate(kwik_link):
            down_url = url.replace("/f/","/d/")
            ep = arg.split(",")[i]
            future = executor.submit(kwik_download, url,down_url,dpath="/home/haxsys/Downloads",ep=ep)
            n()
            n()
            futures.append(future)


        # Wait for all tasks to complete
        concur.wait(futures)
        # for future in futures:
        #     future.result()
        
        


    

            
def multi_download_verbose(eps: str):
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
    
    for ep in episodes:
        download(ep)
        print(f"{animepicked} ep-{ep} downloading")

    
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
    
    # Handling episode to download prompt
    download_type = input("""
    Enter the type of download facilty you want
    
    1. s or single_download for single episode download
    2. md or multi_download for multi episode download
    3. v or md_verbose for a verbose variant of the md function[SLOW]
    4. i for more in -depth info on the options above 
    
    >> """)
    print("\n")
    ep_to_download = (input("    Enter episode(s) to download >> "))
    
    switch = {
        1:download,
        2:multi_download_optimized,
        3:multi_download_verbose,
        4:info,
        's':download,
        'md':multi_download_optimized,
        'v':multi_download_verbose,
        'i':info,
        'single_download':download,
        'multi_download':multi_download_optimized,
        'md_verbose':multi_download_verbose,
        'info':info
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
    sharg = args.search_hidden
    iarg = args.index
    sdarg = args.single_download
    mdarg = args.multi_download_optimized
    mdvarg = args.multi_download_verbose
    abtarg = args.about
    
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
        
    if mdvarg:
        multi_download_verbose(mdvarg)
        
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

    parser.add_argument('-mdc', '--multi_download_verbose',
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
    main()
else:
    Banners.header()
    

n()

finish = time.perf_counter()

print(f'Finish time is {round(finish-start,2)}\n')


