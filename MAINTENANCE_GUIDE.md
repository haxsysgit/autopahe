# AutoPahe Maintenance & Troubleshooting Guide

This guide helps you quickly navigate the codebase, diagnose issues, and ship releases.

## Where to start when things break
- Search not returning results
  - Entry: `lookup()` in `auto_pahe.py`
  - Network: `ap_core/browser.py#get_request_session()` (shared session, headers)
  - API fallback order: `.si` → `.com` → `.ru`
  - Browser fallback: `ap_core/browser.py#driver_output()`
  - Disk cache: `ap_core/cache.py` (stored under `~/.cache/autopahe`)
  - Tips: try `--verbose`, `--cache clear`, verify Playwright installed, and try again.

- Index/episodes missing or slow
  - Entry: `index()` in `auto_pahe.py`
  - Prefetch: `batch_driver_output()` used in `command_main()`
  - HTTP JSON path first, then Playwright fallback
  - Cache keys: `anime_url_format` persisted in memory and disk caches

- About/info missing
  - Entry: `about()` in `auto_pahe.py`
  - Prefers prefetched HTML, else `driver_output(..., content=True)`
  - DOM selector: `.anime-synopsis`

- Download issues
  - Entry: `download()` in `auto_pahe.py`
  - Navigates stream page, finds quality links (`.dropdown-item`), then goes to kwik
  - Final link: anchor with class `redirect`
  - If site layout changes, update selectors here.

- Records, sorting, notifications
  - Records: `features/manager.py`
  - Sorting: `features/pahesort.py`
  - Notifications: `ap_core/notifications.py`

## Logging & Debugging
- Use `--verbose` for DEBUG logs or `--quiet` to suppress noise.
- Logs written to `autopahe.log` in CWD.
- For headless/browser logs, run Playwright in non-headless (default) and check console.

## Configuration
- File: `~/.config/autopahe/config.ini` (write with `--write-config` or `--setup`).
- Defaults: Chrome, 720p, 1 worker.
- Env override: `AUTOPAHE_BROWSER` (chrome/chromium/firefox).

## Performance notes
- HTTP first with pooled `requests.Session`, browser only as fallback.
- Disk cache for search/episodes for speed.
- Shared Playwright persistent context avoids many browser spawns.
- Optional improvement: replace fixed waits in `download()` with `wait_for_selector` on link elements.

## Releasing to PyPI
1. Bump version in `pyproject.toml`.
2. Clean artifacts: `rm -rf dist build autopahe.egg-info`.
3. Build: `python -m build`.
4. Upload: `twine upload dist/*`.
5. Tag & push: `git tag vX.Y.Z && git push --tags`.
6. Post-install check:
   - `pip install -U autopahe` (or `uv tool install autopahe`)
   - `autopahe --setup`
   - `autopahe -s "naruto" -i 0 -a`

## Quick map
- `auto_pahe.py`: CLI entry, high-level flow, arg parsing.
- `ap_core/`: browser, cache, config, notifications, banners, parser.
- `features/`: records, sorting, execution tracking.
- `kwikdown.py`: downloads from kwik.
- `pyproject.toml`: packaging and console script.
