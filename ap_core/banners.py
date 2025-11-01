import os
import sys

current_system_os = str(sys.platform)

class Banners:
    def header():
        os.system('cls' if current_system_os.lower() == 'windows' else 'clear')
        print('''
              
             db    8    8 88888 .d88b.      888b.    db    8   8 8888 
            dPYb   8    8   8   8P  Y8 ____ 8  .8   dPYb   8www8 8www 
           dPwwYb  8b..d8   8   8b  d8      8wwP'  dPwwYb  8   8 8    
          dP    Yb `Y88P'   8   `Y88P'      8     dP    Yb 8   8 8888 
              
              ''')

    def search(anime=None):
        print(f'''
        ----------------------------------------
            Searching for {anime}..
        ----------------------------------------
        ''')

    def downloading(anime=None, eps=None):
        print(f'''
        ----------------------------------------
            Downloading episode {eps} of {anime}..
        ----------------------------------------
        ''')

    def select(anime, eps=None, anipage=None, year=None,
               atype=None, img=None, status=None):
        print(f'''
        ----------------------------------------
                Selected  {anime}..
        ----------------------------------------
        
        - Episodes Available : {eps}
        - Anime Hompage : {anipage}
        - Year released : {year}
        - Type of anime (TV , Movie , ONA or OVA) : {atype}
        - Cover image : {img}
        - Status : {status}
        
        ''')

    def anime_info(anim=None, abt=None):
        print(f'''
        ----------------------------------------
            ABOUT {anim}
        ----------------------------------------
        
        {abt}
        
        ''')

    def i_info(summary=None):
        print(f'''
        ----------------------------------------
            Summary on Anime
        ----------------------------------------
        
        {summary}
        
        ''')


def n():
    print()
