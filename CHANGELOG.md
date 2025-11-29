# AutoPahe Changelog

## [v3.3.0] - 2025-11-29

### 🗂️ MAJOR RESTRUCTURING

#### Centralized Data Architecture
- **Unified Data Directory**: All project data now centralized in `data/` folder
- **Organized Subdirectories**: `records/`, `logs/`, `cache/`, `collection/`, `backups/`
- **Automatic Migration**: Seamless one-time migration from legacy locations
- **Privacy Protection**: User data excluded from git via updated `.gitignore`
- **Portable Mode**: Support for portable installations via `AUTO_PAHE_PORTABLE` env var

#### Database Consolidation
- **Record Merging**: Combined root `animerecord.json` (87 entries) with `json_data/` version (5 entries)
- **Zero Data Loss**: All 91 anime records preserved with automatic backups
- **Enhanced Sync**: Collection manager now syncs with records database for accurate episode counts
- **Backup System**: Automatic timestamped backups before any data modifications

### 🛠️ IMPROVEMENTS

#### Collection Management
- **Robust Episode Tracking**: Fixed 0.0% completion issues by syncing with records database
- **Manual Episode Setting**: New `--collection set-episodes <title> <count>` command
- **Data Paths Command**: `--collection data-paths` shows current data structure and usage
- **Smart Title Matching**: Fuzzy matching for sync between collection and records systems
- **Debug Logging**: Enhanced logging for troubleshooting data sync issues

#### Code Organization
- **Centralized Configuration**: `config.py` manages all data paths and migration logic
- **Cleaner Imports**: Reduced hardcoded paths throughout codebase
- **Modular Architecture**: Clear separation between records (manager.py) and collection (collection_manager.py) systems

### 🔧 CHANGED
- **Data Locations**: All user data moved from scattered locations to `data/` folder
- **Migration Logic**: One-time automatic migration with `.migrated` flag to prevent re-runs
- **Git Structure**: Updated `.gitignore` to protect user privacy while preserving project structure
- **Legacy Cleanup**: Removed obsolete files and consolidated changelog management

### 🗑️ REMOVED
- **Root Artifacts**: Cleaned up `autopahe.log`, `cache_backup.json` from root directory
- **One-time Scripts**: Removed `merge_records.py` after successful migration
- **Legacy Paths**: Eliminated hardcoded paths in favor of centralized configuration

### 📊 VERIFIED FUNCTIONALITY
- ✅ 91 anime records successfully migrated and accessible
- ✅ Collection system shows accurate completion percentages
- ✅ Automatic migration runs only once with proper backups
- ✅ New installations work cleanly with `data/.gitkeep`
- ✅ Privacy protection prevents user data from being tracked

### 📁 NEW FILES
- `config.py` - Centralized configuration and data path management
- `data/.gitkeep` - Preserves directory structure for new users
- `data/records/animerecord.json` - Consolidated anime database (91 entries)

### 🔄 MODIFIED FILES
- `features/manager.py` - Updated to use centralized config
- `features/collection_manager.py` - Enhanced sync and data paths commands
- `auto_pahe.py` - Updated imports and collection handling
- `.gitignore` - Enhanced privacy protection for user data

---

## [v3.2.0] - 2024-11-23

### 🎬 ADDED
- **Cross-Platform Streaming**: Stream anime directly to media players
- **Auto Player Detection**: Automatically detects VLC, MPV, Windows Media Player, MPC-HC, MPC-BE, Iina, SMPlayer, Celluloid
- **Smart Fallback**: Provides installation guidance when no media player is found
- **Streaming Commands**: New `-st/--stream` argument for instant streaming
- **Player Support Matrix**: Comprehensive support for Windows, macOS, and Linux players
- **Installation Guides**: OS-specific setup instructions for missing players

### ⚡ IMPROVED
- **Performance**: 5-10x faster HTML parsing by removing BeautifulSoup dependency
- **Startup Speed**: Faster application launch with optimized imports
- **Memory Usage**: Reduced memory footprint with unified cache management
- **Cache Efficiency**: Instant anime information loading from disk cache
- **Code Organization**: Streamlined error handling and reduced duplication

