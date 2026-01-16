# AutoPahe Docker PowerShell Script for Windows
# This script helps build and run the AutoPahe Docker container

param(
    [Parameter(Position=0)]
    [ValidateSet("build", "run", "compose", "shell", "clean")]
    [string]$Action = "help",
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$CommandArgs = @()
)

# Colors for output
$ErrorActionPreference = "Stop"

Write-Host "AutoPahe Docker PowerShell Script" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Create data directories if they don't exist
$dirs = @("data", "json_data", "collection")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Yellow
    }
}

# Create Downloads directory if it doesn't exist
$downloadsDir = "$env:USERPROFILE\Downloads\autopahe"
if (-not (Test-Path $downloadsDir)) {
    New-Item -ItemType Directory -Path $downloadsDir | Out-Null
    Write-Host "Created directory: $downloadsDir" -ForegroundColor Yellow
}

# Function to join arguments properly
function Join-Arguments {
    param([string[]]$Args)
    $result = @()
    foreach ($arg in $Args) {
        if ($arg -match '\s') {
            $result += "`"$arg`""
        } else {
            $result += $arg
        }
    }
    return $result -join ' '
}

# Function to build the Docker image
function Build-Image {
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t autopahe:latest .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Image built successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to build image" -ForegroundColor Red
        exit 1
    }
}

# Function to run the container
function Run-Container {
    $cmd = Join-Arguments -Args $CommandArgs
    if (-not $cmd) {
        $cmd = "--help"
    }
    
    Write-Host "Running AutoPahe with command: $cmd" -ForegroundColor Yellow
    
    $currentDir = Get-Location
    docker run -it --rm `
        -v "${currentDir}\data:/app/data" `
        -v "${currentDir}\json_data:/app/json_data" `
        -v "${currentDir}\collection:/app/collection" `
        -v "${downloadsDir}:/app/downloads" `
        -e AUTOPAHE_DOWNLOAD_DIR=/app/downloads `
        autopahe:latest $cmd
}

# Function to run with docker-compose
function Run-Compose {
    $cmd = Join-Arguments -Args $CommandArgs
    if (-not $cmd) {
        $cmd = "--help"
    }
    
    Write-Host "Running with docker-compose..." -ForegroundColor Yellow
    docker-compose run --rm autopahe $cmd
}

# Function to open shell
function Open-Shell {
    Write-Host "Opening PowerShell in container..." -ForegroundColor Yellow
    
    $currentDir = Get-Location
    docker run -it --rm `
        -v "${currentDir}\data:/app/data" `
        -v "${currentDir}\json_data:/app/json_data" `
        -v "${currentDir}\collection:/app/collection" `
        -v "${downloadsDir}:/app/downloads" `
        -e AUTOPAHE_DOWNLOAD_DIR=/app/downloads `
        --entrypoint powershell `
        autopahe:latest
}

# Function to clean up
function Clean-Up {
    Write-Host "Cleaning up Docker resources..." -ForegroundColor Yellow
    
    # Remove stopped containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    Write-Host "✅ Cleanup completed!" -ForegroundColor Green
}

# Main script logic
switch ($Action) {
    "build" {
        Build-Image
    }
    "run" {
        Build-Image
        Run-Container
    }
    "compose" {
        Run-Compose
    }
    "shell" {
        Open-Shell
    }
    "clean" {
        Clean-Up
    }
    default {
        Write-Host "Usage: .\docker-run.ps1 [build|run|compose|shell|clean] [command]" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Cyan
        Write-Host "  build          - Build the Docker image"
        Write-Host "  run [cmd]      - Build and run with docker run"
        Write-Host "  compose [cmd]  - Run with docker-compose"
        Write-Host "  shell          - Open a PowerShell shell in the container"
        Write-Host "  clean          - Clean up Docker resources"
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Cyan
        Write-Host "  .\docker-run.ps1 build"
        Write-Host "  .\docker-run.ps1 run --help"
        Write-Host "  .\docker-run.ps1 run search 'one piece'"
        Write-Host "  .\docker-run.ps1 run -s 'one piece' -i 0 -d 1"
        Write-Host "  .\docker-run.ps1 compose download -u <anime-url>"
        Write-Host ""
        Write-Host "Note: No need to escape quotes, just pass arguments normally!" -ForegroundColor Green
    }
}
