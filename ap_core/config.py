import os
import configparser
from pathlib import Path
from typing import List, Optional

from ap_core.platform_paths import get_config_dir, get_legacy_config_locations, is_windows

def _get_default_config_locations() -> List[Path]:
    """Get platform-appropriate config file locations."""
    locations = [
        get_config_dir() / "config.ini",
    ]
    # Add legacy locations for backwards compatibility
    locations.extend(get_legacy_config_locations())
    # Also check current working directory
    locations.append(Path.cwd() / "autopahe.ini")
    return locations

DEFAULT_LOCATIONS = _get_default_config_locations()

DEFAULTS = {
    "browser": "chrome",
    "resolution": "720",
    "workers": "1",
    "download_dir": "",
    "sort_on_complete": "false",
    "sort_mode": "",
    "sort_path": "",
}

SUPPORTED_BROWSERS = {"chrome", "chromium", "firefox"}
SUPPORTED_RESOLUTIONS = {"360", "480", "720", "1080", "best", "worst"}


def _coerce_bool(v: str) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_resolution(v: str, warnings: List[str]) -> str:
    raw = "" if v is None else str(v).strip().lower()
    if not raw:
        return DEFAULTS["resolution"]

    if raw.endswith("p") and raw[:-1].isdigit():
        raw = raw[:-1]
    if raw.isdigit():
        raw = str(int(raw))

    if raw in SUPPORTED_RESOLUTIONS:
        return raw

    warnings.append(
        f"Invalid resolution/quality '{v}'. Supported: {sorted(SUPPORTED_RESOLUTIONS)}. Falling back to {DEFAULTS['resolution']}."
    )
    return DEFAULTS["resolution"]


def _normalize_workers(v: str, warnings: List[str]) -> str:
    raw = "" if v is None else str(v).strip()
    if not raw:
        return DEFAULTS["workers"]
    try:
        n = int(raw)
        if n < 1:
            raise ValueError("workers must be >= 1")
        return str(n)
    except Exception:
        warnings.append(f"Invalid workers '{v}'. Falling back to {DEFAULTS['workers']}.")
        return DEFAULTS["workers"]


def _normalize_browser(v: str, warnings: List[str]) -> str:
    raw = "" if v is None else str(v).strip().lower()
    if not raw:
        return DEFAULTS["browser"]
    if raw in SUPPORTED_BROWSERS:
        return raw
    warnings.append(
        f"Invalid browser '{v}'. Supported: {sorted(SUPPORTED_BROWSERS)}. Falling back to {DEFAULTS['browser']}."
    )
    return DEFAULTS["browser"]


def load_app_config(explicit_path: Optional[str] = None):
    candidates = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    candidates.extend(DEFAULT_LOCATIONS)

    warnings: List[str] = []
    if explicit_path:
        try:
            p0 = Path(explicit_path)
            if not p0.exists():
                warnings.append(
                    f"Config path '{explicit_path}' does not exist. Falling back to default config locations."
                )
        except Exception as e:
            warnings.append(
                f"Config path '{explicit_path}' could not be checked ({e}). Falling back to default config locations."
            )
    cfg = configparser.ConfigParser(
        interpolation=None,
        inline_comment_prefixes=(";", "#"),
    )
    path_used = None
    for p in candidates:
        try:
            if p and p.exists():
                cfg.read(p, encoding="utf-8")
                path_used = str(p)
                break

        except Exception as e:
            warnings.append(f"Failed to read config file '{p}': {e}. Ignoring this file.")
            continue

    section = cfg["defaults"] if cfg.has_section("defaults") else {}

    result = DEFAULTS.copy()
    result.update({k: section.get(k, result.get(k, "")) for k in DEFAULTS.keys()})

    # Backwards/alternate key support
    if (not result.get("resolution")) and cfg.has_option("defaults", "quality"):
        result["resolution"] = section.get("quality", result.get("resolution", ""))

    # Normalize and validate (never raise)
    result["browser"] = _normalize_browser(result.get("browser"), warnings)
    result["resolution"] = _normalize_resolution(result.get("resolution"), warnings)
    result["workers"] = _normalize_workers(result.get("workers"), warnings)
    result["download_dir"] = str(result.get("download_dir") or "").strip()
    result["sort_on_complete"] = "true" if _coerce_bool(result.get("sort_on_complete")) else "false"
    result["sort_mode"] = str(result.get("sort_mode") or "").strip()
    result["sort_path"] = str(result.get("sort_path") or "").strip()

    # Validate download_dir and sort_path are usable directories if set
    if result.get("download_dir"):
        try:
            d = Path(result["download_dir"]).expanduser()
            d.mkdir(parents=True, exist_ok=True)
            if not d.is_dir():
                raise OSError("not a directory")
            result["download_dir"] = str(d)
        except Exception as e:
            warnings.append(
                f"Invalid download_dir '{result.get('download_dir')}' ({e}). Falling back to default Downloads directory."
            )
            result["download_dir"] = ""

    if result.get("sort_path"):
        try:
            s = Path(result["sort_path"]).expanduser()
            s.mkdir(parents=True, exist_ok=True)
            if not s.is_dir():
                raise OSError("not a directory")
            result["sort_path"] = str(s)
        except Exception as e:
            warnings.append(
                f"Invalid sort_path '{result.get('sort_path')}' ({e}). Ignoring sort_path."
            )
            result["sort_path"] = ""

    return result, path_used, warnings


def write_sample_config(path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(sample_config_text())
    return str(p)


def sample_config_text() -> str:
    """Generate sample config with platform-appropriate examples."""
    if is_windows():
        download_example = r"# Example: C:\Users\YourName\Downloads"
        sort_example = r"# Example: C:\Users\YourName\Videos\Anime"
    else:
        download_example = "# Example: /home/you/Downloads (Linux) or /Users/you/Downloads (macOS)"
        sort_example = "# Example: /home/you/Videos/Anime"
    
    return f"""# AutoPahe configuration
[defaults]
# Default browser: chrome, chromium, or firefox
browser = chrome

# Default resolution: 360, 480, 720, 1080, best, worst
resolution = 720

# Default workers for multi-download (use >1 with caution)
workers = 1

# Optional download directory override (leave empty to use OS default Downloads)
{download_example}
download_dir = 

# Optional: automatically sort after downloads (not enabled by default)
sort_on_complete = false

# Optional: preferred sort mode when enabled: all | rename | organize
sort_mode = 

# Optional: sort path override (leave empty to use download_dir or OS default)
{sort_example}
sort_path = 
"""
