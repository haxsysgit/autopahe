"""
Collection Data Models
======================
Defines data structures for anime collection management.
"""

import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field


class WatchStatus(Enum):
    """Enum for anime watch status."""
    UNWATCHED = "unwatched"
    WATCHING = "watching"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    DROPPED = "dropped"
    PLAN_TO_WATCH = "plan_to_watch"
    
    @classmethod
    def from_string(cls, value: str) -> 'WatchStatus':
        """Convert string to WatchStatus."""
        value = value.lower().replace(' ', '_').replace('-', '_')
        for status in cls:
            if status.value == value:
                return status
        return cls.UNWATCHED
    
    def display_name(self) -> str:
        """Get display-friendly name."""
        return self.value.replace('_', ' ').title()


class AnimeType(Enum):
    """Enum for anime type."""
    TV = "TV"
    MOVIE = "Movie"
    OVA = "OVA"
    ONA = "ONA"
    SPECIAL = "Special"
    MUSIC = "Music"
    UNKNOWN = "Unknown"
    
    @classmethod
    def from_string(cls, value: str) -> 'AnimeType':
        """Convert string to AnimeType."""
        value = value.upper().strip()
        for anime_type in cls:
            if anime_type.value.upper() == value or anime_type.name == value:
                return anime_type
        # Handle common aliases
        if value in ('TV SERIES', 'SERIES', 'TV SHOW'):
            return cls.TV
        if value in ('FILM', 'THEATRICAL'):
            return cls.MOVIE
        return cls.UNKNOWN


@dataclass
class Episode:
    """
    Represents a single episode in the collection.
    """
    number: int
    title: str = ""
    file_path: str = ""
    file_size: int = 0  # bytes
    quality: str = ""
    watched: bool = False
    watched_date: Optional[str] = None
    season: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'number': self.number,
            'title': self.title,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'quality': self.quality,
            'watched': self.watched,
            'watched_date': self.watched_date,
            'season': self.season,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Episode':
        """Create instance from dictionary."""
        return cls(
            number=data.get('number', 0),
            title=data.get('title', ''),
            file_path=data.get('file_path', ''),
            file_size=data.get('file_size', 0),
            quality=data.get('quality', ''),
            watched=data.get('watched', False),
            watched_date=data.get('watched_date'),
            season=data.get('season', 1),
        )
    
    def get_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024) if self.file_size > 0 else 0
    
    def get_status_icon(self) -> str:
        """Get status icon for display."""
        if self.watched:
            return "✅"
        elif self.file_path and os.path.exists(self.file_path):
            return "📥"  # Downloaded but not watched
        else:
            return "⏳"  # Not downloaded


