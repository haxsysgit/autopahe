# AutoPahe Advanced Usage Guide

> **Complete command reference and advanced features for power users**

This guide covers all the advanced features, configuration options, and detailed command usage for AutoPahe.

## 📋 Complete Command Reference

### Search & Download Commands

| Command | Description | Example |
|---------|-------------|---------|
| `-s, --search TEXT` | Search for anime by name | `-s "Attack on Titan"` |
| `-i, --index INT` | Select anime from search results | `-i 0` (first result) |
| `-d, --single_download INT` | Download single episode | `-d 1` |
| `-md, --multi_download TEXT` | Download multiple episodes | `-md "1-5,7,10-12"` |
| `-l, --link` | Get download link without downloading | `-l 1` |
| `-ml, --multilinks` | Get multiple download links | `-ml "1-5"` |
| `-a, --about` | Show anime overview | `-a` |

### Advanced Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `-b, --browser TEXT` | Browser choice | firefox | `-b chrome` |
| `-p, --resolution TEXT` | Video quality | 720p | `-p 1080` |
| `-w, --workers INT` | Parallel download workers | 1 | `-w 3` |
| `--notify` | Enable desktop notifications | false | `--notify` |
| `--verbose` | Show detailed logging | false | `--verbose` |
| `--quiet` | Show minimal output | false | `--quiet` |

### Search Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `--year INT` | Filter by release year | `--year 2023` |
| `--status TEXT` | Filter by airing status | `--status "Finished Airing"` |

### Batch Downloads

| Option | Description | Example |
|--------|-------------|---------|
| `--season INT` | Download entire season | `--season 1` (eps 1-12) |

## ⚙️ Configuration System

### Creating Configuration

Generate a sample configuration file:
```bash
autopahe --write-config
```

This creates `~/.config/autopahe/config.ini` with default settings.

### Configuration Options

```ini
[defaults]
# Browser choice: firefox or chrome
browser = firefox

# Video quality: 480, 720, 1080
resolution = 720

# Parallel download workers (1 = sequential)
workers = 1

# Custom download directory (optional)
# download_dir = /home/user/Videos/Anime

# Enable desktop notifications
notifications = false

# Auto-sort downloaded files
sort_on_complete = false
sort_mode = rename

# Custom sort directory (optional)
sort_path = 

# Logging level: DEBUG, INFO, WARNING, ERROR
log_level = INFO
```

### Loading Configuration

Config files are loaded in this order:
1. `--config /path/to/config.ini` (explicit)
2. `~/.config/autopahe/config.ini`
3. `~/.autopahe.ini`
4. `./autopahe.ini`

## 📦 Advanced Download Operations

### Parallel Downloads

Download multiple episodes simultaneously:
```bash
autopahe -s "My Hero Academia" -i 0 -md "1-10" -w 3
```

**Warning**: Parallel downloads may trigger DDoS-Guard protection. Use with caution.

### Quality Selection

Choose specific video quality:
```bash
# 1080p (best quality)
autopahe -s "Anime Name" -i 0 -d 1 -p 1080

# 480p (smaller file size)
autopahe -s "Anime Name" -i 0 -d 1 -p 480
```

### Episode Ranges

Multiple episode selection formats:
```bash
# Individual episodes
autopahe -s "Anime" -i 0 -md "1,3,5,7"

# Range of episodes
autopahe -s "Anime" -i 0 -md "1-12"

# Mixed format
autopahe -s "Anime" -i 0 -md "1-5,7,10-12"

# Entire season (12-13 episodes)
autopahe -s "Anime" -i 0 --season 1
```

## 🗂️ File Organization

### Sorting Modes

```bash
# Preview changes without applying
autopahe --sort all --sort-dry-run

# Rename files only
autopahe --sort rename

# Organize into folders
autopahe --sort organize

# Full sorting (rename + organize)
autopahe --sort all

# Custom directory
autopahe --sort all --sort-path ~/Downloads
```

### Automatic Sorting

Enable in config file:
```ini
sort_on_complete = true
sort_mode = all
```

## 📊 Record Management

### Basic Operations

```bash
# View all records
autopahe -R view

# Search records
autopahe -R search "naruto"

# Delete a record
autopahe -R delete "Naruto"
```

### Advanced Record Operations

```bash
# Update watching progress
autopahe -R progress "Naruto" 27

# Rate an anime (0-10)
autopahe -R rate "Naruto" 9.5

# Rename an anime in records
autopahe -R rename "Naruto" "Naruto Shippuden"

# Set custom keyword/tag
autopahe -R set-keyword "Naruto" "shonen"

# Filter by status
autopahe -R list-status "watching"
autopahe -R list-status "completed"
autopahe -R list-status "on_hold"
```

### Import/Export Records

```bash
# Export to JSON
autopahe -R export backup.json json

# Export to CSV
autopahe -R export records.csv csv

# Import from backup
autopahe -R import backup.json
```

## 💾 Cache Management

