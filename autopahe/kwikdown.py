#!/usr/bin/env python


import requests,os,tqdm,time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as chrome_service
from selenium.webdriver.chrome.service import Service as ff_service
# from webdriver_manager.firefox import GeckoDriverManager
# from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

    
    
    




def kwik_download(url:str,posturl:str,browser: str = "firefox",dpath:str = os.getcwd(),chunk_size: int = 160 * 1024,ep=None):
    # browser handling
    chrome_guess = ["chrome","Chrome","google chrome","google"]
    ff_guess = ["ff","firefox","ffgui","ffox","fire"]
    
    if browser.lower() in chrome_guess:
        chserv = chrome_service("/snap/bin/geckodriver")
        
        options = webdriver.ChromeOptions()
        options.headless = True
        
        driver = webdriver.Chrome(service = chserv,options=options)
        
    elif browser.lower() in ff_guess:
        ffserv = ff_service("/snap/bin/geckodriver")
        
        options = webdriver.FirefoxOptions()
        options.headless = True
        
        driver = webdriver.Firefox(service=ffserv,options=options)
    else:
        print(f"Sorry your browser is not supported :( ,\nfeel free to report the issue at https://github.com/haxsysgit/autopahe/issues")
        return 0
    
    driver.get(url)
    
    # Extract the page source
    page_source = driver.page_source
    
    # Create a BeautifulSoup object from the page source
    soup = BeautifulSoup(page_source, "html.parser")
    
    # Find the form element
    form = soup.find("form")
    
    # Find the hidden input element within the form and Extract the value attribute of the hidden input
    token = form.find("input", attrs={"type": "hidden"})['value']
    
    # Navigate to the desired page
    driver.get(posturl)

    # Get the cookies
    cookies = driver.get_cookies()

    # Combine cookies into a single string
    cookie_string = ';'.join([cookie['name'] + '=' + cookie['value'] for cookie in cookies])

    # Quit the driver
    driver.quit()
    
    # request handlin
    params = {"_token":token}
    kwikhead = {
        'Host': 'kwik.cx',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': url,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': '47',
        'Origin': 'https://kwik.cx',
        'Alt-Used': 'kwik.cx',
        'Connection': 'keep-alive',
        'Cookie': cookie_string,
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'TE': 'trailers'
    }
    
    response = requests.post(posturl,data=params,headers=kwikhead,stream=True)
    
    total_size = int(response.headers.get('content-length', 0))

    
    if response.status_code == 200:
        # Retrieve the content disposition header
        content_disposition = response.headers.get("content-disposition")
        filename = None

        # Extract the filename from the content disposition header
        if content_disposition:
            filename_start = content_disposition.find("filename=")
            if filename_start != -1:
                filename = content_disposition[filename_start + 9:]

        # If the filename is not extracted, use a default name
        # changing to path is specified, if not the current path
        os.chdir(dpath)
        if not filename:
            filename = "video.mp4"
        
        # Save the content to a file
        with open(filename, "wb") as file,tqdm.tqdm(
            desc=f'Downloading ep {ep}',
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            ncols=80
        ) as progress_bar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)
                progress_bar.update(len(chunk))


    else:
        print("Failed to download the MP4 file.\n")
        print(f"return code : {response.status_code}")
        


