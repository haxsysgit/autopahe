# AutoPahe Changelog

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