### 🛠️ CHANGED
- **Dependencies**: Removed BeautifulSoup4 and lxml for smaller footprint
- **Folder Creation**: Fixed duplicate Anime folder creation issue
- **Collection Manager**: Disabled redundant organization - `--sort` handles all file organization
- **File Organization**: Cleaner separation between downloading and sorting workflows

### 🔧 REMOVED
- **Unused Modules**: Removed `cookies.py` and `execution_tracker.py` for optimization
- **Redundant Code**: Eliminated duplicate filter functions and error handling blocks
- **Heavy Dependencies**: Streamlined dependency list for faster installation

### 📚 DOCUMENTATION
- **Streaming Section**: Comprehensive documentation with examples for all platforms
- **Player Support**: Detailed matrix of supported media players by OS
- **Installation Guides**: Step-by-step setup instructions for missing players
- **Performance Notes**: Highlighted major speed improvements in README

## [v3.1.0] - 2024-11-22

### 🎯 MAJOR NEW FEATURES

#### 🔍 Smart Search with Fuzzy Matching
- **Automatic typo correction** for anime titles (e.g., "deth note" → "death note")
- **Confidence scoring** for search matches with configurable threshold
- **Genre and year filter extraction** from natural language queries
- **Common anime title corrections** built-in
- **CLI Options**: `--no-fuzzy`, `--fuzzy-threshold <0.0-1.0>`

#### 🔄 Smart Resume System
- **Persistent download state** across application sessions
- **Automatic retry** with exponential backoff on failures
- **Quality fallback** (1080p → 720p → 480p → 360p) on repeated failures
- **Download progress tracking** with checksum verification
- **Resume capability** for interrupted downloads
- **CLI Options**: `--resume`, `--resume-stats`, `--max-retries <n>`

#### 📚 Collection Manager
- **Automatic episode organization** into structured folders
- **Duplicate detection** and cleanup based on file hashes
- **Watch status tracking** (watching, completed, on_hold, dropped, plan_to_watch)
- **Series completion percentage** and missing episode detection
- **Export/Import** collection data in JSON format
- **Rating system** (1-10) for anime
- **CLI Options**: `--collection <stats|organize|duplicates|export|import>`, `--watch-status`, `--rate <1-10>`

### 🔧 ENHANCEMENTS

#### Download System
- **Fixed resolution selection** to properly handle 360p/480p requests
- **Enhanced download link extraction** parsing text content for resolution info
- **Improved error handling** and debug logging
- **Integration with resume and collection managers**

#### Cache System
- **Instant cache hit indicator** (⚡) for visual feedback
- **Enhanced cache statistics** and management
- **Better cache expiry handling**

#### CLI Interface
- **Updated help menu** with categorized options and emojis
- **New feature arguments** properly integrated
- **Better error messages** and user feedback

### 🧪 TESTING
- **Comprehensive test suite** covering all major features
- **Real-world download testing** with anime "86 Eighty-Six"
- **Integration testing** between all components
- **Performance verification** for cache and search systems

### 📊 VERIFIED FUNCTIONALITY
- ✅ Fuzzy search with typo correction working
- ✅ Download resume system operational
- ✅ Collection management features functional
- ✅ Cache system with instant access working
- ✅ All CLI arguments properly integrated
- ✅ Download functionality verified with real anime

### 📁 NEW FILES
- `ap_core/fuzzy_search.py` - Fuzzy search engine implementation
- `ap_core/resume_manager.py` - Smart resume system
- `ap_core/collection_manager.py` - Collection management
- `tests/test_all_features.py` - Comprehensive test suite
- `CHANGELOG.md` - Version history and changes

### 🔄 MODIFIED FILES
- `auto_pahe.py` - Integrated all new features and CLI arguments
- Various core modules enhanced for new functionality

---

## [v3.0.0] - Previous Release
- Enhanced caching system
- Multi-download support
- Browser optimization
- Records management
- And more...

---

*For detailed usage examples, see the README.md file or run `auto_pahe.py --help`*
