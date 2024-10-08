
<!-- Badges -->
[![PyPI version](https://badge.fury.io/py/autopahe.svg)](https://pypi.org/project/autopahe/)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/haxsysgit/autopahe/)
[![License](https://img.shields.io/github/license/haxsysgit/autopahe?color=brightgreen)](https://github.com/haxsysgit/autopahe/blob/main/license.md)
[![OpenIssues](https://img.shields.io/github/issues/haxsysgit/autopahe?color=important)](https://github.com/haxsysgit/autopahe/issues)
<!--LineBreak-->
[![Windows](https://img.shields.io/badge/Windows-white?style=flat-square&logo=windows&logoColor=blue)](https://github.com/haxsysgit/autopahe/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-white?style=flat-square&logo=ubuntu&logoColor=E95420)](https://github.com/haxsysgit/autopahe/)
<!-- Badges -->
# Autopahe
This is a Python script that can be used to search and download anime episodes from [animepahe](https://animepahe.com/). It uses the `requests`, `beautifulsoup4`, and `selenium` libraries to interact with the website and scrape relevant data.

## Requirements
- Python3
- Any of the main web browser(Chrome,firefox,brave, e.t.c)

## Script dependencies
- Selenium
- BeautifulSoup4
- requests
- webdriver-manager
- tqdm

## Getting Started
1. Make sure you have Python installed in your system
2. Install all dependencies using `pip install -r requirements.txt`
3. Wait for pip to install all required dependencies. Enjoy the script :)
4. Navigate to the project directory and Run `python3 autopahe/auto_pahe.py`

## Usage
- Syntax: `auto_pahe.py -<optional arguments>`
- To run the script, execute `python3 auto_pahe.py`

<!-- ![autopahe](https://user-images.githubusercontent.com/56473062/120795797-922a3b80-c557-11eb-8328-26cfb39f4187.png) -->

## Features
- Search for an anime.
- Select anime from search result.
- Select episodes to download.
- Downloads are made using inbuilt-dlr (default).
- Inbuilt-dlr finds and resumes incomplete downloads by default.

- **Episode Selection Options:**
  <!-- - `0` : downloads all the episodes of the selected anime. -->
  - i : downloads episode i.
    - eg:- `1` : downloads episode 1, `5` downloads episode 5 and so on.
    
  - x-y : downloads episodes from x to y. 
    - eg:- `3-9` : downloads episodes 3 to 9 (3 and 9 inclusive)
    
  - In case of multiple options, each options must be seperated by a `,`
  - Example: `1, 3, 6-11` : downloads episodes 1,3,6,7,8,9,10,11

## Images
![Search Utility Example](imgs/img1_top.png)
![other interaction](imgs/img2_middle.png)
![Finished Downloads](imgs/img3_last.png)



## Command line features
To use the script, run it in your terminal using the following command:

```shell
python auto_pahe.py [-h] [-b BROWSER] [-s SEARCH] [-sh SEARCH_HIDDEN] [-i INDEX] [-sd SINGLE_DOWNLOAD] [-md MULTI_DOWNLOAD_OPTIMIZED] [-mdv MULTI_DOWNLOAD_VERBOSE] [-a ABOUT]
```


Here are the available options:

- `-h`, `--help`: show the help message and exit
- `-s`, `--search`: search for an anime using a keyword. The script will display a list of matching results.
- `-sh`, `--search_hidden`: search for an anime using its name and index. This option is less verbose than the regular search.
- `-i`, `--index`: choose an anime from the search results by its index.
- `-sd`, `--single_download`: download a single episode of an anime by its number.
- `-md`, `--multi_download_optimized`: download multiple episodes of an anime at once using a faster, optimized method. Specify a comma-separated string of episode numbers to download.
- `-a`, `--about`: display an overview of the chosen anime.
- `-r`, `--record`:Interact with the records/database (view, [index], [keyword]).
  

## Example Usage

Here are some example commands to run the script:

To search for an anime
```shell
# To search for an anime
python3 auto_pahe.py -s "One piece"
```
To select an anime from the search result
```shell
# To select an anime from the search result
python3 auto_pahe.py -s "One piece" -i 1
```
To download an episode in the selected anime
```shell
# To download an episode in the selected anime
python3 auto_pahe.py -s "One piece" -i 0 -d 1
```



- **Downloading and Quality :**
  - Files are downloaded to your Default downloads directory.
  - Downloads are taken care of by the inbuilt downloader on default.
  - Currently the download quality priority is only 720p
    <!-- - ie, downloader first checks for 720p video, if 720p is not available checks for 1080p and so on. -->

## Notes
- you need a browser to be installed for this script to work (since the script uses selenium for some of its functions).
- This script is a work under progress and therefore may lack some features, please bear with it, and consider contributing if you have any fixes or improvements :relaxed:. 

- **In Windows** the webdriver if found to misbehave if the script is forced to exit using `ctrl^c`. A good solution to this couldn't be found and a temporary fix have been implemented. And as such, please be noted that if you use ctrl^c to exit, your active firefox sessions or tabs have a good chance of crashing. (Note: ctrl^c doesn't have any issues in Linux)


## Acknowledgments

This script was created by Arinze(haxsys) using the following resources:

- [Animepahe](https://animepahe.com/)
- [Python Requests library](https://requests.readthedocs.io/)
- [Beautiful Soup 4 library](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
