"""Runtime state container for AutoPahe CLI orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutoPaheState:
    """Shared runtime context for a single CLI invocation."""

    session_id: str | None = None
    anime_id: str | None = None
    anime_name: str | None = None
    search_results: dict[str, Any] = field(default_factory=dict)
    episode_page_format: str | None = None
    episode_page_data: dict[str, Any] = field(default_factory=dict)
