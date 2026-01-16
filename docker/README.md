# Docker Directory

This directory contains Docker-related helper scripts and documentation for AutoPahe.

## Files

### Helper Scripts
- **docker-run.sh** - Bash script for Linux/Mac systems
- **docker-run.ps1** - PowerShell script for Windows PowerShell
- **docker-run.bat** - Batch file for Windows Command Prompt

All scripts provide the same functionality:
- `build` - Build the Docker image
- `run [command]` - Build and run with specified command
- `compose [command]` - Run using docker-compose
- `shell` - Open an interactive shell in the container
- `clean` - Clean up Docker resources

### Documentation
- **docker-test.md** - General testing guide for all platforms
- **docker-test-windows.md** - Windows-specific testing instructions and troubleshooting

## Quick Start

### Linux/Mac
```bash
chmod +x docker-run.sh
./docker-run.sh build
./docker-run.sh run --help
```

### Windows PowerShell
```powershell
.\docker-run.ps1 build
.\docker-run.ps1 run --help
```

### Windows Command Prompt
```cmd
docker-run.bat build
docker-run.bat run --help
```

## Notes
- All scripts automatically create necessary data directories
- Volume mounts are handled automatically based on your platform
- Scripts use relative paths to work from any location
