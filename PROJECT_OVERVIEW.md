# AutoPahe v3 Overview

AutoPahe is a CLI tool to search AnimePahe, preview anime details, and download episodes. It emphasizes speed (HTTP first, caching, batched Playwright), good UX (colors, emojis), and resilient browser automation.

## Top-level
- auto_pahe.py
  Main CLI entry. Implements commands: search (-s), index (-i), about (-a), single (-d), multi (-md), records (-R/-r), sorting, caching, and setup. Manages browser batching and caching.
- kwikdown.py
  Downloads from kwik links. Used by download() to save episodes.
- pyproject.toml
  Packaging metadata. Defines console script `autopahe` and dependencies. Packages `ap_core` and `features`, and py-modules `auto_pahe`, `kwikdown`.
- requirements.txt
  Dependency list for non-PEP 621 installs.
- README.md
  Project readme (user-facing introduction).
- license.md
  License.

## Core modules (ap_core)
- ap_core/banners.py
  ASCII banners and small helpers (e.g., `Banners.search`, `Banners.select`). `n()` prints one newline.
- ap_core/browser.py
  Shared Playwright context and utilities (`get_pw_context`, `driver_output`, `batch_driver_output`, `cleanup_browsers`). Defaults to Chrome channel, falls back to Chromium.
- ap_core/cache.py
  Disk cache for HTTP responses. Stored under `~/.cache/autopahe`.
- ap_core/config.py
  Load and write INI config. Defaults set Chrome as browser. Sample config at `~/.config/autopahe/config.ini`.
- ap_core/cookies.py
  Cookie/cache clearing helpers.
- ap_core/notifications.py
  Desktop notifications for completed/failed downloads.
- ap_core/parser.py
  Parser fallback for non-JSON API responses.

## Features (features)
- features/manager.py
  Record keeping: process, list, search, update progress, rate, export/import.
- features/manage.py
  Legacy helpers for manager.
- features/pahesort.py
  Rename/organize downloaded files.
- features/execution_tracker.py
  Run-time logging and reporting of execution stats.

## Key flows
- Search: HTTP with caching -> parse -> colored structured list. Fallback to Playwright only if needed.
- Index: Uses prefetch caches when available, prints selected anime info, prints episode range, shows helpful commands.
- About: Prefers prefetched HTML; otherwise fetches via Playwright.
- Downloads: Navigates to episode stream page, picks links >= 720p by default, downloads via kwikdown.
- Batching: `batch_driver_output` fetches multiple URLs in one Playwright session.

## Configuration
- File: `~/.config/autopahe/config.ini` (write via `--write-config` or `--setup`).
- Defaults: Chrome, 720p, 1 worker, no auto-sort.
- Env: `AUTOPAHE_BROWSER` overrides browser (chrome/chromium/firefox).

## Running
- After install: `autopahe -s "naruto" -i 0 -a`
- Dev (editable): `pip install -e .` then `autopahe ...`
- First-time setup: `autopahe --setup`

## Packaging
- Console script: `autopahe` -> `auto_pahe:main`.
- Packages `ap_core` and `features` as namespace packages.
- Includes top-level modules via `py-modules`.

## Logs and cache
- Log: `autopahe.log` (current working directory).
- Disk cache: `~/.cache/autopahe`.
- Playwright profile: `~/.cache/autopahe-pw/{browser}`.

## Known considerations
- Chrome default: will attempt Chrome channel; falls back to Chromium if Chrome is unavailable.
- API domain: tries `.si` then `.com` with proper headers.
