from bs4 import BeautifulSoup
import auto_pahe


def test_about_uses_prefetched_html(monkeypatch):
    # Prepare prefetched HTML and episode page URL
    url = 'https://animepahe.com/anime/xyz'
    html = '<div class="anime-synopsis">Hello world synopsis</div>'
    auto_pahe.episode_page_format = url
    auto_pahe._prefetched_pages[url] = html

    # Should parse from prefetched, not call driver_output
    got = auto_pahe.about()
    assert got == 'Hello world synopsis'
