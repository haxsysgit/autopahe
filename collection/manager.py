"""
Collection Manager
==================
Core manager for anime collection operations.
"""

import os
import json
import shutil
import hashlib
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from collection.models import AnimeEntry, Episode, WatchStatus, AnimeType

logger = logging.getLogger(__name__)


class CollectionManager:
    """
    Manages the anime collection with comprehensive features.
    
    Features:
        - Full metadata tracking
        - Automatic series organization
        - Duplicate detection and cleanup
        - Watch status and progress tracking
        - Missing episode detection
        - Collection statistics and analytics
        - Import/export functionality
    """
    
    def __init__(self, collection_dir: Optional[Path] = None,
                 metadata_file: Optional[Path] = None):
        """
        Initialize the collection manager.
        
        Args:
            collection_dir: Root directory for anime collection
            metadata_file: Path to metadata JSON file
        """
        # Import config here to avoid circular imports
        try:
            from config import COLLECTION_DIR, COLLECTION_METADATA_FILE
            self.metadata_dir = COLLECTION_DIR
            self.metadata_file = metadata_file or COLLECTION_METADATA_FILE
        except ImportError:
            # Fallback to platform-appropriate paths
            try:
                from ap_core.platform_paths import get_data_dir, get_downloads_dir
                self.metadata_dir = get_data_dir() / 'collection'
            except ImportError:
                # Ultimate fallback for standalone usage
                self.metadata_dir = Path.home() / '.config' / 'autopahe' / 'collection'
            self.metadata_file = metadata_file or self.metadata_dir / 'collection.json'
        
        # Use platform-appropriate downloads directory
        if collection_dir:
            self.collection_dir = collection_dir
        else:
            try:
                from ap_core.platform_paths import get_downloads_dir
                self.collection_dir = get_downloads_dir()
            except ImportError:
                self.collection_dir = Path.home() / 'Downloads'
        self.collection: Dict[str, AnimeEntry] = {}
        
        # Ensure metadata directory exists
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing collection
        self.load_collection()
        
        # Sync with records database
        self.sync_from_records()
    
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
    
    def sync_from_records(self) -> int:
        """
        Sync collection metadata with records database.
        
        Returns:
            Number of entries updated
        """
        updated_count = 0
        try:
            from features.manager import load_database
            records_db = load_database()
            
            for record_id, record_data in records_db.items():
                title = record_data.get('title', '')
                if not title:
                    continue
                
                # Direct match
                if title in self.collection:
                    self.collection[title].update_from_record(record_data)
                    updated_count += 1
                    continue
                
                # Fuzzy match (case-insensitive)
                normalized_title = title.lower().strip()
                for collection_title in self.collection:
                    if collection_title.lower().strip() == normalized_title:
                        self.collection[collection_title].update_from_record(record_data)
                        updated_count += 1
                        break
            
            if updated_count > 0:
                self.save_collection()
                logger.info(f"Synced {updated_count} anime with records database")
                
        except Exception as e:
            logger.error(f"Failed to sync with records: {e}")
        
        return updated_count
    
    def add_anime(self, title: str, total_episodes: int = 0, 
                  record_data: Optional[Dict] = None) -> AnimeEntry:
        """
        Add a new anime to the collection.
        
        Args:
            title: Anime title
            total_episodes: Total number of episodes
            record_data: Optional metadata from records database
            
        Returns:
            The anime entry
        """
        if title not in self.collection:
            self.collection[title] = AnimeEntry(title, total_episodes)
            logger.info(f"Added new anime to collection: {title}")
        
        entry = self.collection[title]
        
        if record_data:
            entry.update_from_record(record_data)
        
        self.save_collection()
        return entry
    
    def get_anime(self, title: str) -> Optional[AnimeEntry]:
        """Get anime entry by title (case-insensitive)."""
        if title in self.collection:
            return self.collection[title]
        
        # Try case-insensitive match
        title_lower = title.lower()
        for key, entry in self.collection.items():
            if key.lower() == title_lower:
                return entry
        
        return None
    
    def search_anime(self, query: str) -> List[AnimeEntry]:
        """
        Search collection by title, genre, or tags.
        
        Args:
            query: Search query
            
        Returns:
            List of matching anime entries
        """
        query_lower = query.lower()
        matches = []
        
        for entry in self.collection.values():
            # Search in title
            if query_lower in entry.title.lower():
                matches.append(entry)
                continue
            
            # Search in genres
            if any(query_lower in genre.lower() for genre in entry.genres):
                matches.append(entry)
                continue
            
            # Search in tags
            if any(query_lower in tag.lower() for tag in entry.tags):
                matches.append(entry)
                continue
            
            # Search in synopsis
            if entry.synopsis and query_lower in entry.synopsis.lower():
                matches.append(entry)
                continue
        
        return matches
    
    def add_episode_file(self, anime_title: str, episode_num: int,
                        source_path: str, organize: bool = True,
                        episode_title: str = "", quality: str = "",
                        season: int = 1) -> str:
        """
        Add an episode file to the collection.
        
        Args:
            anime_title: Anime title
            episode_num: Episode number
            source_path: Path to the episode file
            organize: Whether to organize (move) the file
            episode_title: Optional episode title
            quality: Video quality
            season: Season number
            
        Returns:
            Final path of the episode file
        """
        # Add anime if not exists
        if anime_title not in self.collection:
            self.add_anime(anime_title)
        
        entry = self.collection[anime_title]
        final_path = source_path
        
        if organize and os.path.exists(source_path):
            # Create organized folder structure
            anime_folder = self.collection_dir / self._sanitize_filename(anime_title)
            if season > 1 or entry.total_episodes > 26:
                # Use season folders for multi-season anime
                anime_folder = anime_folder / f"Season {season:02d}"
            anime_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate organized filename
            source_file = Path(source_path)
            extension = source_file.suffix
            if season > 1:
                organized_filename = f"{anime_title} S{season:02d}E{episode_num:02d}{extension}"
            else:
                organized_filename = f"{anime_title} - Episode {episode_num:02d}{extension}"
            organized_path = anime_folder / self._sanitize_filename(organized_filename)
            
            try:
                shutil.move(str(source_file), str(organized_path))
                final_path = str(organized_path)
                logger.info(f"Organized episode to: {organized_path}")
            except Exception as e:
                logger.error(f"Failed to organize file: {e}")
                final_path = source_path
        
        # Add episode to entry
        entry.add_episode(
            episode_num=episode_num,
            file_path=final_path,
            title=episode_title,
            quality=quality,
            season=season,
        )
        
        self.save_collection()
        return final_path
    
    def update_watch_status(self, anime_title: str, 
                           status: WatchStatus,
                           progress: Optional[int] = None) -> bool:
        """
        Update watch status for an anime.
        
        Args:
            anime_title: Anime title
            status: New watch status
            progress: Episodes watched (optional)
            
        Returns:
            True if successful
        """
        entry = self.get_anime(anime_title)
        if not entry:
            logger.warning(f"Anime not in collection: {anime_title}")
            return False
        
        entry.watch_status = status
        
        if progress is not None:
            entry.watch_progress = progress
            entry.last_watched = datetime.now().isoformat()
            
            # Set started date if first time watching
            if not entry.started_date and progress > 0:
                entry.started_date = datetime.now().isoformat()
        
        # Auto-update status based on progress
        if entry.total_episodes > 0:
            if entry.watch_progress >= entry.total_episodes:
                entry.watch_status = WatchStatus.COMPLETED
            elif entry.watch_progress > 0 and entry.watch_status == WatchStatus.UNWATCHED:
                entry.watch_status = WatchStatus.WATCHING
        
        self.save_collection()
        logger.info(f"Updated watch status for {anime_title}: {status.value}")
        return True
    
    def set_rating(self, anime_title: str, rating: float) -> bool:
        """Set user rating for an anime."""
        entry = self.get_anime(anime_title)
        if not entry:
            return False
        
        entry.rating = max(0, min(10, rating))
        self.save_collection()
        return True
    
    def set_episode_count(self, anime_title: str, count: int) -> bool:
        """Manually set episode count for an anime."""
        entry = self.get_anime(anime_title)
        if not entry:
            return False
        
        entry.total_episodes = count
        self.save_collection()
        return True
    
    def detect_duplicates(self) -> List[Tuple[str, List[Dict[str, Any]]]]:
        """
        Detect duplicate files in the collection.
        
        Returns:
            List of (hash, [file_info]) for duplicates
        """
        file_hashes: Dict[str, List[Dict[str, Any]]] = {}
        
        for entry in self.collection.values():
            for episode in entry.episodes.values():
                if episode.file_path and os.path.exists(episode.file_path):
                    try:
                        # Calculate file hash (first 10MB for speed)
                        with open(episode.file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read(10 * 1024 * 1024)).hexdigest()
                        
                        file_info = {
                            'path': episode.file_path,
                            'anime': entry.title,
                            'episode': episode.number,
                            'size': episode.file_size,
                            'quality': episode.quality,
                        }
                        
                        if file_hash not in file_hashes:
                            file_hashes[file_hash] = []
                        file_hashes[file_hash].append(file_info)
                    except Exception as e:
                        logger.debug(f"Failed to hash file {episode.file_path}: {e}")
        
        # Find duplicates (same hash, multiple files)
        return [(h, files) for h, files in file_hashes.items() if len(files) > 1]
    
    def cleanup_duplicates(self, keep_organized: bool = True, 
                          dry_run: bool = False) -> Tuple[int, int]:
        """
        Remove duplicate files from the collection.
        
        Args:
            keep_organized: Keep files in collection directory
            dry_run: Only report, don't delete
            
        Returns:
            Tuple of (files_removed, bytes_freed)
        """
        duplicates = self.detect_duplicates()
        removed_count = 0
        bytes_freed = 0
        
        for file_hash, file_infos in duplicates:
            if keep_organized:
                # Keep file in collection directory
                organized = [f for f in file_infos 
                           if str(self.collection_dir) in f['path']]
                keep_file = organized[0] if organized else file_infos[0]
                remove_files = [f for f in file_infos if f['path'] != keep_file['path']]
            else:
                # Keep largest/highest quality file
                sorted_files = sorted(file_infos, key=lambda x: x['size'], reverse=True)
                keep_file = sorted_files[0]
                remove_files = sorted_files[1:]
            
            for file_info in remove_files:
                if not dry_run:
                    try:
                        os.remove(file_info['path'])
                        removed_count += 1
                        bytes_freed += file_info['size']
                        logger.info(f"Removed duplicate: {file_info['path']}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_info['path']}: {e}")
                else:
                    removed_count += 1
                    bytes_freed += file_info['size']
        
        return removed_count, bytes_freed
    
    def organize_collection(self, dry_run: bool = False, in_place: bool = True) -> Dict[str, Any]:
        """
        Organize all collection files into proper folder structure.
        
        Args:
            dry_run: Only report, don't move files
            in_place: If True, organize files in their current directory (default).
                      If False, move files to collection_dir.
            
        Returns:
            Organization results
        """
        results = {
            'files_moved': 0,
            'folders_created': 0,
            'errors': [],
            'operations': [],
        }
        
        created_folders = set()
        
        for title, entry in self.collection.items():
            for episode in entry.episodes.values():
                if not episode.file_path or not os.path.exists(episode.file_path):
                    continue
                
                source_path = Path(episode.file_path)
                
                # Determine the base directory for organizing
                # in_place=True: use the parent directory of the current file
                # in_place=False: use the collection_dir (Downloads by default)
                if in_place:
                    base_dir = source_path.parent
                else:
                    base_dir = self.collection_dir
                
                # Determine target folder (create anime subfolder)
                anime_folder = base_dir / self._sanitize_filename(title)
                if episode.season > 1 or entry.total_episodes > 26:
                    anime_folder = anime_folder / f"Season {episode.season:02d}"
                
                # Determine target filename
                ext = source_path.suffix
                if episode.season > 1:
                    new_filename = f"{title} S{episode.season:02d}E{episode.number:02d}{ext}"
                else:
                    new_filename = f"{title} - Episode {episode.number:02d}{ext}"
                
                target_path = anime_folder / self._sanitize_filename(new_filename)
                
                # Skip if already organized (same path)
                if source_path.resolve() == target_path.resolve():
                    continue
                
                # Skip if file is already in an anime-named folder with correct name
                if source_path.parent.name == self._sanitize_filename(title) and source_path.name == self._sanitize_filename(new_filename):
                    continue
                
                results['operations'].append({
                    'from': str(source_path),
                    'to': str(target_path),
                    'anime': title,
                    'episode': episode.number,
                })
                
                if not dry_run:
                    try:
                        if str(anime_folder) not in created_folders:
                            anime_folder.mkdir(parents=True, exist_ok=True)
                            created_folders.add(str(anime_folder))
                            results['folders_created'] += 1
                        
                        shutil.move(str(source_path), str(target_path))
                        episode.file_path = str(target_path)
                        results['files_moved'] += 1
                    except Exception as e:
                        results['errors'].append({
                            'file': str(source_path),
                            'error': str(e),
                        })
        
        if not dry_run:
            self.save_collection()
        
        return results
    
    def export_collection(self, export_path: str, 
                         format: str = 'json',
                         include_stats: bool = True) -> None:
        """Export collection to file."""
        from collection.stats import CollectionStats
        
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'version': '3.3.3',
            'collection': {
                title: entry.to_dict()
                for title, entry in self.collection.items()
            }
        }
        
        if include_stats:
            stats = CollectionStats(self)
            export_data['statistics'] = stats.get_full_stats()
        
        if format == 'json':
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif format == 'csv':
            import csv
            with open(export_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Title', 'Type', 'Year', 'Episodes', 'Downloaded', 
                    'Status', 'Progress', 'Rating', 'Genres', 'Added Date'
                ])
                for title, entry in self.collection.items():
                    writer.writerow([
                        title,
                        entry.anime_type.value,
                        entry.year or '',
                        entry.total_episodes,
                        entry.get_downloaded_count(),
                        entry.watch_status.value,
                        entry.watch_progress,
                        entry.rating or '',
                        ', '.join(entry.genres),
                        entry.added_date,
                    ])
        
        logger.info(f"Exported collection to {export_path} ({format} format)")
    
    def import_collection(self, import_path: str, 
                         merge: bool = True) -> Dict[str, int]:
        """
        Import collection from file.
        
        Args:
            import_path: Path to import file
            merge: Merge with existing collection or replace
            
        Returns:
            Import statistics
        """
        results = {'imported': 0, 'updated': 0, 'skipped': 0}
        
        with open(import_path, 'r') as f:
            import_data = json.load(f)
        
        # Handle different formats
        if 'collection' in import_data:
            collection_data = import_data['collection']
        else:
            collection_data = import_data
        
        if not merge:
            self.collection = {}
        
        for title, entry_data in collection_data.items():
            if title in self.collection:
                if merge:
                    # Update existing entry with new data
                    existing = self.collection[title]
                    new_entry = AnimeEntry.from_dict(entry_data)
                    
                    # Merge episodes
                    for ep_num, episode in new_entry.episodes.items():
                        if ep_num not in existing.episodes:
                            existing.episodes[ep_num] = episode
                    
                    # Update metadata if missing
                    if not existing.synopsis and new_entry.synopsis:
                        existing.synopsis = new_entry.synopsis
                    if not existing.genres and new_entry.genres:
                        existing.genres = new_entry.genres
                    
                    results['updated'] += 1
                else:
                    results['skipped'] += 1
            else:
                self.collection[title] = AnimeEntry.from_dict(entry_data)
                results['imported'] += 1
        
        self.save_collection()
        logger.info(f"Imported collection: {results}")
        return results
    
    def get_by_status(self, status: WatchStatus) -> List[AnimeEntry]:
        """Get all anime with given watch status."""
        return [e for e in self.collection.values() if e.watch_status == status]
    
    def get_by_type(self, anime_type: AnimeType) -> List[AnimeEntry]:
        """Get all anime of given type."""
        return [e for e in self.collection.values() if e.anime_type == anime_type]
    
    def get_by_year(self, year: int) -> List[AnimeEntry]:
        """Get all anime from given year."""
        return [e for e in self.collection.values() if e.year == year]
    
    def get_recent(self, limit: int = 5, 
                  sort_by: str = 'added') -> List[AnimeEntry]:
        """
        Get recently added or watched anime.
        
        Args:
            limit: Maximum number to return
            sort_by: 'added' or 'watched'
        """
        if sort_by == 'watched':
            entries = [e for e in self.collection.values() if e.last_watched]
            entries.sort(key=lambda e: e.last_watched or '', reverse=True)
        else:
            entries = list(self.collection.values())
            entries.sort(key=lambda e: e.added_date or '', reverse=True)
        
        return entries[:limit]
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        filename = re.sub(r'\s+', ' ', filename)
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip()
