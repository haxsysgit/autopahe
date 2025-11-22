#!/usr/bin/env python3

import requests                # For sending HTTP requests and managing sessions
import os                      # For file/directory management
import tqdm                    # For progress bar during file download
import time                    # For delay/retries
from pathlib import Path
from bs4 import BeautifulSoup  # For parsing HTML content
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
from ap_core.browser import get_pw_context


def setup_session(retries=5):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def download_with_retries(session, posturl, params, headers, filename, ep, chunk_size=1024 * 300, retries=5):
    for attempt in range(1, retries + 1):
        try:
            # Check for partial file and set resume header BEFORE request
            file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
            if file_size:
                headers["Range"] = f"bytes={file_size}-"

            # Send request
            response = session.post(posturl, data=params, headers=headers, stream=True, timeout=30)

            if response.status_code == 403:
                print("403 Forbidden: Server blocked the request.")
                print(f"  UA: {headers.get('User-Agent','')[:120]}")
                print(f"  Origin: {headers.get('Origin','')}")
                print(f"  Referer: {headers.get('Referer','')}")
                print(f"  Post URL: {posturl}")
                print(f"  Hints: Ensure the kwik form token is valid and not expired; try again after a short wait.")
                return
            if response.status_code not in (200, 206):
                print(f"Unexpected status code: {response.status_code}")
                print(f"  UA: {headers.get('User-Agent','')[:120]}")
                print(f"  Origin: {headers.get('Origin','')}")
                print(f"  Referer: {headers.get('Referer','')}")
                print(f"  Post URL: {posturl}")
                return

            # Extract filename (prefer server-provided name)
            content_disposition = response.headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[-1].strip('"')
            if not filename:
                filename = "video.mp4"

            # Total size = server content + local file (for resume)
            total_size = int(response.headers.get("content-length", 0)) + file_size
            mode = "ab" if file_size else "wb"

            # Begin download with progress bar
            with open(filename, mode) as f, tqdm.tqdm(
                total=total_size, initial=file_size, unit='B',
                unit_scale=True, desc=f"Episode {ep}",
                ncols=80, unit_divisor=1024
            ) as bar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
            return  # Success
        except Exception as e:
            print(f"Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(3)
            else:
                print("Download failed after all retries.")
                return

def kwik_download(url, browser="chrome", dpath=os.getcwd(), chunk_size=1024 * 300, ep=None, animename=None):
    os.chdir(dpath)

    # Handle pahe.win redirect pages
    if 'pahe.win' in url:
        if 'is_verbose' in globals() and is_verbose():
            print(f'Debug: Detected pahe.win redirect page, extracting final URL...')
        browser_choice = (os.environ.get('AUTOPAHE_BROWSER') or browser or 'chrome').lower()
        try:
            context = get_pw_context(browser_choice, headless=True)
            if context is None:
                print('Playwright context not available')
                return
            page = context.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for the redirect link to be available and extract it
            try:
                # Wait for countdown to complete (up to 10 seconds)
                page.wait_for_function('document.querySelector("a.redirect").href.includes("kwik.cx")', timeout=10000)
                redirect_url = page.eval_on_selector('a.redirect', 'el => el.href')
                if 'is_verbose' in globals() and is_verbose():
                    print(f'Debug: Extracted redirect URL: {redirect_url}')
                url = redirect_url
                page.close()
            except Exception as e:
                if 'is_verbose' in globals() and is_verbose():
                    print(f'Debug: Failed to extract redirect URL after countdown: {e}')
                # Fallback: extract from JavaScript
                try:
                    js_content = page.content()
                    import re
                    kwik_match = re.search(r'kwik\.cx/f/([a-zA-Z0-9]+)', js_content)
                    if kwik_match:
                        redirect_url = f"https://kwik.cx/f/{kwik_match.group(1)}"
                        if 'is_verbose' in globals() and is_verbose():
                            print(f'Debug: Extracted redirect URL from JavaScript: {redirect_url}')
                        url = redirect_url
                        page.close()
                    else:
                        if 'is_verbose' in globals() and is_verbose():
                            print('Debug: Could not find kwik.cx URL in JavaScript')
                        page.close()
                        return
                except Exception as js_e:
                    if 'is_verbose' in globals() and is_verbose():
                        print(f'Debug: Failed to extract from JavaScript: {js_e}')
                    page.close()
                    return
        except Exception as e:
            print(f'Failed to handle pahe.win redirect: {e}')
            return

    posturl = url.replace("/f/", "/d/")  # Build POST endpoint based on pattern

    token = None
    session = setup_session()  # Robust session with retries

    # Use Playwright to get token and cookies
    browser_choice = (os.environ.get('AUTOPAHE_BROWSER') or browser or 'chrome').lower()
    user_data_dir = str(Path.home() / '.cache' / 'autopahe-pw' / browser_choice)
    try:
        context = get_pw_context(browser_choice, headless=True)
        if context is None:
            print('Playwright context not available')
            return
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        # Wait for form and potential countdown
        try:
            page.wait_for_selector('form', timeout=10000)
        except Exception:
            pass
        time.sleep(3)

        soup = BeautifulSoup(page.content(), 'lxml')
        form = soup.find('form')
        if not form:
            # Debug: Save HTML content to file for inspection
            debug_file = str(Path.home() / "autopahe_debug" / f"kwik_debug_{int(time.time())}.html")
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page.content())
            print(f'Could not locate download form on kwik page')
            if 'is_verbose' in globals() and is_verbose():
                print(f'Debug: Page content saved to {debug_file}')
                print(f'Debug: URL was: {url}')
                print(f'Debug: Page title: {page.title()}')
            
                # Check for common anti-bot indicators
                content_lower = page.content().lower()
                if 'cloudflare' in content_lower:
                    print('Debug: Cloudflare protection detected')
                if 'captcha' in content_lower:
                    print('Debug: CAPTCHA detected')
                if 'blocked' in content_lower or 'access denied' in content_lower:
                    print('Debug: Access blocked detected')
                
                # Also print first 1000 characters of page content for immediate inspection
                print(f'Debug: First 1000 chars of page content:')
                print(page.content()[:1000])
            
            page.close()
            return
        hidden = form.find('input', {'type': 'hidden'})
        if not hidden or not hidden.get('value'):
            page.close()
            print('Could not extract CSRF token')
            return
        token = hidden['value']
        # Capture the actual browser user agent from Playwright
        try:
            ua = page.evaluate("navigator.userAgent") or ""
        except Exception:
            ua = ""

        # Transfer cookies from Playwright to requests.Session
        try:
            cookies = context.cookies([url])
        except Exception:
            cookies = context.cookies()
        for c in cookies:
            domain = c.get('domain') or 'kwik.si'
            session.cookies.set(c['name'], c['value'], domain=domain)
        page.close()
    except Exception as e:
        print('Playwright failed to capture token/cookies:', e)
        return

    # Construct realistic headers (mimic the browser actually used)
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    is_chromium = 'chrome' in browser_choice or 'chromium' in browser_choice

    headers = {
        'User-Agent': ua or (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' if is_chromium
            else 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': url,               # refer back to the /f/ page
        'Origin': origin,             # must match the kwik host
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    if is_chromium:
        headers.update({
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Google Chrome";v="120", "Chromium";v="120", "Not=A?Brand";v="99"',
            'Sec-Ch-Ua-Platform': '"Linux"',
            'Sec-Ch-Ua-Mobile': '?0',
        })

    # Token included in form body
    params = {"_token": token}

    # Call the actual download function
    download_with_retries(session, posturl, params, headers, animename, ep, chunk_size)
