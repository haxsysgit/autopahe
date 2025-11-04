import json
import types
import builtins

import auto_pahe


class _Resp:
    def __init__(self, status_code=200, payload=None, url="https://animepahe.si/api"):
        self.status_code = status_code
        self._payload = payload or {"data": [{"title": "Foo", "episodes": 12, "status": "Finished Airing", "year": 2020, "type": "TV", "session": "abcd", "poster": "/img.jpg"}]}
        self.url = url
        self.content = json.dumps(self._payload).encode()


class _Session:
    def get(self, url, params=None, headers=None, timeout=15):
        return _Resp()


def test_lookup_http_path(monkeypatch):
    # Monkeypatch the request session to avoid real HTTP
    from ap_core import browser as br

    def _fake_session():
        return _Session()

    monkeypatch.setattr(br, "get_request_session", _fake_session)

    # Run lookup; should parse and return dict without falling back to Playwright
    res = auto_pahe.lookup("foo")
    assert isinstance(res, dict)
    assert "data" in res
    assert len(res["data"]) >= 1