class AnimeEntry:
    """
    Represents an anime entry in the collection with full metadata.
    
    Attributes:
        title: Anime title
        total_episodes: Total number of episodes
        anime_type: Type (TV, Movie, OVA, etc.)
        year: Year aired
        genres: List of genres
        synopsis: Anime description
        cover_url: URL to cover image
        rating: User rating (0-10)
        watch_status: Current watch status
        watch_progress: Number of episodes watched
        episodes: Dictionary of episodes
        added_date: Date when added to collection
        last_watched: Date of last watched episode
        tags: Custom tags
        notes: User notes
        main_page: AnimePahe URL
        keyword: Search keyword
    """
    
    def __init__(self, title: str, total_episodes: int = 0):
        """Initialize an anime entry."""
        self.title = title
        self.total_episodes = total_episodes
        self.anime_type = AnimeType.UNKNOWN
        self.year: Optional[int] = None
        self.genres: List[str] = []
        self.synopsis: str = ""
        self.cover_url: str = ""
        self.rating: Optional[float] = None
        self.watch_status = WatchStatus.UNWATCHED
        self.watch_progress: int = 0
        self.episodes: Dict[int, Episode] = {}
        self.added_date = datetime.now().isoformat()
        self.last_watched: Optional[str] = None
        self.started_date: Optional[str] = None
        self.tags: List[str] = []
        self.notes: str = ""
        self.main_page: str = ""
        self.keyword: str = ""
    
    def add_episode(self, episode_num: int, file_path: str = "", 
                   title: str = "", quality: str = "", season: int = 1) -> Episode:
        """Add an episode to the collection."""
        if episode_num not in self.episodes:
            self.episodes[episode_num] = Episode(
                number=episode_num,
                title=title,
                season=season,
            )
        
        episode = self.episodes[episode_num]
        if file_path:
            episode.file_path = file_path
            if os.path.exists(file_path):
                episode.file_size = os.path.getsize(file_path)
        if title:
            episode.title = title
        if quality:
            episode.quality = quality
        if season:
            episode.season = season
        
        return episode
    
    def get_downloaded_episodes(self) -> List[int]:
        """Get list of downloaded episode numbers."""
        return sorted([
            ep.number for ep in self.episodes.values() 
            if ep.file_path and os.path.exists(ep.file_path)
        ])
    
    def get_downloaded_count(self) -> int:
        """Get count of downloaded episodes."""
        return len(self.get_downloaded_episodes())
    
    def get_completion_percentage(self) -> float:
        """Calculate collection completion percentage."""
        if self.total_episodes == 0:
            return 0.0
        return (self.get_downloaded_count() / self.total_episodes) * 100
    
    def get_watch_percentage(self) -> float:
        """Calculate watch progress percentage."""
        if self.total_episodes == 0:
            return 0.0
        return (self.watch_progress / self.total_episodes) * 100
    
    def get_missing_episodes(self) -> List[int]:
        """Get list of missing episode numbers."""
        if self.total_episodes == 0:
            return []
        
        downloaded = set(self.get_downloaded_episodes())
        all_episodes = set(range(1, self.total_episodes + 1))
        return sorted(list(all_episodes - downloaded))
    
    def get_total_size(self) -> int:
        """Get total size of all downloaded episodes in bytes."""
        return sum(ep.file_size for ep in self.episodes.values() if ep.file_size > 0)
    
    def get_total_size_gb(self) -> float:
        """Get total size in GB."""
        return self.get_total_size() / (1024**3)
    
    def get_seasons(self) -> Dict[int, List[Episode]]:
        """Group episodes by season."""
        seasons: Dict[int, List[Episode]] = {}
        for episode in sorted(self.episodes.values(), key=lambda e: e.number):
            season = episode.season
            if season not in seasons:
                seasons[season] = []
            seasons[season].append(episode)
        return seasons
    
    def mark_watched(self, episode_num: int) -> None:
        """Mark an episode as watched."""
        if episode_num in self.episodes:
            self.episodes[episode_num].watched = True
            self.episodes[episode_num].watched_date = datetime.now().isoformat()
        
        # Update watch progress
        watched_count = sum(1 for ep in self.episodes.values() if ep.watched)
        self.watch_progress = max(self.watch_progress, watched_count)
        self.last_watched = datetime.now().isoformat()
        
        # Auto-update status
        if self.total_episodes > 0 and self.watch_progress >= self.total_episodes:
            self.watch_status = WatchStatus.COMPLETED
        elif self.watch_progress > 0:
            if self.watch_status == WatchStatus.UNWATCHED:
                self.watch_status = WatchStatus.WATCHING
                self.started_date = datetime.now().isoformat()
    
    def update_from_record(self, record_data: Dict[str, Any]) -> None:
        """Update metadata from records database."""
        if 'max_episode' in record_data and record_data['max_episode']:
            self.total_episodes = record_data['max_episode']
        if 'type' in record_data and record_data['type']:
            self.anime_type = AnimeType.from_string(record_data['type'])
        if 'year_aired' in record_data and record_data['year_aired']:
            self.year = record_data['year_aired']
        if 'about' in record_data and record_data['about']:
            self.synopsis = record_data['about']
        if 'cover_photo' in record_data and record_data['cover_photo']:
            self.cover_url = record_data['cover_photo']
        if 'rating' in record_data and record_data['rating']:
            # Don't override user rating with external rating
            pass
        if 'Main Page' in record_data and record_data['Main Page']:
            self.main_page = record_data['Main Page']
        if 'keyword' in record_data and record_data['keyword']:
            self.keyword = record_data['keyword']
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'title': self.title,
            'total_episodes': self.total_episodes,
            'anime_type': self.anime_type.value,
            'year': self.year,
            'genres': self.genres,
            'synopsis': self.synopsis,
            'cover_url': self.cover_url,
            'rating': self.rating,
            'watch_status': self.watch_status.value,
            'watch_progress': self.watch_progress,
            'episodes': {str(k): v.to_dict() for k, v in self.episodes.items()},
            'added_date': self.added_date,
            'last_watched': self.last_watched,
            'started_date': self.started_date,
            'tags': self.tags,
            'notes': self.notes,
            'main_page': self.main_page,
            'keyword': self.keyword,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimeEntry':
        """Create instance from dictionary."""
        entry = cls(data['title'], data.get('total_episodes', 0))
        entry.anime_type = AnimeType.from_string(data.get('anime_type', 'Unknown'))
        entry.year = data.get('year')
        entry.genres = data.get('genres', [])
        entry.synopsis = data.get('synopsis', '')
        entry.cover_url = data.get('cover_url', '')
        entry.rating = data.get('rating')
        entry.watch_status = WatchStatus.from_string(data.get('watch_status', 'unwatched'))
        entry.watch_progress = data.get('watch_progress', 0)
        entry.added_date = data.get('added_date', datetime.now().isoformat())
        entry.last_watched = data.get('last_watched')
        entry.started_date = data.get('started_date')
        entry.tags = data.get('tags', [])
        entry.notes = data.get('notes', '')
        entry.main_page = data.get('main_page', '')
        entry.keyword = data.get('keyword', '')
        
        # Load episodes
        episodes_data = data.get('episodes', {})
        for ep_num_str, ep_data in episodes_data.items():
            entry.episodes[int(ep_num_str)] = Episode.from_dict(ep_data)
        
        # Backward compatibility: convert old format
        if 'downloaded_episodes' in data and not entry.episodes:
            for ep_num in data.get('downloaded_episodes', []):
                file_path = data.get('file_paths', {}).get(str(ep_num), '')
                file_size = data.get('file_sizes', {}).get(str(ep_num), 0)
                entry.episodes[ep_num] = Episode(
                    number=ep_num,
                    file_path=file_path,
                    file_size=file_size,
                )
        
        return entry
    
    def get_display_status(self) -> str:
        """Get display-friendly status string."""
        if self.watch_status == WatchStatus.WATCHING:
            return f"Watching Episode {self.watch_progress}"
        elif self.watch_status == WatchStatus.COMPLETED:
            return "Completed"
        elif self.watch_status == WatchStatus.ON_HOLD:
            return f"On Hold (Episode {self.watch_progress})"
        elif self.watch_status == WatchStatus.DROPPED:
            return f"Dropped (Episode {self.watch_progress})"
        elif self.watch_status == WatchStatus.PLAN_TO_WATCH:
            return "Plan to Watch"
        else:
            return "Not Started"
    
    def get_rating_display(self) -> str:
        """Get rating display string."""
        if self.rating and self.rating > 0:
            return f"⭐ {self.rating}/10"
        return ""
