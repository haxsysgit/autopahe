"""
Collection Statistics
=====================
Comprehensive statistics and analytics for anime collections.
"""

from typing import Dict, List, Any, Optional, TYPE_CHECKING
from collections import defaultdict
from datetime import datetime

from collection.models import WatchStatus, AnimeType

if TYPE_CHECKING:
    from collection.manager import CollectionManager


class CollectionStats:
    """
    Calculate and format collection statistics.
    """
    
    def __init__(self, manager: 'CollectionManager'):
        """Initialize with a CollectionManager instance."""
        self.manager = manager
        self.collection = manager.collection
    
    def get_full_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive collection statistics.
        
        Returns:
            Dictionary with all statistics
        """
        stats = {
            'summary': self._get_summary_stats(),
            'by_status': self._get_status_breakdown(),
            'by_type': self._get_type_breakdown(),
            'by_year': self._get_year_breakdown(),
            'ratings': self._get_rating_stats(),
            'genres': self._get_genre_stats(),
            'recent': self._get_recent_stats(),
            'storage': self._get_storage_stats(),
        }
        return stats
    
    def _get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total_episodes = 0
        total_size = 0
        total_watched = 0
        
        for entry in self.collection.values():
            total_episodes += entry.get_downloaded_count()
            total_size += entry.get_total_size()
            total_watched += entry.watch_progress
        
        return {
            'total_anime': len(self.collection),
            'total_episodes': total_episodes,
            'total_watched': total_watched,
            'total_size_bytes': total_size,
            'total_size_gb': total_size / (1024**3),
        }
    
    def _get_status_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by watch status."""
        breakdown = {}
        
        for status in WatchStatus:
            entries = [e for e in self.collection.values() if e.watch_status == status]
            if entries:
                total_eps = sum(e.get_downloaded_count() for e in entries)
                breakdown[status.value] = {
                    'count': len(entries),
                    'episodes': total_eps,
                    'titles': [e.title for e in entries],
                }
        
        return breakdown
    
    def _get_type_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by anime type."""
        breakdown = {}
        
        for anime_type in AnimeType:
            entries = [e for e in self.collection.values() if e.anime_type == anime_type]
            if entries:
                breakdown[anime_type.value] = {
                    'count': len(entries),
                    'titles': [e.title for e in entries],
                }
        
        return breakdown
    
    def _get_year_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by year."""
        breakdown = defaultdict(lambda: {'count': 0, 'titles': []})
        
        for entry in self.collection.values():
            if entry.year:
                # Group by decade ranges
                if entry.year >= 2020:
                    key = '2020-present'
                elif entry.year >= 2015:
                    key = '2015-2019'
                elif entry.year >= 2010:
                    key = '2010-2014'
                else:
                    key = 'Before 2010'
                
                breakdown[key]['count'] += 1
                breakdown[key]['titles'].append(entry.title)
        
        return dict(breakdown)
    
    def _get_rating_stats(self) -> Dict[str, Any]:
        """Get rating statistics."""
        ratings = [e.rating for e in self.collection.values() if e.rating and e.rating > 0]
        
        if not ratings:
            return {
                'average': 0,
                'highest': None,
                'lowest': None,
                'top_rated': [],
                'rated_count': 0,
            }
        
        # Get top rated anime
        rated_entries = [(e.title, e.rating) for e in self.collection.values() 
                        if e.rating and e.rating > 0]
        rated_entries.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'average': sum(ratings) / len(ratings),
            'highest': max(ratings),
            'lowest': min(ratings),
            'top_rated': rated_entries[:5],
            'rated_count': len(ratings),
        }
    
    def _get_genre_stats(self) -> Dict[str, Any]:
        """Get genre statistics."""
        genre_counts = defaultdict(int)
        
        for entry in self.collection.values():
            for genre in entry.genres:
                genre_counts[genre] += 1
        
        # Sort by frequency
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_genres': len(genre_counts),
            'most_common': sorted_genres[:5] if sorted_genres else [],
            'all_genres': dict(sorted_genres),
        }
    
    def _get_recent_stats(self) -> Dict[str, Any]:
        """Get recently added/watched stats."""
        # Recently added
        added_entries = list(self.collection.values())
        added_entries.sort(key=lambda e: e.added_date or '', reverse=True)
        
        # Recently watched
        watched_entries = [e for e in self.collection.values() if e.last_watched]
        watched_entries.sort(key=lambda e: e.last_watched or '', reverse=True)
        
        return {
            'recently_added': [
                {'title': e.title, 'date': e.added_date}
                for e in added_entries[:5]
            ],
            'recently_watched': [
                {'title': e.title, 'date': e.last_watched, 'progress': e.watch_progress}
                for e in watched_entries[:5]
            ],
        }
    
    def _get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        size_by_anime = []
        
        for entry in self.collection.values():
            size = entry.get_total_size()
            if size > 0:
                size_by_anime.append({
                    'title': entry.title,
                    'size_bytes': size,
                    'size_gb': size / (1024**3),
                    'episodes': entry.get_downloaded_count(),
                })
        
        size_by_anime.sort(key=lambda x: x['size_bytes'], reverse=True)
        
        total_size = sum(x['size_bytes'] for x in size_by_anime)
        
        return {
            'total_size_gb': total_size / (1024**3),
            'largest_anime': size_by_anime[:5] if size_by_anime else [],
            'anime_with_files': len(size_by_anime),
        }
    
    def format_stats_display(self) -> str:
        """
        Format statistics for console display.
        
        Returns:
            Formatted string for display
        """
        stats = self.get_full_stats()
        summary = stats['summary']
        
        lines = [
            "",
            "📊 Collection Statistics",
            "=" * 40,
            f"Total anime: {summary['total_anime']}",
            f"Total episodes: {summary['total_episodes']:,}",
            f"Total size: {summary['total_size_gb']:.1f} GB",
            "",
        ]
        
        # By Status
        by_status = stats['by_status']
        if by_status:
            lines.append("By Status:")
            for status, data in by_status.items():
                status_display = status.replace('_', ' ').title()
                lines.append(f"  - {status_display}: {data['count']} anime ({data['episodes']} episodes)")
        
        lines.append("")
        
        # By Type
        by_type = stats['by_type']
        if by_type:
            lines.append("By Type:")
            for anime_type, data in by_type.items():
                lines.append(f"  - {anime_type}: {data['count']} anime")
        
        lines.append("")
        
        # By Year
        by_year = stats['by_year']
        if by_year:
            lines.append("By Year:")
            for year_range, data in sorted(by_year.items(), reverse=True):
                lines.append(f"  - {year_range}: {data['count']} anime")
        
        lines.append("")
        
        # Ratings
        ratings = stats['ratings']
        if ratings['rated_count'] > 0:
            lines.append(f"Average Rating: {ratings['average']:.1f}/10")
            
            if ratings['top_rated']:
                lines.append("Top Rated:")
                for title, rating in ratings['top_rated'][:3]:
                    lines.append(f"  - {title}: {rating}/10 ⭐")
        
        lines.append("")
        
        # Genres
        genres = stats['genres']
        if genres['most_common']:
            lines.append("Most Watched Genres:")
            for genre, count in genres['most_common'][:3]:
                lines.append(f"  - {genre}: {count} anime")
        
        return '\n'.join(lines)
    
    def format_view_display(self) -> str:
        """
        Format collection overview for console display.
        
        Returns:
            Formatted string for display
        """
        lines = [
            "",
            "🎬 Anime Collection Overview",
            "=" * 40,
        ]
        
        # Group by status
        status_groups = {
            'Currently Watching': WatchStatus.WATCHING,
            'Completed': WatchStatus.COMPLETED,
            'On Hold': WatchStatus.ON_HOLD,
            'Plan to Watch': WatchStatus.PLAN_TO_WATCH,
            'Dropped': WatchStatus.DROPPED,
        }
        
        for group_name, status in status_groups.items():
            entries = [e for e in self.collection.values() if e.watch_status == status]
            if entries:
                lines.append("")
                lines.append(f"{group_name} ({len(entries)}):")
                
                # Sort by last watched or added date
                if status == WatchStatus.WATCHING:
                    entries.sort(key=lambda e: e.last_watched or '', reverse=True)
                else:
                    entries.sort(key=lambda e: e.title)
                
                for entry in entries[:10]:  # Show max 10 per category
                    rating_str = f" ({entry.rating}/10) ⭐" if entry.rating else ""
                    
                    if status == WatchStatus.WATCHING:
                        progress_str = f" - E{entry.watch_progress}/{entry.total_episodes or '?'}"
                    elif status == WatchStatus.COMPLETED:
                        progress_str = f" - {entry.total_episodes or entry.get_downloaded_count()} episodes"
                    elif status in (WatchStatus.ON_HOLD, WatchStatus.DROPPED):
                        progress_str = f" - E{entry.watch_progress}/{entry.total_episodes or '?'}"
                    else:
                        progress_str = ""
                    
                    lines.append(f"  • {entry.title}{progress_str}{rating_str}")
                
                if len(entries) > 10:
                    lines.append(f"  ... and {len(entries) - 10} more")
        
        # Recently added
        recent = self.manager.get_recent(5, 'added')
        if recent:
            lines.append("")
            lines.append("Recently Added:")
            for entry in recent:
                days_ago = self._days_since(entry.added_date)
                time_str = f"({days_ago} days ago)" if days_ago else "(today)"
                lines.append(f"  • {entry.title} {time_str}")
        
        return '\n'.join(lines)
    
    def _days_since(self, date_str: Optional[str]) -> int:
        """Calculate days since a date string."""
        if not date_str:
            return 0
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            delta = datetime.now() - date.replace(tzinfo=None)
            return delta.days
        except:
            return 0
