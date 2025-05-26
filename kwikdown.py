#!/usr/bin/env python3

import requests                # For sending HTTP requests and managing sessions
import os                     # For file/directory management
import tqdm                   # For progress bar during file download
import time                   # For delay/retries
from bs4 import BeautifulSoup # For parsing HTML content
from selenium import webdriver  # For controlling a real browser (headless)
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait         # To wait for elements to load
from selenium.webdriver.support import expected_conditions as EC

# Download the file with retry support
def download_with_retries(session, posturl, params, headers, filename, ep, chunk_size=1024, retries=5):
    for attempt in range(1, retries + 1):
        try:
            # Send POST request to download link with token and headers
            response = session.post(posturl, data=params, headers=headers, stream=True, timeout=30)
            # print(response.headers)

            if response.status_code == 403:
                print("403 Forbidden: Check headers, token, or wait timing.")
                return

            if response.status_code not in (200, 206):
                print(f"Unexpected status code: {response.status_code}")
                return

            # Extract filename from headers if not set
            content_disposition = response.headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[-1].strip('"')

            if not filename:
                filename = "video.mp4"

            # Resume logic: calculate size of partially downloaded file
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            if file_size:
                headers["Range"] = f"bytes={file_size}-"  # Add Range header for resuming
            total_size = int(response.headers.get("content-length", 0)) + file_size

            mode = "ab" if file_size else "wb"  # Append or write new
            with open(filename, mode) as f, tqdm.tqdm(
                total=total_size, initial=file_size, unit='B', unit_scale=True,
                desc=f"Episode {ep}", ncols=80, unit_divisor=1024
            ) as bar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
            return
        except Exception as e:
            print(f"Error during download: {e}")
            if attempt < retries:
                time.sleep(3)  # Wait and retry
            else:
                print("Download failed.")
                return


def kwik_download(url, browser="firefox", dpath=os.getcwd(), chunk_size=1024 * 10, ep=None, animename=None):
    os.chdir(dpath)  # Change to download directory
    posturl = url.replace("/f/", "/d/")  # Build POST endpoint based on pattern

    # Set up headless Firefox browser via Selenium
    service = FirefoxService(executable_path="/snap/bin/geckodriver")
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")  # Run without GUI
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)  # Open the kwik.si file page

    try:
        # Wait until the form appears (ensures JS executed)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "form")))
        time.sleep(5)  # Additional wait for countdowns to complete

        # Parse the current page source to extract the form
        soup = BeautifulSoup(driver.page_source, "lxml")
        form = soup.find("form")
        token = form.find("input", {"type": "hidden"})["value"]  # Extract CSRF token
    except Exception as e:
        print("Could not find token:", e)
        driver.quit()
        return

    # Capture all cookies from the browser into the requests session
    selenium_cookies = driver.get_cookies()
    driver.quit()

    session = requests.Session()  # Persistent session for reuse
    for cookie in selenium_cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', 'kwik.si'))

    # Construct realistic headers (mimic real browser)
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': url,               # Crucial: refers back to original /f/ page
        'Origin': 'https://kwik.si',  # Must match site
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i',
        'Content-Type': 'application/x-www-form-urlencoded',

        # Extra headers that help evade bot detection
        'Sec-Ch-Ua': '"Firefox";v="138", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Ch-Ua-Mobile': '?0',
    }

    # Token included in form body
    params = {"_token": token}

    # Call the actual download function
    download_with_retries(session, posturl, params, headers, animename, ep, chunk_size)
