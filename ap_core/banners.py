import os
import sys
import shutil
import platform
from colorama import Fore, Style, init
init()

current_system_os = str(sys.platform)

class Banners:
    def header():
        """Display original banner with subtitle like webpage header"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        
        # Original banner
        print('''
              
             db    8    8 88888 .d88b.      888b.    db    8   8 8888 
            dPYb   8    8   8   8P  Y8 ____ 8  .8   dPYb   8www8 8www 
           dPwwYb  8b..d8   8   8b  d8      8wwP'  dPwwYb  8   8 8    
          dP    Yb `Y88P'   8   `Y88P'      8     dP    Yb 8   8 8888 
              
              ''')
        
        # Add subtitle like webpage header
        print(f"{Fore.YELLOW}        ⚡ Anime Downloader with Advanced Features ⚡{Style.RESET_ALL}")
        print()

    def section_header(title, icon="🔍"):
        """Create webpage-like section header with ASCII separators"""
        terminal_width = shutil.get_terminal_size().columns
        section_width = min(terminal_width - 16, 80)  # Leave margin, max 80 chars
        
        # Create separator line
        separator = "o" + "-" * (section_width - 2) + "o"
        
        # Center the title within the section
        title_with_icon = f"{icon} {title}"
        padding = (section_width - len(title_with_icon) - 4) // 2
        title_line = "|" + " " * padding + f"{Fore.CYAN}{title_with_icon}{Style.RESET_ALL}" + " " * (section_width - len(title_with_icon) - padding - 4) + "|"
        
        print("        " + separator)
        print("        " + title_line)
        print("        " + separator)
        print()

    def search_results(results, from_cache=False):
        """Display search results in structured webpage format"""
        resultlen = len(results)
        
        # Section header
        cache_indicator = "⚡" if from_cache else ""
        Banners.section_header(f"Search Results {cache_indicator}", "🔍")
        
        # Results count
        print(f"        {Fore.GREEN}{resultlen}{Style.RESET_ALL} results were found  {Fore.CYAN}--->{Style.RESET_ALL}")
        print()
        
        # Display results with uniform indentation
        for i, result in enumerate(results):
            print(f"        {Fore.MAGENTA}[{i}]{Style.RESET_ALL} : {Fore.CYAN}{result['title']}{Style.RESET_ALL}")
            print("        " + "-" * 60)
            print(f"        {Fore.BLUE}Number of episodes contained{Style.RESET_ALL} : {Fore.YELLOW}{result['episodes']}{Style.RESET_ALL}")
            print(f"        {Fore.BLUE}Current status of the anime{Style.RESET_ALL} : {Fore.GREEN}{result['status']}{Style.RESET_ALL}")
            print(f"        {Fore.BLUE}Year the anime aired{Style.RESET_ALL} : {Fore.YELLOW}{result['year']}{Style.RESET_ALL}")
            print()

    def anime_selection(anime_data):
        """Display anime selection in structured webpage format"""
        Banners.section_header("Anime Information", "📺")
        
        # Center the anime title under the separator
        title = anime_data['title']
        separator_length = 60
        padding = (separator_length - len(title)) // 2
        centered_title = " " * padding + f"{Fore.CYAN}{title}{Style.RESET_ALL}"
        
        print(f"        {centered_title}")
        print("        " + "-" * 60)
        print(f"        {Fore.BLUE}Episodes Available{Style.RESET_ALL} : {Fore.YELLOW}{anime_data.get('episodes', 'N/A')}{Style.RESET_ALL}")
        print(f"        {Fore.BLUE}Anime Homepage{Style.RESET_ALL} : {Fore.CYAN}{anime_data.get('homepage', 'N/A')}{Style.RESET_ALL}")
        print(f"        {Fore.BLUE}Year Released{Style.RESET_ALL} : {Fore.YELLOW}{anime_data.get('year', 'N/A')}{Style.RESET_ALL}")
        print(f"        {Fore.BLUE}Type{Style.RESET_ALL} : {Fore.CYAN}{anime_data.get('type', 'N/A')}{Style.RESET_ALL}")
        print(f"        {Fore.BLUE}Status{Style.RESET_ALL} : {Fore.GREEN}{anime_data.get('status', 'N/A')}{Style.RESET_ALL}")
        print(f"        {Fore.BLUE}Cover Image{Style.RESET_ALL} : {Fore.CYAN}{anime_data.get('image', 'N/A')}{Style.RESET_ALL}")
        print()

    def commands_table():
        """Display available commands in structured format"""
        Banners.section_header("Available Commands", "🔧")
        
        print(f"        {Fore.BLUE}➤ Download:{Style.RESET_ALL} {Fore.YELLOW}-d{Style.RESET_ALL} <episode_number>  (e.g., {Fore.YELLOW}-d 1{Style.RESET_ALL})")
        print(f"        {Fore.BLUE}➤ Multi-download:{Style.RESET_ALL} {Fore.YELLOW}-md{Style.RESET_ALL} <range>  (e.g., {Fore.YELLOW}-md 1-12{Style.RESET_ALL})")
        print(f"        {Fore.BLUE}➤ Get links:{Style.RESET_ALL} {Fore.YELLOW}-l{Style.RESET_ALL} <episode>  (e.g., {Fore.YELLOW}-l 1{Style.RESET_ALL})")
        print(f"        {Fore.BLUE}➤ Back to search:{Style.RESET_ALL} {Fore.YELLOW}-s{Style.RESET_ALL} <new_search>")
        print()

    def download_progress(anime_name, episode):
        """Display download progress in structured format"""
        Banners.section_header("Download Progress", "📥")
        
        print(f"        {Fore.YELLOW}Downloading episode {episode} of {anime_name}{Style.RESET_ALL}")
        print("        " + "-" * 60)
        print()

    def success_message(message):
        """Display success message in structured format"""
        print()  # Add spacing before success message
        print(f"        {Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        print()

    def info_message(message):
        """Display info message in structured format"""
        print(f"        {Fore.BLUE}ℹ️ {message}{Style.RESET_ALL}")
        print()

    def progress_indicator(status="searching"):
        """Display progress indicator at top like webpage"""
        indicators = {
            "searching": f"        {Fore.BLUE}[SEARCHING]{Style.RESET_ALL} 🔍 Finding anime...",
            "loading": f"        {Fore.YELLOW}[LOADING]{Style.RESET_ALL} ⏳ Processing data...",
            "downloading": f"        {Fore.GREEN}[DOWNLOADING]{Style.RESET_ALL} 📥 Fetching episodes...",
            "complete": f"        {Fore.GREEN}[COMPLETE]{Style.RESET_ALL} ✅ Operation finished!"
        }
        
        print(indicators.get(status, indicators["loading"]))

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
