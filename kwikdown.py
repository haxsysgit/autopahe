#!/usr/bin/env python

import os
import time
import requests
import tqdm
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from requests.exceptions import ChunkedEncodingError, RequestException

# Download function that retries a few times if there's a network error
def download_with_retries(download_url, referer, filename, ep, chunk_size=1024, retries=5):
    parsed = urlparse(download_url)
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': parsed.netloc,
        'Referer': referer,
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0',
        'Priority': 'u=0, i'
    }

    for attempt in range(1, retries + 1):
        try:
            # Attempt the download
            r = requests.get(download_url, headers=headers, stream=True, timeout=30)

            # Extract filename if provided
            cd = r.headers.get('content-disposition', '')
            if 'filename=' in cd:
                filename = cd.split('filename=')[1].strip('"')

            # Use fallback filename if none provided
            if not filename:
                filename = f'episode_{ep}.bin'

            # Determine if we're resuming or starting fresh
            mode = 'ab' if os.path.exists(filename) else 'wb'
            start = os.path.getsize(filename) if mode == 'ab' else 0
            if mode == 'ab':
                headers['Range'] = f'bytes={start}-'

            # Determine full file size
            total = int(r.headers.get('content-length', 0)) + start

            # Proceed if status is OK or partial content
            if r.status_code in (200, 206):
                with open(filename, mode) as f, tqdm.tqdm(
                    desc=f'Downloading Episode {ep}',
                    total=total,
                    initial=start,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    ncols=80
                ) as bar:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))
                return
            else:
                print(f'Unexpected status code: {r.status_code}')
        except (ChunkedEncodingError, RequestException) as e:
            print(f'Error during download: {e}')
            if attempt < retries:
                print(f'Retrying... ({attempt}/{retries})')
                time.sleep(5)
            else:
                print('Failed after multiple retries.')
                break

# Main handler function
def kwik_download(url: str, browser: str = 'firefox', dpath: str = os.getcwd(), chunk_size: int = 10*1024, ep=None, animename=None):
    os.chdir(dpath)  # Change to download directory
    posturl = url.replace('/f/', '/d/')  # Convert to POST submission URL

    # Choose browser automation engine
    if browser.lower() in ['chrome', 'google chrome', 'google']:
        svc = ChromeService('/snap/bin/chromedriver')
        opts = webdriver.ChromeOptions()
        opts.add_argument('--headless')
        driver = webdriver.Chrome(service=svc, options=opts)
    elif browser.lower() in ['firefox', 'ff', 'ffox']:
        svc = FirefoxService('/snap/bin/geckodriver')
        opts = webdriver.FirefoxOptions()
        opts.add_argument('--headless')
        driver = webdriver.Firefox(service=svc, options=opts)
    else:
        print('Unsupported browser. Please report this issue at https://github.com/haxsysgit/autopahe/issues')
        return

    # Load the webpage
    driver.get(url)

    # Wait for the form to load (token usually inside)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
    except Exception as e:
        print(f'Error: Form not found on the page. {e}')
        driver.quit()
        return

    # Extract form and token
    soup = BeautifulSoup(driver.page_source, 'lxml')
    form = soup.find('form')
    if not form:
        print('Error: Form not found on the page.')
        driver.quit()
        return

    token = form.find('input', attrs={'type': 'hidden'})['value']
    
    # Collect cookies from the browser
    cookies = driver.get_cookies()
    cookie_string = ';'.join([c['name'] + '=' + c['value'] for c in cookies])
    driver.quit()

    # Prepare POST request to submit form and get redirect
    params = {'_token': token}
    post_headers = {
        'Host': urlparse(url).netloc,
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0',
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': url,
        'Origin': f'{urlparse(url).scheme}://{urlparse(url).netloc}',
        'Connection': 'keep-alive',
        'Cookie': cookie_string
    }

    # Send the POST request
    response = requests.post(posturl, data=params, headers=post_headers, allow_redirects=False, timeout=30)

    # If we receive a redirect, that's our file
    if response.status_code in (301, 302) and 'Location' in response.headers:
        download_url = response.headers['Location']
        download_with_retries(download_url, url, animename, ep, chunk_size)
    else:
        print(f'Error: Expected redirect, got {response.status_code}')