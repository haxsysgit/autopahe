"""
Collection Command Handlers
===========================
Command handlers for --collection CLI arguments.
"""

import os
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from collection.models import WatchStatus, AnimeType
from collection.stats import CollectionStats

if TYPE_CHECKING:
    from collection.manager import CollectionManager


def handle_collection_command(args: List[str], manager: 'CollectionManager') -> None:
    """
    Handle collection management commands.
    
    Args:
        args: List of command arguments from argparse
        manager: CollectionManager instance
    """
    if not args:
        args = ['stats']  # Default to stats
    
    command = args[0].lower()
    cmd_args = args[1:] if len(args) > 1 else []
    
    handlers = {
        'stats': lambda: _cmd_stats(manager),
        'view': lambda: _cmd_view(manager),
        'show': lambda: _cmd_show(manager, cmd_args),
        'episodes': lambda: _cmd_episodes(manager, cmd_args),
        'search': lambda: _cmd_search(manager, cmd_args),
        'organize': lambda: _cmd_organize(manager, cmd_args),
        'duplicates': lambda: _cmd_duplicates(manager, cmd_args),
        'export': lambda: _cmd_export(manager, cmd_args),
        'import': lambda: _cmd_import(manager, cmd_args),
        'set-episodes': lambda: _cmd_set_episodes(manager, cmd_args),
        'data-paths': lambda: _cmd_data_paths(manager),
    }
    
    if command in handlers:
        handlers[command]()
    else:
        print(f"❌ Unknown collection command: {command}")
        print("\nAvailable commands:")
        print("  stats          - Show collection statistics")
        print("  view           - View collection overview")
        print("  show <title>   - Show anime details")
        print("  episodes <title> - List episodes for anime")
        print("  search <query> - Search collection")
        print("  organize       - Organize collection files (in-place by default)")
        print("                   Options: --dry-run, --move-to-downloads")
        print("  duplicates     - Find and remove duplicates")
        print("  export <path>  - Export collection")
        print("  import <path>  - Import collection")
        print("  set-episodes <title> <count> - Set episode count")
        print("  data-paths     - Show data directory structure")


def _cmd_stats(manager: 'CollectionManager') -> None:
    """Display collection statistics."""
    stats = CollectionStats(manager)
    print(stats.format_stats_display())


def _cmd_view(manager: 'CollectionManager') -> None:
    """Display collection overview."""
    stats = CollectionStats(manager)
    print(stats.format_view_display())


