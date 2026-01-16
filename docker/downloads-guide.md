# AutoPahe Downloads Guide

## How Downloads Work in Docker

When you run AutoPahe in Docker, all downloads are stored in the mounted volumes:

- **`./data`** - Main download directory and database
- **`./json_data`** - Cache and metadata  
- **`./collection`** - Your organized anime collection

## Download Commands

### Single Episode Download
```bash
# Linux/Mac
docker/docker-run.sh run -s "one piece" -i 0 -d 1

# Windows PowerShell
docker\docker-run.ps1 run -s "one piece" -i 0 -d 1

# Windows CMD
docker\docker-run.bat run -s "one piece" -i 0 -d 1
```

### Multiple Episodes (Range)
```bash
# Download episodes 1-12
docker/docker-run.sh run -s "one piece" -i 0 -md 1-12

# Download episodes 1, 3, 5-7
docker/docker-run.sh run -s "one piece" -i 0 -md "1,3,5-7"
```

### Quality Options
```bash
# Download in 1080p
docker/docker-run.sh run -s "one piece" -i 0 -d 1 -p 1080

# Download in 720p
docker/docker-run.sh run -s "one piece" -i 0 -d 1 -p 720

# Best quality available
docker/docker-run.sh run -s "one piece" -i 0 -d 1 -p best
```

### Parallel Downloads
```bash
# Download with 3 workers
docker/docker-run.sh run -s "one piece" -i 0 -md 1-12 -w 3
```

### English Dub (if available)
```bash
docker/docker-run.sh run -s "one piece" -i 0 -d 1 --dub
```

## Download Locations

### Inside Container
- Downloads are saved to `/app/data/downloads/` by default
- Database is stored at `/app/data/records/animerecord.json`

### On Host System
- Due to volume mounts, downloads appear in `./data/downloads/`
- Database is accessible at `./data/records/animerecord.json`

## Streaming Instead of Downloading

```bash
# Stream episode 1 with default player
docker/docker-run.sh run -s "one piece" -i 0 -st 1

# Stream with VLC
docker/docker-run.sh run -s "one piece" -i 0 -st 1 --player vlc

# Stream with MPV
docker/docker-run.sh run -s "one piece" -i 0 -st 1 --player mpv
```

Note: Streaming requires the player to be installed on your host system, not in the container.

## Managing Downloads

### View Download History
```bash
docker/docker-run.sh run --records
```

### Resume Failed Downloads
```bash
docker/docker-run.sh run --resume
```

### Clear Cache
```bash
docker/docker-run.sh run --cache clear
```

## Tips

1. **Large Downloads**: For large series, consider using `-w` (workers) to speed up downloads
2. **Storage**: Ensure you have enough disk space in the mounted volume
3. **Network**: Downloads depend on your network connection to AnimePahe
4. **Persistence**: All downloads persist between container runs due to volume mounts
5. **Quality**: Higher quality (1080p) files are larger and take longer to download

## Troubleshooting

### Permission Errors
If you get permission errors, ensure:
```bash
# On Linux/Mac
sudo chown -R $USER:$USER data/

# Or run with proper Docker user settings
```

### Download Fails
- Check your internet connection
- Try with `--max-retries 3`
- Clear cache with `--cache clear`
- Check if the episode is available on AnimePahe

### Storage Full
- Check disk space with `df -h`
- Clean old downloads from `./data/downloads/`
- Use lower quality (-p 720 or -p 480) for smaller files
