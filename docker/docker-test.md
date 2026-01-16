# Docker Testing Guide

## Build the Image
```bash
docker build -t autopahe:latest .
```

## Test Basic Functionality
```bash
# Test help command
docker run -it --rm autopahe:latest --help

# Test search (this will test Playwright browser)
docker run -it --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/json_data:/app/json_data \
  autopahe:latest -s "one piece"

# Test with the helper script
./docker/docker-run.sh run --help
```

## Expected Outcomes
1. Help command should display all available options
2. Search should work and display anime results
3. No permission errors on volume mounts
4. Playwright browser should launch without issues

## Troubleshooting
- If browser fails to launch, check Playwright installation
- If permission errors, ensure data directories exist on host
- If memory issues, consider increasing Docker memory limit
