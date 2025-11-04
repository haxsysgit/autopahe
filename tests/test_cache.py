import os
from ap_core.cache import cache_set, cache_get, cache_clear, get_cache_dir


def test_cache_roundtrip(tmp_path, monkeypatch):
    # Isolate cache location
    monkeypatch.setenv("HOME", str(tmp_path))
    cache_dir = get_cache_dir()
    assert os.path.isdir(cache_dir)

    url = "https://example.com/api?q=test"
    data = b"{\"ok\": true}"

    cache_set(url, data)
    got = cache_get(url, max_age_hours=24)
    assert got == data

    # Clear should not raise
    cache_clear(max_age_days=0)