def _cmd_show(manager: 'CollectionManager', args: List[str]) -> None:
    """Show detailed info for specific anime."""
    if not args:
        print("❌ Please specify an anime title: --collection show <title>")
        return
    
    anime_title = ' '.join(args)
    entry = manager.get_anime(anime_title)
    
    if not entry:
        # Try fuzzy search
        matches = manager.search_anime(anime_title)
        if matches:
            print(f"❌ '{anime_title}' not found. Did you mean:")
            for match in matches[:5]:
                print(f"  • {match.title}")
        else:
            print(f"❌ '{anime_title}' not found in collection")
        return
    
    # Display detailed info
    print()
    print(f"🎭 {entry.title}")
    print("=" * (len(entry.title) + 3))
    print()
    
    # Basic Info
    print("📊 Basic Info:")
    print(f"  • Type: {entry.anime_type.value}")
    print(f"  • Episodes: {entry.total_episodes or '?'} (downloaded: {entry.get_downloaded_count()})")
    if entry.year:
        print(f"  • Year: {entry.year}")
    if entry.rating:
        print(f"  • Rating: {entry.rating}/10 ⭐")
    print(f"  • Status: {entry.get_display_status()}")
    
    # Synopsis
    if entry.synopsis:
        print()
        print("📝 Synopsis:")
        # Truncate long synopsis
        synopsis = entry.synopsis[:300] + "..." if len(entry.synopsis) > 300 else entry.synopsis
        print(f"  {synopsis}")
    
    # Genres
    if entry.genres:
        print()
        print(f"🏷️ Genres: {', '.join(entry.genres)}")
    
    # Episode list (show first few and last few)
    if entry.episodes:
        print()
        print("🎬 Episodes:")
        
        sorted_episodes = sorted(entry.episodes.values(), key=lambda e: e.number)
        
        # Show up to 10 episodes
        display_episodes = sorted_episodes[:5]
        if len(sorted_episodes) > 10:
            display_episodes += sorted_episodes[-3:]
            show_ellipsis = True
        elif len(sorted_episodes) > 5:
            display_episodes = sorted_episodes[:10]
            show_ellipsis = False
        else:
            show_ellipsis = False
        
        shown_numbers = set()
        for ep in display_episodes:
            if ep.number in shown_numbers:
                continue
            shown_numbers.add(ep.number)
            
            status_icon = ep.get_status_icon()
            size_str = f" ({ep.get_size_mb():.1f}MB)" if ep.file_size > 0 else ""
            title_str = f" - {ep.title}" if ep.title else ""
            
            season_prefix = f"S{ep.season:02d}E" if ep.season > 1 else "E"
            print(f"  • {season_prefix}{ep.number:02d}{title_str}{size_str} {status_icon}")
            
            if show_ellipsis and ep.number == display_episodes[4].number:
                print(f"  • ...")
    
    # Progress
    print()
    completion = entry.get_completion_percentage()
    watch_pct = entry.get_watch_percentage()
    print(f"📈 Download Progress: {entry.get_downloaded_count()}/{entry.total_episodes or '?'} episodes ({completion:.1f}%)")
    print(f"📺 Watch Progress: {entry.watch_progress}/{entry.total_episodes or '?'} episodes ({watch_pct:.1f}%)")
    
    # Dates
    if entry.started_date or entry.last_watched:
        print()
        if entry.started_date:
            print(f"📅 Started: {entry.started_date[:10]}")
        if entry.last_watched:
            print(f"📅 Last Watched: {entry.last_watched[:10]}")
    
    # Missing episodes
    missing = entry.get_missing_episodes()
    if missing and len(missing) <= 20:
        print()
        print(f"⚠️ Missing Episodes: {', '.join(map(str, missing))}")
    elif missing:
        print()
        print(f"⚠️ Missing Episodes: {len(missing)} episodes not downloaded")


def _cmd_episodes(manager: 'CollectionManager', args: List[str]) -> None:
    """List episodes for specific anime."""
    if not args:
        print("❌ Please specify an anime title: --collection episodes <title>")
        return
    
    anime_title = ' '.join(args)
    entry = manager.get_anime(anime_title)
    
    if not entry:
        print(f"❌ '{anime_title}' not found in collection")
        return
    
    print()
    print(f"📺 {entry.title} - All Episodes")
    print("=" * 40)
    
    if not entry.episodes:
        print("  No episodes downloaded")
        return
    
    # Group by season
    seasons = entry.get_seasons()
    
    total_watched = 0
    total_downloaded = 0
    
    for season_num in sorted(seasons.keys()):
        episodes = seasons[season_num]
        
        if len(seasons) > 1:
            print()
            print(f"Season {season_num} ({len(episodes)} episodes):")
        
        for ep in sorted(episodes, key=lambda e: e.number):
            status_icon = ep.get_status_icon()
            size_str = f" ({ep.get_size_mb():.1f}MB)" if ep.file_size > 0 else ""
            title_str = f" - {ep.title}" if ep.title else ""
            
            if len(seasons) > 1:
                ep_str = f"S{season_num:02d}E{ep.number:02d}"
            else:
                ep_str = f"Episode {ep.number:02d}"
            
            print(f"  • {ep_str}{title_str}{size_str} {status_icon}")
            
            if ep.watched:
                total_watched += 1
            if ep.file_path and os.path.exists(ep.file_path):
                total_downloaded += 1
    
    print()
    print(f"📊 Total: {len(entry.episodes)} episodes | ✅ {total_watched} watched | 📥 {total_downloaded} downloaded")
    
    completion = entry.get_completion_percentage()
    if entry.total_episodes:
        print(f"📈 Completion: {completion:.1f}%")


