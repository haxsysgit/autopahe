
<!-- Badges -->
[![PyPI version](https://badge.fury.io/py/autopahe.svg)](https://pypi.org/project/autopahe/)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/haxsysgit/autopahe/)
[![License](https://img.shields.io/github/license/haxsysgit/autopahe?color=brightgreen)](https://github.com/haxsysgit/autopahe/blob/main/license.md)
[![OpenIssues](https://img.shields.io/github/issues/haxsysgit/autopahe?color=important)](https://github.com/haxsysgit/autopahe/issues)
<!--LineBreak-->
[![Windows](https://img.shields.io/badge/Windows-white?style=flat-square&logo=windows&logoColor=blue)](https://github.com/haxsysgit/autopahe/)
[![macOS](https://img.shields.io/badge/macOS-white?style=flat-square&logo=apple&logoColor=black)](https://github.com/haxsysgit/autopahe/)
[![Linux](https://img.shields.io/badge/Linux-white?style=flat-square&logo=linux&logoColor=black)](https://github.com/haxsysgit/autopahe/)
<!-- Badges -->

# AutoPahe

> **Download and stream anime episodes easily from AnimePahe**

A simple yet powerful tool to search, download, and stream your favorite anime episodes. Works on Windows, Mac, and Linux with a beautiful, colorful interface.

## ✨ New in v3.3

### 🗂️ **Centralized Data Architecture**
- **Unified data directory** - All project data now organized in `data/` folder
- **Automatic migration** - Seamless upgrade from older versions with zero data loss
- **Privacy protection** - User data excluded from git, clean project structure
- **Portable mode** - Support for portable installations via environment variable
- **Data management** - `--collection data-paths` shows current data structure

### 📚 **Enhanced Collection Management**
- **Accurate episode tracking** - Fixed 0.0% completion issues with database sync
- **Manual episode setting** - `--collection set-episodes <title> <count>` command
- **Smart title matching** - Better sync between collection and records systems
- **91 anime records** - Consolidated database with comprehensive metadata

### 🛠️ **Code Organization**
- **Centralized configuration** - `config.py` manages all data paths and migration
- **Cleaner imports** - Reduced hardcoded paths throughout codebase
- **Modular architecture** - Clear separation between records and collection systems
- **Project cleanup** - Removed obsolete files and consolidated management

## ✨ New in v3.2

### 🎬 **Cross-Platform Streaming**
- **Stream directly** to your favorite media player (VLC, MPV, etc.)
- **Auto-detects players** on Windows, macOS, and Linux
- **Smart fallback** - suggests installation if no player found
- **One-command streaming**: `autopahe -s "anime name" -i 0 -st 1`

### ⚡ **Major Performance Boost**
- **Instant anime info** - loads cached data in milliseconds
- **Removed heavy dependencies** - faster startup and smaller footprint
- **Optimized caching** - smarter memory usage and disk storage
- **5-10x faster** HTML parsing with native selectors

### 🛠️ **Enhanced Organization**
- **Fixed duplicate folder creation** - cleaner file management
- **Streamlined sorting** - `--sort` now handles all organization
- **Better memory management** - reduced resource usage

## 🎯 What It Does

- **Search Anime** - Find any anime by name with smart suggestions
- **Download Episodes** - Get single episodes or entire seasons
- **Fast Downloads** - Download multiple episodes at once
- **Resume Downloads** - Pick up where you left off if interrupted
- **Organize Collection** - Keep your downloaded anime neatly organized
- **Desktop Notifications** - Get alerts when downloads finish

## 🚀 Quick Start

### Installation

#### 🚀 **Easiest Setup (Recommended)**
```bash
# Clone and run our automated installer
git clone https://github.com/haxsysgit/autopahe.git
cd autopahe
python install.py
```

#### 📦 **Alternative Methods**

**Using UV (fastest):**
```bash
git clone https://github.com/haxsysgit/autopahe.git
cd autopahe
uv sync
uv run playwright install
```

**Using pip:**
```bash
git clone https://github.com/haxsysgit/autopahe.git
cd autopahe
pip install -r requirements.txt
playwright install
```

**From PyPI:**
```bash
pip install autopahe
autopahe --setup  # Required first-time setup
```

### 🔧 First-Time Setup (Required)

After installation, run the setup command once to install browser engines:

```bash
autopahe --setup
```

This installs Playwright browsers (~500MB) needed for bypassing DDoS protection. You only need to do this once.

### Basic Usage
```bash
# Search for anime
autopahe -s "your anime name"

# Download a single episode
autopahe -s "anime name" -i 0 -d 1

# Download entire season
autopahe -s "anime name" -i 0 -md 1-12
```
## 📖 More Examples

### Download Different Quality
```bash
# Download in 1080p (best quality)
autopahe -s "anime name" -i 0 -d 1 -p 1080

# Download in 360p (smaller file size)
autopahe -s "anime name" -i 0 -d 1 -p 360
```

### Download Multiple Episodes
```bash
# Download episodes 1, 3, and 5
autopahe -s "anime name" -i 0 -md "1,3,5"

# Download episodes 1 through 12
autopahe -s "anime name" -i 0 -md "1-12"

# Download with faster parallel downloads
autopahe -s "anime name" -i 0 -md "1-12" --workers 3

# Download English dubbed versions (if available)
autopahe -s "anime name" -i 0 -md "1-12" --dub
```

### 🎬 Stream Anime Episodes (NEW in v3.2)
```bash
# Stream episode 1 directly (auto-detects player)
autopahe -s "anime name" -i 0 -st 1

# Stream with specific player
autopahe -s "anime name" -i 0 -st 1 --player vlc
autopahe -s "anime name" -i 0 -st 1 --player mpv

# Stream multiple episodes
autopahe -s "anime name" -i 0 -st "1-3"

# Stream in different quality
autopahe -s "anime name" -i 0 -st 1 -p 1080

# Stream English dubbed versions (if available)
autopahe -s "anime name" -i 0 -st 1 --dub
```

**Supported Players:**
- **Windows**: VLC, MPV, Windows Media Player, MPC-HC, MPC-BE
- **macOS**: VLC, MPV, Iina
- **Linux**: VLC, MPV, MPlayer, SMPlayer, Celluloid

**If no player is found, AutoPahe will:**
- Show installation instructions for your OS
- Suggest available players
- Guide you through setup

### Get Download Links Only
```bash
# Get the download link without downloading
autopahe -s "anime name" -i 0 -l 1
```

## 💡 Tips

- Use quotes around anime names with spaces: `"Attack on Titan"`
- The first time you run it, it may take a moment to set up
- Downloads go to your `Downloads/Anime` folder by default
- Use `--verbose` to see detailed information while downloading
- Use `--quiet` to see minimal output

## 🛠️ What You Need

- Python 3.8 or higher
- Internet connection
- About 500MB of free space for setup

**That's it!** The tool handles everything else automatically.

## 🎨 Beautiful Interface

AutoPahe features a colorful, organized interface that looks like a webpage:
- Clean section headers with progress indicators
- Colored text for easy reading
- Organized layout with proper spacing
- No technical clutter - just what you need

## 📱 Works Everywhere

- **Windows** - Full support with desktop notifications
- **Mac** - Native integration and notifications  
- **Linux** - Complete functionality

## 🆘 Need Help?

If you run into any issues:
1. Make sure you have Python 3.8 or higher
2. Check your internet connection
3. Try using quotes around anime names with spaces

For more help, visit our GitHub page or report an issue.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](license.md) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

If you need help or have questions, visit our [GitHub Issues](https://github.com/haxsysgit/autopahe/issues) page.

## 🔧 Advanced Usage

For power users who want more control and features, see our [Advanced Usage Guide](ADVANCED.md) which covers:

- **Detailed command reference** with all available options
- **Configuration system** for customizing settings
- **Batch operations** and parallel downloads
- **Record management** for tracking your anime collection
- **File organization** and sorting options
- **Performance tuning** and troubleshooting

---

**Enjoy AutoPahe! 🎬**
