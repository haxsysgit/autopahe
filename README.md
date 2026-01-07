<!-- Badges -->
[![PyPI version](https://badge.fury.io/py/autopahe.svg)](https://pypi.org/project/autopahe/)
[![License](https://img.shields.io/github/license/haxsysgit/autopahe?color=brightgreen)](https://github.com/haxsysgit/autopahe/blob/main/license.md)
[![Windows](https://img.shields.io/badge/Windows-0078D6?logo=windows)](https://github.com/haxsysgit/autopahe/)
[![macOS](https://img.shields.io/badge/macOS-000000?logo=apple)](https://github.com/haxsysgit/autopahe/)
[![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black)](https://github.com/haxsysgit/autopahe/)

# AutoPahe

> **Download and stream anime from AnimePahe**

Search, download, and stream anime episodes. Cross-platform (Windows, Mac, Linux).

## 🚀 Installation

**From PyPI (recommended):**
```bash
pip install autopahe
autopahe --setup
```

**From source:**
```bash
git clone https://github.com/haxsysgit/autopahe.git
cd autopahe
pip install -r requirements.txt
playwright install chromium
```

## 📖 Usage

```bash
# Search for anime
autopahe -s "anime name"

# Download episode 1
autopahe -s "anime name" -i 0 -d 1

# Download episodes 1-12
autopahe -s "anime name" -i 0 -md 1-12

# Stream episode 1
autopahe -s "anime name" -i 0 -st 1
```

### More Options
```bash
# Different quality (360, 480, 720, 1080)
autopahe -s "anime name" -i 0 -d 1 -p 1080

# Parallel downloads
autopahe -s "anime name" -i 0 -md 1-12 --workers 3

# English dub (if available)
autopahe -s "anime name" -i 0 -d 1 --dub

# Stream with specific player
autopahe -s "anime name" -i 0 -st 1 --player vlc
```

## ⚙️ Configuration

```bash
# Edit config
autopahe config edit

# Show config
autopahe config show

# Validate config
autopahe config validate
```

Config location:
- **Windows**: `%APPDATA%\autopahe\config.ini`
- **Linux/Mac**: `~/.config/autopahe/config.ini`

## 📚 Collection Management

```bash
# View collection stats
autopahe --collection stats

# Organize downloaded files
autopahe --collection organize

# Find duplicates
autopahe --collection duplicates
```

## 🎬 Supported Players

VLC, MPV, MPC-HC, MPC-BE (Windows), Iina (macOS), SMPlayer, Celluloid (Linux)

## 📜 License

MIT License - see [LICENSE](license.md)

## 🆘 Help

[GitHub Issues](https://github.com/haxsysgit/autopahe/issues) | [Discussions](https://github.com/haxsysgit/autopahe/discussions)
