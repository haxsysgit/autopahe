# AutoPahe v3.5.0 Release Notes

## 🐳 Major New Feature: Docker Support

AutoPahe now includes comprehensive Docker support for easy cross-platform deployment!

### Docker Features Added:
- **Complete Docker Setup**: Dockerfile and docker-compose.yml included
- **Cross-Platform Helper Scripts**: 
  - Linux/Mac: `docker/docker-run.sh`
  - Windows PowerShell: `docker/docker-run.ps1`
  - Windows CMD: `docker/docker-run.bat`
- **Smart Download Handling**: Downloads automatically go to your host Downloads folder
- **Input Sanitization**: No need to manually escape quotes in most cases
- **Persistent Data**: Volume mounts for data, cache, and collection

### Quick Start with Docker:
```bash
# Linux/Mac
docker/docker-run.sh build
docker/docker-run.sh run -s "one piece" -i 0 -d 1

# Windows PowerShell
docker\docker-run.ps1 build
docker\docker-run.ps1 run -s "one piece" -i 0 -d 1
```

### Documentation Added:
- `docker/README.md` - Helper script documentation
- `docker/docker-test.md` - Testing guide
- `docker/docker-test-windows.md` - Windows-specific testing
- `docker/downloads-guide.md` - Complete downloads guide

## 🔄 Improvements:
- Updated Playwright to v1.56.0
- Fixed argument parsing for quoted strings
- Added environment variable support for custom download paths
- Removed legacy data directories from .gitignore
- Fixed permission issues in Docker container

## 📦 Package Updates:
- Version bumped to 3.5.0
- Published to PyPI with all Docker assets

## 🚀 Installation:
```bash
# From PyPI (recommended)
pip install autopahe==3.5.0

# With Docker
git clone https://github.com/haxsysgit/autopahe.git
cd autopahe
docker build -t autopahe:latest .
```

## 🐛 Bug Fixes:
- Resolved Docker container permission errors
- Fixed multi-word argument handling in helper scripts
- Proper download directory mounting in Docker

## 📝 Notes:
- ADVANCED.md has been retained for power users
- All legacy documentation preserved
- Backward compatibility maintained

Enjoy the new Docker support! 🎉
