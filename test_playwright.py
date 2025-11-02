from pathlib import Path
from playwright.sync_api import sync_playwright

def pw_get_body_text(url: str, wait_ms: int = 10000, headless: bool = False, user_data_dir: str = "~/.cache/autopahe-pw"):
    user_data_dir = str(Path(user_data_dir).expanduser())
    with sync_playwright() as p:
        context = p.firefox.launch_persistent_context(user_data_dir, headless=headless)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(wait_ms)  # simple deterministic wait
        text = page.evaluate("document.body.innerText")
        context.close()
        return text

if __name__ == "__main__":
    print(pw_get_body_text("https://animepahe.si/api?m=search&q=naruto", wait_ms=10000, headless=False))