def _cmd_search(manager: 'CollectionManager', args: List[str]) -> None:
    """Search collection."""
    if not args:
        print("❌ Please specify a search query: --collection search <query>")
        return
    
    query = ' '.join(args)
    matches = manager.search_anime(query)
    
    print()
    print(f"🔍 Collection Search: \"{query}\"")
    print("=" * 40)
    
    if not matches:
        print("No matches found")
        return
    
    print(f"Found {len(matches)} matching anime:")
    print()
    
    for i, entry in enumerate(matches, 1):
        rating_str = f" - {entry.rating}/10 ⭐" if entry.rating else ""
        year_str = f" ({entry.year})" if entry.year else ""
        
        print(f"{i}. {entry.title}{year_str} - {entry.anime_type.value}{rating_str}")
        
        if entry.genres:
            print(f"   Genre: {', '.join(entry.genres[:3])}")
        
        status_str = entry.get_display_status()
        print(f"   Status: {status_str}")
        print()


def _cmd_organize(manager: 'CollectionManager', args: List[str]) -> None:
    """Organize collection files."""
    dry_run = '--dry-run' in args or '-n' in args
    # By default, organize in-place. Use --move-to-downloads to move files to collection_dir
    in_place = '--move-to-downloads' not in args and '--move' not in args
    
    print()
    if dry_run:
        print("🔍 Organization Preview (Dry Run)")
    else:
        print("🗂️ Organizing Collection...")
    
    if in_place:
        print("   Mode: In-place (files stay in their current directory)")
    else:
        print(f"   Mode: Move to {manager.collection_dir}")
    print("=" * 40)
    
    results = manager.organize_collection(dry_run=dry_run, in_place=in_place)
    
    if results['operations']:
        print()
        print("File operations:")
        for op in results['operations'][:20]:  # Show max 20
            print(f"  • {Path(op['from']).name}")
            print(f"    → {op['to']}")
        
        if len(results['operations']) > 20:
            print(f"  ... and {len(results['operations']) - 20} more")
    
    print()
    if dry_run:
        print(f"📋 Would move {len(results['operations'])} files")
        print("Run without --dry-run to apply changes")
    else:
        print(f"✅ Organization complete!")
        print(f"  • {results['files_moved']} files moved")
        print(f"  • {results['folders_created']} folders created")
        
        if results['errors']:
            print(f"  • {len(results['errors'])} errors occurred")


def _cmd_duplicates(manager: 'CollectionManager', args: List[str]) -> None:
    """Find and handle duplicate files."""
    dry_run = '--dry-run' in args or '-n' in args
    cleanup = '--cleanup' in args or '-c' in args
    
    print()
    print("🔍 Duplicate Detection")
    print("=" * 40)
    
    duplicates = manager.detect_duplicates()
    
    if not duplicates:
        print("✅ No duplicates found")
        return
    
    print(f"Found {len(duplicates)} duplicate groups:")
    print()
    
    total_space = 0
    
    for i, (file_hash, files) in enumerate(duplicates, 1):
        print(f"{i}. Duplicate Set (hash: {file_hash[:8]}...):")
        
        for file_info in files:
            size_mb = file_info['size'] / (1024 * 1024)
            print(f"   • {file_info['path']}")
            print(f"     {file_info['anime']} E{file_info['episode']} ({size_mb:.1f}MB)")
        
        # Calculate space that could be freed (keep 1, remove rest)
        total_space += sum(f['size'] for f in files[1:])
        print()
    
    space_mb = total_space / (1024 * 1024)
    space_gb = total_space / (1024**3)
    
    print(f"💡 Potential space savings: {space_mb:.1f}MB ({space_gb:.2f}GB)")
    
    if cleanup:
        print()
        if dry_run:
            print("🔍 Cleanup Preview (Dry Run)")
            removed, freed = manager.cleanup_duplicates(dry_run=True)
            print(f"Would remove {removed} files and free {freed / (1024**3):.2f}GB")
        else:
            print("🧹 Cleaning up duplicates...")
            removed, freed = manager.cleanup_duplicates(dry_run=False)
            print(f"✅ Removed {removed} files, freed {freed / (1024**3):.2f}GB")
    else:
        print("Use --collection duplicates --cleanup to remove duplicates")
        print("Add --dry-run to preview without deleting")


