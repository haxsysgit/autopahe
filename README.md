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

**With Docker:**
```bash
git clone https://github.com/haxsysgit/autopahe.git
cd autopahe
docker build -t autopahe:latest .
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/json_data:/app/json_data \
  -v $(pwd)/collection:/app/collection \
  autopahe:latest --help
```

See the `docker/` directory for helper scripts and detailed documentation.

Or use the helper script:

**Linux/Mac:**
```bash
docker/docker-run.sh build
docker/docker-run.sh run --help
```

**Windows PowerShell:**
```powershell
docker\docker-run.ps1 build
docker\docker-run.ps1 run --help
```

**Windows Command Prompt:**
```cmd
docker\docker-run.bat build
docker\docker-run.bat run --help
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

## 🐳 Docker Usage

### Quick Start

**Linux/Mac:**
```bash
# Build and run with helper script
docker/docker-run.sh build
docker/docker-run.sh run --help

# Search for anime (no need to escape quotes!)
docker/docker-run.sh run search one piece
docker/docker-run.sh run -s one piece -i 0 -d 1

# Download episodes
docker/docker-run.sh run -s "one piece" -i 0 -md 1-5
```

**Windows PowerShell:**
```powershell
# Build and run with helper script
docker\docker-run.ps1 build
docker\docker-run.ps1 run --help

# Search for anime (no need to escape quotes!)
docker\docker-run.ps1 run search one piece
docker\docker-run.ps1 run -s one piece -i 0 -d 1

# Download episodes
docker\docker-run.ps1 run -s "one piece" -i 0 -md 1-5
```

**Windows Command Prompt:**
```cmd
# Build and run with helper script
docker\docker-run.bat build
docker\docker-run.bat run --help

# Search for anime (use quotes for spaces)
docker\docker-run.bat run search "one piece"
docker\docker-run.bat run -s "one piece" -i 0 -d 1

# Download episodes
docker\docker-run.bat run -s "one piece" -i 0 -md 1-5
```

### Docker Commands

**Linux/Mac:**
```bash
# Build image
docker build -t autopahe:latest .

# Run with volume mounts
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/json_data:/app/json_data \
  -v $(pwd)/collection:/app/collection \
  autopahe:latest [command]

# Use docker-compose
docker-compose run --rm autopahe --help

# Open shell in container
docker/docker-run.sh shell
```

**Windows PowerShell:**
```powershell
# Build image
docker build -t autopahe:latest .

# Run with volume mounts
docker run -it --rm `
  -v "${pwd}\data:/app/data" `
  -v "${pwd}\json_data:/app/json_data" `
  -v "${pwd}\collection:/app/collection" `
  autopahe:latest [command]

# Use docker-compose
docker-compose run --rm autopahe --help

# Open shell in container
docker\docker-run.ps1 shell
```

**Windows Command Prompt:**
```cmd
# Build image
docker build -t autopahe:latest .

# Run with volume mounts
docker run -it --rm ^
  -v "%cd%\data:/app/data" ^
  -v "%cd%\json_data:/app/json_data" ^
  -v "%cd%\collection:/app/collection" ^
  autopahe:latest [command]

# Use docker-compose
docker-compose run --rm autopahe --help

# Open shell in container
docker\docker-run.bat shell
```

### Volume Mounts
- `./data` - Download storage
- `./json_data` - Cache and metadata
- `./collection` - Your anime collection

### Additional Documentation
- See `docker/docker-test.md` for testing guide
- See `docker/docker-test-windows.md` for Windows-specific testing
- See `docker/README.md` for helper script documentation
- See `docker/downloads-guide.md` for complete downloads guide

### Script Features
- **Input Sanitization**: No need to manually escape quotes in most cases
- **Auto Directory Creation**: Scripts create necessary data directories
- **Cross-Platform**: Separate scripts for Linux/Mac, PowerShell, and CMD
- **Clean Command**: Easy Docker resource cleanup with `clean` option

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
