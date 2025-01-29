#!/usr/bin/env python

import requests
import os
import tqdm
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
from requests.exceptions import ChunkedEncodingError, RequestException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC





def download_with_retries(posturl, params, preheaders, filename, ep, chunk_size=1024, retries=5):
    for attempt in range(1, retries + 1):
        try:
            # Make the request with timeout
            response = requests.post(posturl, data=params, headers=preheaders, stream=True, timeout=30)




            # Extract the filename from the content disposition header
            content_disposition = response.headers.get("content-disposition")
            if content_disposition:
                filename_start = content_disposition.find("filename=")
                if filename_start != -1:
                    filename = content_disposition[filename_start + 9:]


            # If the filename is not extracted, use a default name
            # changing to path is specified, if not the current path
            if not filename:
                filename = "video.mp4"  # Use a default filename if not extracted from headers

            # Check if file exists and set Range header
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                preheaders["Range"] = f"bytes={file_size}-"
            else:
                file_size = 0



            if response.status_code in (200, 206):
                total_size = int(response.headers.get('content-length', 0)) + file_size
                mode = "ab" if response.status_code == 206 else "wb"
                with open(filename, mode) as file, tqdm.tqdm(
                    desc=f'Downloading Episode {ep}',
                    total=total_size,
                    initial=file_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    ncols=80
                ) as progress_bar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        file.write(chunk)
                        progress_bar.update(len(chunk))
                print("Download completed successfully!")
                return
            else:
                print(f"Unexpected status code: {response.status_code}")
        except (ChunkedEncodingError, RequestException) as e:
            print(f"Error during download: {e}")
            if attempt < retries:
                print(f"Retrying... ({attempt}/{retries})")
                time.sleep(5)
            else:
                print("Failed after multiple retries.")
                break

def kwik_download(url: str, browser: str = "firefox", dpath: str = os.getcwd(), chunk_size: int = 10 * 1024, ep=None, animename=None):
    # Change to specified path
    os.chdir(dpath)

    # Generate post URL from URL
    posturl = url.replace("/f/", "/d/")

    # Browser handling
    chrome_guess = ["chrome", "google chrome", "google"]
    ff_guess = ["firefox", "ff", "ffox"]

    if browser.lower() in chrome_guess:
        ch_service = ChromeService("/snap/bin/chromedriver")

        options = webdriver.ChromeOptions()
        options.headless = True

        driver = webdriver.Chrome(service=ch_service, options=options)
    elif browser.lower() in ff_guess:
        ff_service = FirefoxService("/snap/bin/geckodriver")

        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")

        driver = webdriver.Firefox(service=ff_service, options=options)
    else:
        print("Unsupported browser. Please report this issue at https://github.com/haxsysgit/autopahe/issues")
        return 0

    # Interact with the web page
    driver.get(url)

    # Wait until the form is loaded
    try:
        form_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
    except Exception as e:
        print(f"Error: Form not found on the page. {e}")
        driver.quit()
        return 0

    soup = BeautifulSoup(driver.page_source, "lxml")
    form = soup.find("form")

    if not form:
        print("Error: Form not found on the page.")
        driver.quit()
        return 0

    # Extract token
    token = form.find("input", attrs={"type": "hidden"})['value']

    # Get cookies
    cookies = driver.get_cookies()
    cookie_string = ';'.join([cookie['name'] + '=' + cookie['value'] for cookie in cookies])
    driver.quit()  # Quit the driver

    # Prepare headers
    params = {"_token": token}
    preheaders = {
        'Host': 'kwik.si',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': url,  # Ensure dynamic handling
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': '47',
        'Origin': 'https://kwik.si',
        'Connection': 'keep-alive',
        'Cookie': cookie_string,  # Replace dynamically
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
        'TE': 'trailers',
        'Alt-Used': 'kwik.si'
    }

    download_with_retries(posturl, params, preheaders, animename, ep, chunk_size)
   # request handlin


 