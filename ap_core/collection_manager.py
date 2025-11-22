"""
Collection Manager for AutoPahe
================================
Manages anime collection organization, tracking, and metadata.
Provides automatic organization, duplicate detection, and watch status tracking.

Author: AutoPahe Development Team
Date: 2024-11-22
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class WatchStatus(Enum):
    """Enum for anime watch status."""
    UNWATCHED = "unwatched"
    WATCHING = "watching"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    DROPPED = "dropped"
    PLAN_TO_WATCH = "plan_to_watch"


class AnimeEntry:
    """
    Represents an anime entry in the collection.
    
    Attributes:
        title: Anime title
        total_episodes: Total number of episodes
        downloaded_episodes: Set of downloaded episode numbers
        watch_status: Current watch status
        watch_progress: Number of episodes watched
        file_paths: Dictionary mapping episode numbers to file paths
        added_date: Date when anime was added to collection
        last_watched: Date of last watched episode
        tags: Custom tags for organization
        rating: User rating (1-10)
        notes: User notes about the anime
    """
    
    def __init__(self, title: str, total_episodes: int = 0):
        """
        Initialize an anime entry.
        
        Args:
            title: Anime title
            total_episodes: Total number of episodes
        """
        self.title = title
        self.total_episodes = total_episodes
        self.downloaded_episodes: Set[int] = set()
        self.watch_status = WatchStatus.UNWATCHED
        self.watch_progress = 0
        self.file_paths: Dict[int, str] = {}
        self.added_date = datetime.now().isoformat()
        self.last_watched: Optional[str] = None
        self.tags: List[str] = []
        self.rating: Optional[int] = None
        self.notes: str = ""
        self.file_sizes: Dict[int, int] = {}  # Episode number to file size mapping
    
    def add_episode(self, episode_num: int, file_path: str) -> None:
        """
        Add an episode to the collection.
        
        Args:
            episode_num: Episode number
            file_path: Path to the episode file
        """
        self.downloaded_episodes.add(episode_num)
        self.file_paths[episode_num] = file_path
        
        # Update file size
        if os.path.exists(file_path):
            self.file_sizes[episode_num] = os.path.getsize(file_path)
    
    def get_completion_percentage(self) -> float:
        """
        Calculate collection completion percentage.
        
        Returns:
            Percentage of episodes downloaded
        """
        if self.total_episodes == 0:
            return 0.0
        return (len(self.downloaded_episodes) / self.total_episodes) * 100
    
    def get_missing_episodes(self) -> List[int]:
        """
        Get list of missing episode numbers.
        
        Returns:
            List of missing episode numbers
        """
        if self.total_episodes == 0:
            return []
        
        all_episodes = set(range(1, self.total_episodes + 1))
        missing = all_episodes - self.downloaded_episodes
        return sorted(list(missing))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'title': self.title,
            'total_episodes': self.total_episodes,
            'downloaded_episodes': list(self.downloaded_episodes),
            'watch_status': self.watch_status.value,
            'watch_progress': self.watch_progress,
            'file_paths': self.file_paths,
            'added_date': self.added_date,
            'last_watched': self.last_watched,
            'tags': self.tags,
            'rating': self.rating,
            'notes': self.notes,
            'file_sizes': {str(k): v for k, v in self.file_sizes.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AnimeEntry':
        """Create instance from dictionary."""
        entry = cls(data['title'], data.get('total_episodes', 0))
        entry.downloaded_episodes = set(data.get('downloaded_episodes', []))
        entry.watch_status = WatchStatus(data.get('watch_status', 'unwatched'))
        entry.watch_progress = data.get('watch_progress', 0)
        entry.file_paths = {int(k): v for k, v in data.get('file_paths', {}).items()}
        entry.added_date = data.get('added_date', datetime.now().isoformat())
        entry.last_watched = data.get('last_watched')
        entry.tags = data.get('tags', [])
        entry.rating = data.get('rating')
        entry.notes = data.get('notes', '')
        entry.file_sizes = {int(k): v for k, v in data.get('file_sizes', {}).items()}
        return entry


class CollectionManager:
    """
    Manages the anime collection with organization and tracking features.
    
    Features:
        - Automatic series organization into folders
        - Duplicate file detection and cleanup
        - Watch status and progress tracking
        - Missing episode detection
        - Collection statistics and analytics
        - Import/export functionality
    """
    
    def __init__(self, collection_dir: Optional[Path] = None,
                 metadata_dir: Optional[Path] = None):
        """
        Initialize the collection manager.
        
        Args:
            collection_dir: Root directory for anime collection
            metadata_dir: Directory to store metadata (default: ~/.cache/autopahe/collection)
        """
        self.collection_dir = collection_dir or Path.home() / 'Downloads' / 'Anime'
        self.metadata_dir = metadata_dir or Path.home() / '.cache' / 'autopahe' / 'collection'
        
        # Create directories if they don't exist
        self.collection_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.metadata_dir / 'collection.json'
        self.collection: Dict[str, AnimeEntry] = {}
        
        # Load existing collection
        self.load_collection()
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        
        # Trim to reasonable length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename.strip()
    
    def save_collection(self) -> None:
        """Save collection metadata to disk."""
        try:
            collection_data = {
                title: entry.to_dict()
                for title, entry in self.collection.items()
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(collection_data, f, indent=2)
            
            logger.debug(f"Saved collection with {len(collection_data)} anime")
        except Exception as e:
            logger.error(f"Failed to save collection: {e}")
    
    def load_collection(self) -> None:
        """Load collection metadata from disk."""
        if not self.metadata_file.exists():
            logger.debug("No existing collection found")
            return
        
        try:
            with open(self.metadata_file, 'r') as f:
                collection_data = json.load(f)
            
            self.collection = {
                title: AnimeEntry.from_dict(entry_data)
                for title, entry_data in collection_data.items()
            }
            
            logger.info(f"Loaded collection with {len(self.collection)} anime")
        except Exception as e:
            logger.error(f"Failed to load collection: {e}")
            self.collection = {}
    
    def add_anime(self, title: str, total_episodes: int = 0) -> AnimeEntry:
        """
        Add a new anime to the collection.
        
        Args:
            title: Anime title
            total_episodes: Total number of episodes
            
        Returns:
            The anime entry
        """
        if title not in self.collection:
            self.collection[title] = AnimeEntry(title, total_episodes)
            self.save_collection()
            logger.info(f"Added new anime to collection: {title}")
        
        return self.collection[title]
    
    def add_episode_file(self, anime_title: str, episode_num: int,
                        source_path: str, organize: bool = True) -> str:
        """
        Add an episode file to the collection.
        
        Args:
            anime_title: Anime title
            episode_num: Episode number
            source_path: Path to the episode file
            organize: Whether to organize (move) the file
            
        Returns:
            Final path of the episode file
        """
        # Add anime if not exists
        if anime_title not in self.collection:
            self.add_anime(anime_title)
        
        entry = self.collection[anime_title]
        
        if organize:
            # Create anime folder
            anime_folder = self.collection_dir / self.sanitize_filename(anime_title)
            anime_folder.mkdir(exist_ok=True)
            
            # Generate organized filename
            source_file = Path(source_path)
            extension = source_file.suffix
            organized_filename = f"{anime_title} - Episode {episode_num:02d}{extension}"
            organized_path = anime_folder / self.sanitize_filename(organized_filename)
            
            # Move or copy file
            try:
                if source_file.exists():
                    shutil.move(str(source_file), str(organized_path))
                    logger.info(f"Organized episode to: {organized_path}")
                    final_path = str(organized_path)
                else:
                    logger.warning(f"Source file not found: {source_path}")
                    final_path = source_path
            except Exception as e:
                logger.error(f"Failed to organize file: {e}")
                final_path = source_path
        else:
            final_path = source_path
        
        # Add to collection
        entry.add_episode(episode_num, final_path)
        self.save_collection()
        
        return final_path
    
    def detect_duplicates(self) -> List[Tuple[str, List[str]]]:
        """
        Detect duplicate files in the collection.
        
        Returns:
            List of (hash, [file_paths]) for duplicates
        """
        file_hashes: Dict[str, List[str]] = {}
        
        for entry in self.collection.values():
            for file_path in entry.file_paths.values():
                if os.path.exists(file_path):
                    # Calculate file hash (first 10MB for speed)
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read(10 * 1024 * 1024)).hexdigest()
                            
                            if file_hash not in file_hashes:
                                file_hashes[file_hash] = []
                            file_hashes[file_hash].append(file_path)
                    except Exception as e:
                        logger.debug(f"Failed to hash file {file_path}: {e}")
        
        # Find duplicates (same hash, multiple files)
        duplicates = [(hash_val, paths) for hash_val, paths in file_hashes.items()
                     if len(paths) > 1]
        
        return duplicates
    
    def cleanup_duplicates(self, keep_organized: bool = True) -> int:
        """
        Remove duplicate files from the collection.
        
        Args:
            keep_organized: Keep files in organized folders, remove others
            
        Returns:
            Number of files removed
        """
        duplicates = self.detect_duplicates()
        removed_count = 0
        
        for file_hash, file_paths in duplicates:
            if keep_organized:
                # Keep file in collection directory, remove others
                organized_files = [p for p in file_paths 
                                 if str(self.collection_dir) in p]
                if organized_files:
                    keep_file = organized_files[0]
                    remove_files = [p for p in file_paths if p != keep_file]
                else:
                    # Keep first file if none are organized
                    keep_file = file_paths[0]
                    remove_files = file_paths[1:]
            else:
                # Keep largest file
                file_sizes = [(p, os.path.getsize(p)) for p in file_paths
                            if os.path.exists(p)]
                if file_sizes:
                    file_sizes.sort(key=lambda x: x[1], reverse=True)
                    keep_file = file_sizes[0][0]
                    remove_files = [p for p, _ in file_sizes[1:]]
                else:
                    continue
            
            # Remove duplicate files
            for file_path in remove_files:
                try:
                    os.remove(file_path)
                    removed_count += 1
                    logger.info(f"Removed duplicate: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove duplicate {file_path}: {e}")
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate files")
        
        return removed_count
    
    def update_watch_status(self, anime_title: str, 
                           status: WatchStatus,
                           progress: Optional[int] = None) -> None:
        """
        Update watch status for an anime.
        
        Args:
            anime_title: Anime title
            status: New watch status
            progress: Episodes watched (optional)
        """
        if anime_title not in self.collection:
            logger.warning(f"Anime not in collection: {anime_title}")
            return
        
        entry = self.collection[anime_title]
        entry.watch_status = status
        
        if progress is not None:
            entry.watch_progress = progress
            entry.last_watched = datetime.now().isoformat()
        
        # Auto-update status based on progress
        if entry.total_episodes > 0:
            if entry.watch_progress >= entry.total_episodes:
                entry.watch_status = WatchStatus.COMPLETED
            elif entry.watch_progress > 0:
                entry.watch_status = WatchStatus.WATCHING
        
        self.save_collection()
        logger.info(f"Updated watch status for {anime_title}: {status.value}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        stats = {
            'total_anime': len(self.collection),
            'total_episodes': 0,
            'total_size_gb': 0.0,
            'watch_status': {},
            'completion_rate': 0.0,
            'missing_episodes': 0,
            'average_rating': 0.0,
            'top_rated': [],
            'recently_added': [],
            'recently_watched': []
        }
        
        # Initialize watch status counts
        for status in WatchStatus:
            stats['watch_status'][status.value] = 0
        
        ratings = []
        recent_added = []
        recent_watched = []
        
        for entry in self.collection.values():
            # Count episodes and size
            stats['total_episodes'] += len(entry.downloaded_episodes)
            stats['total_size_gb'] += sum(entry.file_sizes.values()) / (1024**3)
            
            # Count watch status
            stats['watch_status'][entry.watch_status.value] += 1
            
            # Count missing episodes
            stats['missing_episodes'] += len(entry.get_missing_episodes())
            
            # Collect ratings
            if entry.rating:
                ratings.append((entry.title, entry.rating))
            
            # Collect recent entries
            recent_added.append((entry.title, entry.added_date))
            if entry.last_watched:
                recent_watched.append((entry.title, entry.last_watched))
        
        # Calculate averages and sort lists
        if ratings:
            stats['average_rating'] = sum(r for _, r in ratings) / len(ratings)
            stats['top_rated'] = sorted(ratings, key=lambda x: x[1], reverse=True)[:5]
        
        stats['recently_added'] = sorted(recent_added, key=lambda x: x[1], reverse=True)[:5]
        stats['recently_watched'] = sorted(recent_watched, key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate overall completion rate
        total_possible = sum(e.total_episodes for e in self.collection.values()
                           if e.total_episodes > 0)
        if total_possible > 0:
            stats['completion_rate'] = (stats['total_episodes'] / total_possible) * 100
        
        return stats
    
    def export_collection(self, export_path: str,
                         format: str = 'json',
                         include_stats: bool = True) -> None:
        """
        Export collection to file.
        
        Args:
            export_path: Path for export file
            format: Export format ('json', 'csv', 'mal')
            include_stats: Include statistics in export
        """
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'collection': {
                title: entry.to_dict()
                for title, entry in self.collection.items()
            }
        }
        
        if include_stats:
            export_data['statistics'] = self.get_statistics()
        
        if format == 'json':
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif format == 'csv':
            # Export as CSV
            import csv
            with open(export_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Episodes', 'Downloaded', 'Status', 
                               'Progress', 'Rating', 'Added Date'])
                
                for title, entry in self.collection.items():
                    writer.writerow([
                        title,
                        entry.total_episodes,
                        len(entry.downloaded_episodes),
                        entry.watch_status.value,
                        entry.watch_progress,
                        entry.rating or '',
                        entry.added_date
                    ])
        elif format == 'mal':
            # Export in MyAnimeList compatible format
            mal_data = []
            for title, entry in self.collection.items():
                mal_entry = {
                    'anime_title': title,
                    'episodes_watched': entry.watch_progress,
                    'status': self._mal_status_mapping(entry.watch_status),
                    'score': entry.rating or 0,
                    'tags': ', '.join(entry.tags),
                    'comments': entry.notes
                }
                mal_data.append(mal_entry)
            
            with open(export_path, 'w') as f:
                json.dump(mal_data, f, indent=2)
        
        logger.info(f"Exported collection to {export_path} ({format} format)")
    
    def _mal_status_mapping(self, status: WatchStatus) -> str:
        """Map internal status to MyAnimeList status."""
        mapping = {
            WatchStatus.WATCHING: 'Watching',
            WatchStatus.COMPLETED: 'Completed',
            WatchStatus.ON_HOLD: 'On-Hold',
            WatchStatus.DROPPED: 'Dropped',
            WatchStatus.PLAN_TO_WATCH: 'Plan to Watch',
            WatchStatus.UNWATCHED: 'Plan to Watch'
        }
        return mapping.get(status, 'Plan to Watch')


# Global collection manager instance
collection_manager = CollectionManager()
