@echo off
REM AutoPahe Docker Batch Script for Windows
REM This script helps build and run the AutoPahe Docker container

setlocal enabledelayedexpansion

echo AutoPahe Docker Batch Script
echo ===========================

REM Create data directories if they don't exist
if not exist "data" mkdir data
if not exist "json_data" mkdir json_data
if not exist "collection" mkdir collection

if "%1"=="build" goto :build
if "%1"=="run" goto :run
if "%1"=="compose" goto :compose
if "%1"=="shell" goto :shell
if "%1"=="clean" goto :clean
goto :help

:build
echo Building Docker image...
docker build -t autopahe:latest .
if %ERRORLEVEL% EQU 0 (
    echo ✅ Image built successfully!
) else (
    echo ❌ Failed to build image
    exit /b 1
)
goto :end

:run
call :build
echo Running AutoPahe with command: %2 %3 %4 %5 %6 %7 %8 %9
docker run -it --rm ^
    -v "%cd%\data:/app/data" ^
    -v "%cd%\json_data:/app/json_data" ^
    -v "%cd%\collection:/app/collection" ^
    autopahe:latest %2 %3 %4 %5 %6 %7 %8 %9
goto :end

:compose
echo Running with docker-compose...
docker-compose run --rm autopahe %2 %3 %4 %5 %6 %7 %8 %9
goto :end

:shell
echo Opening command prompt in container...
docker run -it --rm ^
    -v "%cd%\data:/app/data" ^
    -v "%cd%\json_data:/app/json_data" ^
    -v "%cd%\collection:/app/collection" ^
    --entrypoint cmd ^
    autopahe:latest
goto :end

:clean
echo Cleaning up Docker resources...
docker container prune -f
docker image prune -f
echo ✅ Cleanup completed!
goto :end

:help
echo Usage: docker-run.bat [build^|run^|compose^|shell^|clean] [command]
echo.
echo Commands:
echo   build          - Build the Docker image
echo   run [cmd]      - Build and run with docker run
echo   compose [cmd]  - Run with docker-compose
echo   shell          - Open a command prompt in the container
echo   clean          - Clean up Docker resources
echo.
echo Examples:
echo   docker-run.bat build
echo   docker-run.bat run --help
echo   docker-run.bat run search "one piece"
echo   docker-run.bat run -s "one piece" -i 0 -d 1
echo   docker-run.bat compose download -u ^<anime-url^>
echo.
echo Note: Use quotes for arguments with spaces!

:end
endlocal