def _cmd_export(manager: 'CollectionManager', args: List[str]) -> None:
    """Export collection."""
    if not args:
        print("❌ Please specify export path: --collection export <path>")
        return
    
    # Parse format from args
    format = 'json'
    export_path = args[0]
    
    if len(args) > 1:
        format = args[1].lower()
    elif export_path.endswith('.csv'):
        format = 'csv'
    
    print()
    print(f"📤 Exporting collection to: {export_path}")
    
    try:
        manager.export_collection(export_path, format=format)
        print(f"✅ Collection exported successfully ({format} format)")
        print(f"   {len(manager.collection)} anime entries exported")
    except Exception as e:
        print(f"❌ Export failed: {e}")


def _cmd_import(manager: 'CollectionManager', args: List[str]) -> None:
    """Import collection."""
    if not args:
        print("❌ Please specify import path: --collection import <path>")
        return
    
    import_path = args[0]
    merge = '--replace' not in args
    
    if not os.path.exists(import_path):
        print(f"❌ File not found: {import_path}")
        return
    
    print()
    print(f"📥 Importing collection from: {import_path}")
    print(f"   Mode: {'Merge' if merge else 'Replace'}")
    
    try:
        results = manager.import_collection(import_path, merge=merge)
        print(f"✅ Import complete!")
        print(f"   • {results['imported']} new anime imported")
        print(f"   • {results['updated']} existing anime updated")
        if results['skipped'] > 0:
            print(f"   • {results['skipped']} anime skipped")
    except Exception as e:
        print(f"❌ Import failed: {e}")


def _cmd_set_episodes(manager: 'CollectionManager', args: List[str]) -> None:
    """Manually set episode count for an anime."""
    if len(args) < 2:
        print("❌ Usage: --collection set-episodes <title> <count>")
        return
    
    try:
        episode_count = int(args[-1])
    except ValueError:
        print("❌ Episode count must be a number")
        return
    
    anime_title = ' '.join(args[:-1])
    entry = manager.get_anime(anime_title)
    
    if not entry:
        print(f"❌ '{anime_title}' not found in collection")
        return
    
    old_count = entry.total_episodes
    
    if manager.set_episode_count(anime_title, episode_count):
        completion = entry.get_completion_percentage()
        print()
        print(f"✅ Updated {anime_title}")
        print(f"   Episodes: {old_count} → {episode_count}")
        print(f"   Completion: {entry.get_downloaded_count()}/{episode_count} ({completion:.1f}%)")
    else:
        print(f"❌ Failed to update episode count")


def _cmd_data_paths(manager: 'CollectionManager') -> None:
    """Show data directory structure."""
    try:
        from config import get_project_info, DATA_DIR
        import json
        
        info = get_project_info()
        
        print()
        print("📁 AutoPahe Data Structure")
        print("=" * 40)
        print(f"  Data Directory: {info['data_dir']}")
        print(f"  Records Database: {info['database_file']}")
        print(f"  Collection Metadata: {info['collection_file']}")
        print(f"  Log File: {info['log_file']}")
        print(f"  Portable Mode: {info['portable_mode']}")
        
        print()
        print("📂 Directory Structure:")
        subdirs = [d for d in info.get('directories_created', []) if d != str(DATA_DIR)]
        for directory in subdirs:
            dir_name = directory.split('/')[-1]
            print(f"  data/{dir_name}/ - {dir_name.title()} files")
        
        # Show file sizes
        print()
        print("📊 Current Data:")
        
        if os.path.exists(info['database_file']):
            with open(info['database_file'], 'r') as f:
                records = json.load(f)
            size_kb = os.path.getsize(info['database_file']) / 1024
            print(f"  Anime Records: {len(records)} ({size_kb:.1f} KB)")
        
        if os.path.exists(info['collection_file']):
            with open(info['collection_file'], 'r') as f:
                collection = json.load(f)
            size_kb = os.path.getsize(info['collection_file']) / 1024
            print(f"  Collection Entries: {len(collection)} ({size_kb:.1f} KB)")
            
    except ImportError:
        print("❌ Config module not available")
    except Exception as e:
        print(f"❌ Error: {e}")
