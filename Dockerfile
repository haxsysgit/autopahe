FROM mcr.microsoft.com/playwright/python:v1.56.0-jammy

WORKDIR /app

# Install system dependencies and Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Copy application code
COPY . .

# Install the application in editable mode
RUN pip install -e .

# Create data directories
RUN mkdir -p /app/data/records /app/data/downloads /app/json_data /app/collection

# Set default environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AUTO_PAHE_DEV=1 \
    AUTOPAHE_DOWNLOAD_DIR=/app/data/downloads

# Expose volume mounts for persistent data
VOLUME ["/app/data", "/app/json_data", "/app/collection"]

ENTRYPOINT ["python", "-m", "auto_pahe"] 