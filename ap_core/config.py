import os
import configparser
from pathlib import Path

DEFAULT_LOCATIONS = [
    Path.home() / ".config" / "autopahe" / "config.ini",
    Path.home() / ".autopahe.ini",
    Path.cwd() / "autopahe.ini",
]

DEFAULTS = {
    "browser": "chrome",
    "resolution": "720",
    "workers": "1",
    "download_dir": "",
    "sort_on_complete": "false",
    "sort_mode": "",
    "sort_path": "",
}


def _coerce_bool(v: str) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def load_app_config(explicit_path: str | None = None):
    candidates = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    candidates.extend(DEFAULT_LOCATIONS)

    cfg = configparser.ConfigParser()
    path_used = None
    for p in candidates:
        try:
            if p and p.exists():
                cfg.read(p)
                path_used = str(p)
                break
        except Exception:
            continue

    section = cfg["defaults"] if cfg.has_section("defaults") else {}

    result = DEFAULTS.copy()
    result.update({k: section.get(k, result.get(k, "")) for k in DEFAULTS.keys()})

    # Normalize
    result["workers"] = str(result.get("workers") or "1")
    result["download_dir"] = str(result.get("download_dir") or "")
    result["sort_on_complete"] = str(result.get("sort_on_complete") or "false")

    return result, path_used


def write_sample_config(path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(sample_config_text())
    return str(p)


def sample_config_text() -> str:
    return (
        """# AutoPahe configuration
[defaults]
# Default browser: chrome or firefox
browser = chrome

# Default resolution: 480, 720, 1080
resolution = 720

# Default workers for multi-download (use >1 with caution)
workers = 1

# Optional download directory override (leave empty to use OS default Downloads)
# Example: /home/you/Downloads
# On Windows: C:\\Users\\you\\Downloads
# On macOS: /Users/you/Downloads
# On Linux: /home/you/Downloads
download_dir = 

# Optional: automatically sort after downloads (not enabled by default)
sort_on_complete = false

# Optional: preferred sort mode when enabled: all | rename | organize
sort_mode = 

# Optional: sort path override (leave empty to use download_dir or OS default)
sort_path = 
"""
    )
