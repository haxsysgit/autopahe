"""
Smart Resume System for AutoPahe
=================================
Manages download state persistence and intelligent resume capabilities.
Handles interrupted downloads with automatic retry and quality fallback.

Author: AutoPahe Development Team
Date: 22-11-2025
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class DownloadState:
    """
    Represents the state of a download for resume capability.
    
    Attributes:
        anime_title: Name of the anime
        episode_number: Episode being downloaded
        download_url: URL for the download
        file_path: Local path where file is being saved
        total_size: Total file size in bytes
        downloaded_size: Bytes downloaded so far
        quality: Video quality (360p, 720p, 1080p, etc.)
        status: Current status (pending, downloading, paused, failed, completed)
        retry_count: Number of retry attempts
        error_message: Last error message if any
        created_at: Timestamp when download was initiated
        updated_at: Last update timestamp
        checksum: Partial file checksum for integrity
    """
    anime_title: str
    episode_number: str
    download_url: str
    file_path: str
    total_size: int = 0
    downloaded_size: int = 0
    quality: str = "720p"
    status: str = "pending"
    retry_count: int = 0
    error_message: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DownloadState':
        """Create instance from dictionary."""
        return cls(**data)


class SmartResumeManager:
    """
    Manages download resumption with intelligent retry strategies.
    
    Features:
        - Persistent download state across sessions
        - Automatic retry with exponential backoff
        - Quality fallback on repeated failures
        - Checksum verification for partial downloads
        - Download queue management with priorities
    """
    
    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize the resume manager.
        
        Args:
            state_dir: Directory to store download states (uses platform-appropriate cache dir)
        """
        if state_dir:
            self.state_dir = state_dir
        else:
            # Use platform-appropriate cache directory
            try:
                from ap_core.platform_paths import get_cache_dir
                self.state_dir = get_cache_dir() / 'resume'
            except ImportError:
                self.state_dir = Path.home() / '.cache' / 'autopahe' / 'resume'
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / 'download_states.json'
        self.download_states: Dict[str, DownloadState] = {}
        self.quality_fallback_chain = ['1080p', '720p', '480p', '360p']
        self.max_retries = 3
        self.retry_delays = [5, 15, 30]  # Exponential backoff in seconds
        
        # Load existing states
        self.load_states()
    
    def generate_download_id(self, anime_title: str, episode_number: str) -> str:
        """
        Generate unique ID for a download.
        
        Args:
            anime_title: Anime title
            episode_number: Episode number
            
        Returns:
            Unique download ID
        """
        content = f"{anime_title}:{episode_number}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def save_states(self) -> None:
        """Persist all download states to disk."""
        try:
            states_data = {
                download_id: state.to_dict()
                for download_id, state in self.download_states.items()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(states_data, f, indent=2)
            
            logger.debug(f"Saved {len(states_data)} download states")
        except Exception as e:
            logger.error(f"Failed to save download states: {e}")
    
    def load_states(self) -> None:
        """Load download states from disk."""
        if not self.state_file.exists():
            logger.debug("No existing download states found")
            return
        
        try:
            with open(self.state_file, 'r') as f:
                states_data = json.load(f)
            
            self.download_states = {
                download_id: DownloadState.from_dict(state_data)
                for download_id, state_data in states_data.items()
            }
            
            logger.info(f"Loaded {len(self.download_states)} download states")
        except Exception as e:
            logger.error(f"Failed to load download states: {e}")
            self.download_states = {}
    
    def add_download(self, anime_title: str, episode_number: str,
                    download_url: str, file_path: str,
                    quality: str = "720p") -> str:
        """
        Add a new download to the resume system.
        
        Args:
            anime_title: Anime title
            episode_number: Episode number
            download_url: Download URL
            file_path: Destination file path
            quality: Video quality
            
        Returns:
            Download ID
        """
        download_id = self.generate_download_id(anime_title, episode_number)
        
        # Check if download already exists
        if download_id in self.download_states:
            state = self.download_states[download_id]
            if state.status == 'completed':
                logger.info(f"Download already completed: {anime_title} - Episode {episode_number}")
                return download_id
            else:
                logger.info(f"Resuming existing download: {anime_title} - Episode {episode_number}")
        else:
            # Create new download state
            state = DownloadState(
                anime_title=anime_title,
                episode_number=episode_number,
                download_url=download_url,
                file_path=file_path,
                quality=quality,
                status='pending'
            )
            self.download_states[download_id] = state
        
        self.save_states()
        return download_id
    
    def update_progress(self, download_id: str, 
                       downloaded_size: int,
                       total_size: Optional[int] = None) -> None:
        """
        Update download progress.
        
        Args:
            download_id: Download ID
            downloaded_size: Bytes downloaded so far
            total_size: Total file size if known
        """
        if download_id not in self.download_states:
            logger.warning(f"Unknown download ID: {download_id}")
            return
        
        state = self.download_states[download_id]
        state.downloaded_size = downloaded_size
        if total_size:
            state.total_size = total_size
        state.status = 'downloading'
        state.updated_at = datetime.now().isoformat()
        
        # Calculate and update checksum periodically
        if downloaded_size > 0 and downloaded_size % (1024 * 1024 * 10) == 0:  # Every 10MB
            self.update_checksum(download_id)
        
        # Save state periodically (every 5MB)
        if downloaded_size % (1024 * 1024 * 5) == 0:
            self.save_states()
    
    def update_checksum(self, download_id: str) -> None:
        """
        Update partial file checksum for integrity verification.
        
        Args:
            download_id: Download ID
        """
        state = self.download_states.get(download_id)
        if not state or not Path(state.file_path).exists():
            return
        
        try:
            # Calculate checksum of first 1MB for quick verification
            with open(state.file_path, 'rb') as f:
                data = f.read(1024 * 1024)
                if data:
                    state.checksum = hashlib.md5(data).hexdigest()
        except Exception as e:
            logger.debug(f"Failed to calculate checksum: {e}")
    
    def mark_completed(self, download_id: str) -> None:
        """
        Mark a download as completed.
        
        Args:
            download_id: Download ID
        """
        if download_id not in self.download_states:
            return
        
        state = self.download_states[download_id]
        state.status = 'completed'
        state.updated_at = datetime.now().isoformat()
        self.save_states()
        
        logger.info(f"Download completed: {state.anime_title} - Episode {state.episode_number}")
    
    def mark_failed(self, download_id: str, error_message: str) -> bool:
        """
        Mark a download as failed and determine if retry is possible.
        
        Args:
            download_id: Download ID
            error_message: Error message
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        if download_id not in self.download_states:
            return False
        
        state = self.download_states[download_id]
        state.status = 'failed'
        state.error_message = error_message
        state.retry_count += 1
        state.updated_at = datetime.now().isoformat()
        
        # Check if we should retry
        should_retry = state.retry_count <= self.max_retries
        
        if should_retry:
            # Calculate retry delay with exponential backoff
            delay_index = min(state.retry_count - 1, len(self.retry_delays) - 1)
            retry_delay = self.retry_delays[delay_index]
            
            logger.info(f"Will retry download in {retry_delay} seconds (attempt {state.retry_count}/{self.max_retries})")
            state.status = 'pending'  # Reset to pending for retry
        else:
            logger.error(f"Download failed after {self.max_retries} retries: {state.anime_title} - Episode {state.episode_number}")
        
        self.save_states()
        return should_retry
    
    def get_retry_delay(self, download_id: str) -> int:
        """
        Get retry delay for a download based on retry count.
        
        Args:
            download_id: Download ID
            
        Returns:
            Delay in seconds
        """
        state = self.download_states.get(download_id)
        if not state:
            return 0
        
        delay_index = min(state.retry_count - 1, len(self.retry_delays) - 1)
        return self.retry_delays[delay_index] if delay_index >= 0 else 0
    
    def get_fallback_quality(self, download_id: str) -> Optional[str]:
        """
        Get next quality level for fallback.
        
        Args:
            download_id: Download ID
            
        Returns:
            Next quality level or None if no fallback available
        """
        state = self.download_states.get(download_id)
        if not state:
            return None
        
        current_quality = state.quality
        try:
            current_index = self.quality_fallback_chain.index(current_quality)
            if current_index < len(self.quality_fallback_chain) - 1:
                return self.quality_fallback_chain[current_index + 1]
        except ValueError:
            # Current quality not in chain, start with first fallback
            return self.quality_fallback_chain[0] if self.quality_fallback_chain else None
        
        return None
    
    def get_resumable_downloads(self) -> List[Tuple[str, DownloadState]]:
        """
        Get list of downloads that can be resumed.
        
        Returns:
            List of (download_id, state) tuples for resumable downloads
        """
        resumable = []
        
        for download_id, state in self.download_states.items():
            if state.status in ['pending', 'downloading', 'paused', 'failed']:
                # Check if it's not too old (e.g., 7 days)
                updated = datetime.fromisoformat(state.updated_at)
                if datetime.now() - updated < timedelta(days=7):
                    resumable.append((download_id, state))
        
        return resumable
    
    def cleanup_old_states(self, days: int = 30) -> int:
        """
        Remove old completed or failed download states.
        
        Args:
            days: Remove states older than this many days
            
        Returns:
            Number of states removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        to_remove = []
        for download_id, state in self.download_states.items():
            if state.status in ['completed', 'failed']:
                updated = datetime.fromisoformat(state.updated_at)
                if updated < cutoff_date:
                    to_remove.append(download_id)
        
        for download_id in to_remove:
            del self.download_states[download_id]
            removed_count += 1
        
        if removed_count > 0:
            self.save_states()
            logger.info(f"Cleaned up {removed_count} old download states")
        
        return removed_count
    
    def get_download_stats(self) -> Dict[str, Any]:
        """
        Get statistics about download states.
        
        Returns:
            Dictionary with download statistics
        """
        stats = {
            'total': len(self.download_states),
            'pending': 0,
            'downloading': 0,
            'paused': 0,
            'failed': 0,
            'completed': 0,
            'total_downloaded_mb': 0,
            'resumable': 0
        }
        
        for state in self.download_states.values():
            stats[state.status] = stats.get(state.status, 0) + 1
            stats['total_downloaded_mb'] += state.downloaded_size / (1024 * 1024)
            
            if state.status in ['pending', 'downloading', 'paused']:
                stats['resumable'] += 1
        
        return stats


# Global resume manager instance
resume_manager = SmartResumeManager()


def can_resume_download(file_path: str, expected_size: Optional[int] = None) -> Tuple[bool, int]:
    """
    Check if a partial download can be resumed.
    
    Args:
        file_path: Path to the partial file
        expected_size: Expected total file size
        
    Returns:
        Tuple of (can_resume, current_size)
    """
    if not os.path.exists(file_path):
        return False, 0
    
    current_size = os.path.getsize(file_path)
    
    # Can resume if file exists and is smaller than expected
    if expected_size:
        can_resume = 0 < current_size < expected_size
    else:
        # If no expected size, resume if file has some content
        can_resume = current_size > 0
    
    return can_resume, current_size
