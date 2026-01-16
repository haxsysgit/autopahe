# Docker Testing Guide for Windows

## Prerequisites
- Docker Desktop for Windows installed and running
- PowerShell (recommended) or Command Prompt

## Build the Image
```powershell
# In PowerShell
docker build -t autopahe:latest .

# Or using the helper script
docker\docker-run.ps1 build
```

## Test Basic Functionality

### Using PowerShell Script (Recommended)
```powershell
# Test help command
docker\docker-run.ps1 run --help

# Test search (this will test Playwright browser)
docker\docker-run.ps1 run '-s "one piece"'

# Open a shell in the container
docker\docker-run.ps1 shell
```

### Using Batch File (Command Prompt)
```cmd
# Test help command
docker\docker-run.bat run --help

# Test search
docker\docker-run.bat run -s "one piece"

# Open a shell in the container
docker\docker-run.bat shell
```

### Manual Docker Commands
```powershell
# PowerShell syntax
docker run -it --rm `
  -v "${pwd}\data:/app/data" `
  -v "${pwd}\json_data:/app/json_data" `
  -v "${pwd}\collection:/app/collection" `
  autopahe:latest --help
```

```cmd
REM Command Prompt syntax
docker run -it --rm ^
  -v "%cd%\data:/app/data" ^
  -v "%cd%\json_data:/app/json_data" ^
  -v "%cd%\collection:/app/collection" ^
  autopahe:latest --help
```

## Expected Outcomes
1. Help command should display all available options
2. Search should work and display anime results
3. No permission errors on volume mounts
4. Playwright browser should launch without issues

## Windows-Specific Troubleshooting

### Volume Mount Issues
- Ensure Docker Desktop has access to the drive where the project is located
- Go to Docker Desktop > Settings > Resources > File Sharing
- Add the drive letter (e.g., C:) if not already present

### Path Issues
- Use forward slashes in PowerShell: `${pwd}/data`
- Use backslashes in Command Prompt: `%cd%\data`
- The helper scripts handle this automatically

### Permission Issues
- Run PowerShell as Administrator if needed
- Ensure the data directories exist on the host
- Check Docker Desktop file sharing permissions

### Performance Tips
- Use WSL 2 backend for better performance
- Allocate sufficient memory to Docker Desktop (4GB+ recommended)
- Use SSD storage for better I/O performance

## Clean Up
```powershell
# Clean up Docker resources
docker\docker-run.ps1 clean

# Or manually
docker container prune -f
docker image prune -f
```
