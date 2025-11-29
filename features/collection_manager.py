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

# Import centralized configuration
from config import COLLECTION_DIR, COLLECTION_METADATA_FILE, LOGS_DIR, DATA_DIR

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
            # If no episode metadata available, estimate based on downloaded episodes
            # or return 0 if we have no information
            if len(self.downloaded_episodes) > 0:
                # Assume we have at least the downloaded episodes, but can't calculate completion
                return 0.0  # Keep 0.0% but indicate we have episodes
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
            metadata_dir: Directory to store metadata (now uses centralized config)
        """
        self.collection_dir = collection_dir or Path.home() / 'Downloads'
        self.metadata_dir = metadata_dir or COLLECTION_DIR
        
        # Use centralized paths
        self.metadata_file = COLLECTION_METADATA_FILE
        self.collection: Dict[str, AnimeEntry] = {}
        
        # Load existing collection
        self.load_collection()
        
        # Sync with records database to get episode metadata
        self.sync_from_records()
    
    def sync_from_records(self):
        """
        Sync collection metadata with records database to get episode information.
        Updates total_episodes for existing anime entries based on records database.
        """
        try:
            # Import here to avoid circular imports
            from features.manager import load_database
            
            records_db = load_database()
            updated_count = 0
            
            logger.info(f"Starting sync: {len(self.collection)} collection entries, {len(records_db)} records")
            
            # Log collection titles for debugging
            collection_titles = list(self.collection.keys())
            record_titles = [data.get('title') for data in records_db.values() if data.get('title')]
            
            logger.debug(f"Collection titles: {collection_titles}")
            logger.debug(f"Record titles: {record_titles}")
            
            for record_id, record_data in records_db.items():
                title = record_data.get('title')
                max_episodes = record_data.get('max_episode', 0)
                
                if title and title in self.collection:
                    entry = self.collection[title]
                    if entry.total_episodes == 0 and max_episodes > 0:
                        entry.total_episodes = max_episodes
                        updated_count += 1
                        logger.info(f"Updated {title} with {max_episodes} episodes")
                        
                        # If episodes exist but total_episodes was 0, update completion
                        if entry.downloaded_episodes and max_episodes > 0:
                            logger.info(f"{title} now shows {entry.get_completion_percentage():.1f}% completion")
                elif title:
                    # Check for fuzzy match if exact match fails
                    normalized_title = title.lower().strip()
                    for collection_title in self.collection:
                        if collection_title.lower().strip() == normalized_title:
                            entry = self.collection[collection_title]
                            if entry.total_episodes == 0 and max_episodes > 0:
                                entry.total_episodes = max_episodes
                                updated_count += 1
                                logger.info(f"Fuzzy matched '{collection_title}' -> '{title}' with {max_episodes} episodes")
                                break
            
            # Check which collection entries didn't get matched
            unmatched = []
            for collection_title in self.collection:
                entry = self.collection[collection_title]
                if entry.total_episodes == 0:
                    unmatched.append(collection_title)
            
            if unmatched:
                logger.warning(f"Anime without episode metadata: {unmatched}")
            
            if updated_count > 0:
                self.save_collection()
                logger.info(f"Synced {updated_count} anime with episode metadata")
            else:
                logger.debug("No anime needed episode metadata sync")
                
        except Exception as e:
            logger.error(f"Failed to sync with records database: {e}")

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


def handle_collection_commands(collection_cmd, collection_manager_instance):
    """
    Handle collection management commands.
    
    Args:
        collection_cmd: List of command arguments from argparse
        collection_manager_instance: CollectionManager instance to use
    """
    if not collection_cmd:
        collection_cmd = ['stats']  # Default to stats if no arguments
    
    command = collection_cmd[0]
    args_list = collection_cmd[1:] if len(collection_cmd) > 1 else []
    
    if command == 'stats':
        # Display collection statistics
        stats = collection_manager_instance.get_statistics()
        print(f"\n📚 Collection Statistics:")
        print(f"  Total Anime: {stats['total_anime']}")
        print(f"  Total Episodes: {stats['total_episodes']}")
        print(f"  Total Size: {stats['total_size_gb']:.2f} GB")
        print(f"  Completion Rate: {stats['completion_rate']:.1f}%")
        print(f"  Missing Episodes: {stats['missing_episodes']}")
        
        print(f"\n📊 Watch Status:")
        for status, count in stats['watch_status'].items():
            if count > 0:
                print(f"  {status.replace('_', ' ').title()}: {count}")
        
        if stats['recently_added']:
            print(f"\n📅 Recently Added:")
            for title, date in stats['recently_added'][:3]:
                print(f"  • {title}")
        return
    
    elif command == 'view':
        # List all anime in collection
        print(f"\n📚 Anime Collection ({len(collection_manager_instance.collection)} titles):")
        for i, (title, entry) in enumerate(sorted(collection_manager_instance.collection.items()), 1):
            completion = entry.get_completion_percentage()
            rating_text = f" ⭐{entry.rating}/10" if entry.rating and entry.rating > 0 else ""
            status_text = f" [{entry.watch_status.value.replace('_', ' ').title()}]" if entry.watch_status != WatchStatus.UNWATCHED else ""
            print(f"  {i:2d}. {title}{rating_text}{status_text}")
            print(f"      Episodes: {len(entry.file_paths)}/{entry.total_episodes} ({completion:.1f}%)")
        return
    
    elif command == 'show' and args_list:
        # Show detailed info for specific anime
        anime_title = ' '.join(args_list)
        if anime_title in collection_manager_instance.collection:
            entry = collection_manager_instance.collection[anime_title]
            print(f"\n📖 {anime_title}")
            print(f"  Total Episodes: {entry.total_episodes}")
            print(f"  Downloaded: {len(entry.file_paths)} episodes")
            print(f"  Completion: {entry.get_completion_percentage():.1f}%")
            if entry.rating and entry.rating > 0:
                print(f"  Rating: {entry.rating}/10")
            if entry.watch_status != WatchStatus.UNWATCHED:
                print(f"  Status: {entry.watch_status.value.replace('_', ' ').title()}")
            if entry.watch_progress > 0:
                print(f"  Progress: {entry.watch_progress} episodes watched")
            
            missing = entry.get_missing_episodes()
            if missing:
                print(f"  Missing Episodes: {missing[:10]}" + ("..." if len(missing) > 10 else ""))
        else:
            print(f"❌ '{anime_title}' not found in collection")
        return
    
    elif command == 'episodes' and args_list:
        # Show episode list for specific anime
        anime_title = ' '.join(args_list)
        if anime_title in collection_manager_instance.collection:
            entry = collection_manager_instance.collection[anime_title]
            print(f"\n📺 Episodes for {anime_title}:")
            
            if entry.file_paths:
                for episode_num in sorted(entry.file_paths.keys()):
                    file_path = entry.file_paths[episode_num]
                    file_size = entry.file_sizes.get(episode_num, 0)
                    size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
                    size_text = f" ({size_mb:.1f} MB)" if size_mb > 0 else ""
                    print(f"  Episode {episode_num:02d}: {Path(file_path).name}{size_text}")
            else:
                print(f"  No episodes downloaded")
        else:
            print(f"❌ '{anime_title}' not found in collection")
        return
    
    elif command == 'search' and args_list:
        # Search collection by title
        query = ' '.join(args_list).lower()
        print(f"\n🔍 Searching for: '{query}'")
        
        matches = []
        for title, entry in collection_manager_instance.collection.items():
            if query in title.lower():
                matches.append((title, entry))
        
        if matches:
            print(f"Found {len(matches)} matching anime:")
            for i, (title, entry) in enumerate(matches, 1):
                completion = entry.get_completion_percentage()
                rating_text = f" ⭐{entry.rating}/10" if entry.rating and entry.rating > 0 else ""
                status_text = f" [{entry.watch_status.value.replace('_', ' ').title()}]" if entry.watch_status != WatchStatus.UNWATCHED else ""
                print(f"  {i}. {title}{rating_text}{status_text}")
                print(f"     Episodes: {len(entry.file_paths)}/{entry.total_episodes} ({completion:.1f}%)")
        else:
            print("No matches found")
        return
    
    elif command == 'organize':
        # Organize collection files
        print(f"\n🗂️ Organizing collection...")
        organized_count = 0
        
        for title, entry in collection_manager_instance.collection.items():
            for episode_num, file_path in list(entry.file_paths.items()):
                if os.path.exists(file_path):
                    try:
                        new_path = collection_manager_instance.add_episode_file(
                            title, episode_num, file_path, organize=True
                        )
                        if new_path != file_path:
                            organized_count += 1
                    except Exception as e:
                        logger.error(f"Failed to organize {title} episode {episode_num}: {e}")
        
        print(f"✅ Organized {organized_count} files")
        return
    
    elif command == 'duplicates':
        # Find and remove duplicates
        print(f"\n🔍 Scanning for duplicate files...")
        duplicates = collection_manager_instance.detect_duplicates()
        
        if duplicates:
            print(f"Found {len(duplicates)} duplicate groups:")
            for i, (hash_val, paths) in enumerate(duplicates, 1):
                print(f"  {i}. Hash: {hash_val[:8]}...")
                for path in paths:
                    print(f"     {path}")
            
            print(f"\n🧹 Cleaning up duplicates...")
            removed = collection_manager_instance.cleanup_duplicates()
            print(f"✅ Removed {removed} duplicate files")
        else:
            print("✅ No duplicates found")
        return
    
    elif command == 'export' and args_list:
        # Export collection
        export_path = ' '.join(args_list)
        print(f"\n📤 Exporting collection to: {export_path}")
        
        try:
            collection_manager_instance.export_collection(export_path)
            print(f"✅ Collection exported successfully")
        except Exception as e:
            print(f"❌ Export failed: {e}")
        return
    
    elif command == 'import' and args_list:
        # Import collection
        import_path = ' '.join(args_list)
        print(f"\n📥 Importing collection from: {import_path}")
        
        try:
            # This would need to be implemented in CollectionManager
            print("⚠️ Import functionality not yet implemented")
        except Exception as e:
            print(f"❌ Import failed: {e}")
        return
    
    elif command == 'set-episodes' and len(args_list) >= 2:
        # Manually set episode count for an anime
        anime_title = ' '.join(args_list[:-1])
        try:
            episode_count = int(args_list[-1])
        except ValueError:
            print("❌ Episode count must be a number")
            return
        
        if anime_title in collection_manager_instance.collection:
            entry = collection_manager_instance.collection[anime_title]
            old_count = entry.total_episodes
            entry.total_episodes = episode_count
            collection_manager_instance.save_collection()
            
            completion = entry.get_completion_percentage()
            print(f"\n✅ Updated {anime_title}: {old_count} → {episode_count} episodes")
            print(f"   Completion: {len(entry.downloaded_episodes)}/{episode_count} ({completion:.1f}%)")
        else:
            print(f"❌ '{anime_title}' not found in collection")
        return
    
    elif command == 'data-paths':
        # Show current data paths and structure
        from config import get_project_info
        import json
        
        info = get_project_info()
        print(f"\n📁 AutoPahe Data Structure:")
        print(f"  Data Directory: {info['data_dir']}")
        print(f"  Records Database: {info['database_file']}")
        print(f"  Collection Metadata: {info['collection_file']}")
        print(f"  Log File: {info['log_file']}")
        print(f"  Portable Mode: {info['portable_mode']}")
        
        print(f"\n📂 Directory Structure:")
        # Only show subdirectories, not the main data directory itself
        subdirs = [d for d in info['directories_created'] if d != str(DATA_DIR)]
        for directory in subdirs:
            dir_name = directory.split('/')[-1]
            print(f"  data/{dir_name}/ - {dir_name.title()} files")
        
        # Show file sizes and counts
        import os
        if os.path.exists(info['database_file']):
            with open(info['database_file'], 'r') as f:
                records = json.load(f)
                print(f"\n📊 Current Data:")
                print(f"  Anime Records: {len(records)}")
                print(f"  Database Size: {os.path.getsize(info['database_file']) / 1024:.1f} KB")
        
        if os.path.exists(info['collection_file']):
            with open(info['collection_file'], 'r') as f:
                collection = json.load(f)
                print(f"  Collection Entries: {len(collection)}")
                print(f"  Collection Size: {os.path.getsize(info['collection_file']) / 1024:.1f} KB")
        return
    
    else:
        print(f"❌ Unknown collection command: {command}")
        print("Available commands: stats, view, show <title>, episodes <title>, search <query>, organize, duplicates, export <path>, import <path>, set-episodes <title> <count>, data-paths")
        return


# Global collection manager instance
collection_manager = CollectionManager()