### Cache Operations

```bash
# View cache statistics
autopahe --cache stats

# Clear all cache and cookies
autopahe --cache clear
```

### Cache Benefits

- **API Response Caching**: 6-hour cache for faster repeat searches
- **Cookie Persistence**: 24-hour session cookies reduce DDoS-Guard challenges
- **Auto-cleanup**: Old entries removed automatically

## 📈 Statistics and Monitoring

### Execution Statistics

```bash
# Today's activity
autopahe -dt "today"

# This week
autopahe --summary "this week"

# Custom date range
autopahe --summary "from 2025-11-01 to 2025-11-30"

# All time statistics
autopahe --summary "all"
```

### Progress Tracking

Multi-episode downloads show real-time progress:
- Visual progress bars (requires `tqdm`)
- Episode completion status
- Failed episode tracking

## 🔔 Desktop Notifications

### Enable Notifications

```bash
# Command line flag
autopahe -s "Anime" -i 0 -md "1-5" --notify

# Or enable in config
notifications = true
```

### Platform Support

- **Windows**: PowerShell toast notifications (built-in)
- **macOS**: AppleScript notifications (built-in)
- **Linux**: `notify-send` (requires `libnotify-bin`)

Install on Linux:
```bash
sudo apt install libnotify-bin  # Ubuntu/Debian
```

## 🛠️ Performance Tuning

### Optimization Tips

1. **Sequential Downloads**: Use `-w 1` for stability
2. **Cache Usage**: Let cache build for faster repeat searches
3. **Browser Choice**: Firefox is generally more stable
4. **Network**: Stable connection prevents interruptions

### Troubleshooting

#### DDoS-Guard Protection
Symptoms: Captcha challenges, blocked access
Solutions:
- Wait a few minutes and retry
- Use sequential downloads (`-w 1`)
- Clear cache: `autopahe --cache clear`

#### Download Failures
Symptoms: Episodes fail to download
Solutions:
- Check internet connection
- Try different browser: `-b chrome`
- Use verbose mode: `--verbose`
- Check log file: `autopahe.log`

#### Performance Issues
Symptoms: Slow downloads or searches
Solutions:
- Enable caching (default)
- Use appropriate quality: `-p 720`
- Limit parallel workers: `-w 2`

## 📝 Logging System

### Log Levels

```bash
# Default (INFO) - normal operation
autopahe -s "Anime"

# Verbose (DEBUG) - detailed information
autopahe -s "Anime" --verbose

# Quiet (WARNING) - errors only
autopahe -s "Anime" --quiet
```

### Log Files

- Location: `autopahe.log` in current directory
- Rotation: Log file grows indefinitely
- Content: All operations, errors, and debug information

## 🔧 Environment Variables

### Supported Variables

```bash
# Custom config location
export AUTOPAHE_CONFIG=/path/to/config.ini

# Custom download directory
export AUTOPAHE_DOWNLOAD_DIR=/path/to/downloads

# Custom cache directory
export AUTOPAHE_CACHE_DIR=/path/to/cache
```

## 🚀 Command Line Examples

### Complete Workflow

```bash
# 1. Search with filters
autopahe -s "Naruto" --year 2007 --status "Finished Airing"

# 2. Select and download season 1 with notifications
autopahe -s "Naruto" -i 0 --season 1 --notify

# 3. Update watching progress
autopahe -R progress "Naruto" 26

# 4. Rate the anime
autopahe -R rate "Naruto" 9.0
```

### Power User Commands

```bash
# Fast parallel download with custom settings
autopahe -s "One Piece" -i 0 -md "900-920" -w 3 -p 720 --notify

# Search and get links only
autopahe -s "Attack on Titan" -i 0 -ml "1-5"

# Batch operations with custom config
autopahe --config /custom/config.ini -s "Anime" -i 0 --season 1

# Statistics and monitoring
autopahe --summary "this month" -dt "last 30 days"
```

## 🆘 Advanced Troubleshooting

### Debug Mode

```bash
# Enable full debugging
autopahe -s "Anime" --verbose

# Check log file for details
tail -f autopahe.log
```

### Reset and Recovery

```bash
# Clear all cached data
autopahe --cache clear

# Reset configuration
rm ~/.config/autopahe/config.ini
autopahe --write-config

# Check system status
autopahe --cache stats
```

### Performance Monitoring

```bash
# Monitor download progress
autopahe -s "Anime" -i 0 -md "1-10" --verbose

# Check execution statistics
autopahe -dt "today"
autopahe --summary "this week"
```

---

## 📞 Getting Help

For advanced issues and questions:
- **GitHub Issues**: [Report bugs and request features](https://github.com/haxsysgit/autopahe/issues)
- **Discussions**: [Community support and discussions](https://github.com/haxsysgit/autopahe/discussions)
- **Documentation**: [Check the main README](README.md) for basic usage

---

**Master AutoPahe with these advanced features! 🚀**
