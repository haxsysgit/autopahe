# AutoPahe Advanced Usage Guide

> **Complete command reference and advanced features for power users**

This comprehensive guide covers all features, configuration options, and detailed command usage for AutoPahe v3.4.0+. Learn to master search, download, streaming, record management, and advanced automation features.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Search & Discovery](#search--discovery)
3. [Download Operations](#download-operations)
4. [Streaming Features](#streaming-features)
5. [Record Management](#record-management)
6. [Collection Management](#collection-management)
7. [File Organization](#file-organization)
8. [Cache & Performance](#cache--performance)
9. [Notifications & Monitoring](#notifications--monitoring)
10. [Configuration System](#configuration-system)
11. [Advanced Workflows](#advanced-workflows)
12. [Troubleshooting](#troubleshooting)

---

<a id="quick-start"></a>

## 🚀 Quick Start

### First-Time Setup (Required)

Before using AutoPahe for the first time, run the setup command to install browser engines:

```bash
autopahe --setup
```

This installs Playwright browser engines (~500MB) required for bypassing DDoS protection. **You only need to run this once.**

```
🔧 Running comprehensive setup...
✓ Sample config written to: ~/.config/autopahe/config.ini
Installing Chrome browser...
✅ Setup completed successfully!
```

### Basic Download Workflow
```bash
# Search for anime
autopahe -s "Attack on Titan"

# Select first result and download episode 1
autopahe -s "Attack on Titan" -i 0 -d 1

# Download multiple episodes
autopahe -s "Attack on Titan" -i 0 -md "1-5"
```

### Expected Output - Search Results
```
🔍 Searching for: Attack on Titan
[0] Attack on Titan (2013) - TV - 25 episodes - Status: Finished Airing
[1] Attack on Titan: Junior High (2015) - TV - 12 episodes - Status: Finished Airing  
[2] Attack on Titan: The Final Season (2020) - TV - 87 episodes - Status: Finished Airing
Found 3 results. Use -i <index> to select.
```

---

<a id="search--discovery"></a>

## 🔍 Search & Discovery

### Basic Search Commands

| Command | Description | Example |
|---------|-------------|---------|
| `-s TEXT` | Search anime by name | `-s "Naruto"` |
| `-i INT` | Select from search results | `-i 2` |
| `--year INT` | Filter by release year | `--year 2023` |
| `--status TEXT` | Filter by airing status | `--status "Finished Airing"` |
| `--no-fuzzy` | Disable fuzzy search | `--no-fuzzy` |
| `--fuzzy-threshold FLOAT` | Set similarity threshold | `--fuzzy-threshold 0.8` |

### Advanced Search Examples

#### Fuzzy Search with Custom Threshold
```bash
# High precision matching (very similar titles only)
autopahe -s "one piece" --fuzzy-threshold 0.9

# More flexible matching (includes related titles)
autopahe -s "one piece" --fuzzy-threshold 0.5
```

**Expected Output:**
```
🔍 Searching for: one piece (threshold: 0.9)
[0] One Piece (1999) - TV - 1000+ episodes - Status: Currently Airing
[1] One Piece Film: Strong World (2009) - Movie - 1 episodes - Status: Finished Airing
Found 2 high-precision matches.
```

#### Filtered Search
```bash
# Search for completed anime from 2020
autopahe -s "Demon Slayer" --year 2020 --status "Finished Airing"

# Search for ongoing series
autopahe -s "Jujutsu Kaisen" --status "Currently Airing"
```

**Expected Output:**
```
🔍 Searching for: Demon Slayer (Year: 2020, Status: Finished Airing)
[0] Demon Slayer: Kimetsu no Yaiba (2020) - TV - 26 episodes - Status: Finished Airing
[1] Demon Slayer: Kimetsu no Yaiba - Mugen Train (2020) - Movie - 1 episodes - Status: Finished Airing
Found 2 results matching filters.
```

#### Exact Match Search
```bash
# Disable fuzzy search for exact title matching
autopahe -s "Naruto Shippuden" --no-fuzzy
```

---

<a id="download-operations"></a>

## ⬇️ Download Operations

### Single Episode Downloads

| Command | Description | Example |
|---------|-------------|---------|
| `-d INT` | Download single episode | `-d 1` |
| `-p TEXT` | Set video quality | `-p 1080` |
| `--dub` | Prefer dubbed version | `--dub` |
| `--notify` | Enable notifications | `--notify` |

### Quality Selection Options
- `360` - Lowest quality, smallest file size
- `480` - Standard definition
- `720` - High definition (default)
- `1080` - Full HD
- `best` - Highest available quality
- `worst` - Lowest available quality

### Single Download Examples

#### Basic Download
```bash
autopahe -s "My Hero Academia" -i 0 -d 1
```

**Expected Output:**
```
🔍 Searching for: My Hero Academia
[0] My Hero Academia (2016) - TV - 138 episodes - Status: Currently Airing
✓ Selected: My Hero Academia

📥 Downloading episode 1 (720p)...
[####################] 100% Episode 1 - 245.3MB - 00:02:15
✓ Download completed: My Hero Academia S01E01.mp4
```

#### High Quality Dubbed Download
```bash
autopahe -s "My Hero Academia" -i 0 -d 1 -p 1080 --dub --notify
```

**Expected Output:**
```
🔍 Searching for: My Hero Academia
[0] My Hero Academia (2016) - TV - 138 episodes - Status: Currently Airing
✓ Selected: My Hero Academia

📥 Downloading episode 1 (1080p, Dub)...
[####################] 100% Episode 1 - 545.7MB - 00:03:42
✓ Download completed: My Hero Academia S01E01 (1080p Dub).mp4

🔔 Desktop notification sent: Download complete!
```

### Multi-Episode Downloads

| Command | Description | Example |
|---------|-------------|---------|
| `-md TEXT` | Download multiple episodes | `-md "1-5,7,10-12"` |
| `-w INT` | Parallel workers | `-w 3` |
| `--season INT` | Download entire season | `--season 1` |
| `--resume` | Resume interrupted downloads | `--resume` |

### Episode Selection Formats
```bash
# Individual episodes
-md "1,3,5,7"

# Range of episodes  
-md "1-12"

# Mixed format
-md "1-5,7,10-12"

# Entire season (12-13 episodes)
--season 1

# Multiple seasons
--season 1 --season 2
```

### Multi-Download Examples

#### Sequential Download (Recommended)
```bash
autopahe -s "One Piece" -i 0 -md "900-905"
```

**Expected Output:**
```
🔍 Searching for: One Piece
[0] One Piece (1999) - TV - 1000+ episodes - Status: Currently Airing
✓ Selected: One Piece

📥 Downloading episodes 900-905 (sequential)...
[####################] 100% Episode 900 - 248.1MB - 00:02:18
[####################] 100% Episode 901 - 251.4MB - 00:02:22
[####################] 100% Episode 902 - 247.9MB - 00:02:16
[####################] 100% Episode 903 - 253.2MB - 00:02:25
[####################] 100% Episode 904 - 249.8MB - 00:02:19
[####################] 100% Episode 905 - 252.1MB - 00:02:21

✓ All downloads completed! (6 episodes, 1.5GB total)
```

#### Parallel Download (Use with Caution)
```bash
autopahe -s "Attack on Titan" -i 0 -md "1-6" -w 3 --notify
```

**Expected Output:**
```
🔍 Searching for: Attack on Titan
[0] Attack on Titan (2013) - TV - 25 episodes - Status: Finished Airing
✓ Selected: Attack on Titan

📥 Downloading episodes 1-6 (3 workers)...
Worker 1: [####################] 100% Episode 1 - 245.3MB - 00:02:15
Worker 2: [####################] 100% Episode 2 - 247.1MB - 00:02:18  
Worker 3: [####################] 100% Episode 3 - 244.8MB - 00:02:14
Worker 1: [####################] 100% Episode 4 - 246.2MB - 00:02:16
Worker 2: [####################] 100% Episode 5 - 248.9MB - 00:02:20
Worker 3: [####################] 100% Episode 6 - 245.7MB - 00:02:15

✓ All downloads completed! (6 episodes, 1.48GB total)
🔔 Desktop notification sent: Batch download complete!
```

#### Season Download
```bash
autopahe -s "Demon Slayer" -i 0 --season 1 -p 1080
```

**Expected Output:**
```
🔍 Searching for: Demon Slayer
[0] Demon Slayer: Kimetsu no Yaiba (2020) - TV - 26 episodes - Status: Finished Airing
✓ Selected: Demon Slayer: Kimetsu no Yaiba

📥 Downloading Season 1 (episodes 1-26)...
[####################] 100% Episode 1/26 - 545.7MB - 00:03:42
[####################] 100% Episode 2/26 - 542.3MB - 00:03:38
...
[####################] 100% Episode 26/26 - 548.1MB - 00:03:45

✓ Season 1 complete! (26 episodes, 14.2GB total)
```

### Resume Interrupted Downloads

#### Check Resume Status
```bash
autopahe --resume-stats
```

**Expected Output:**
```
📊 Download Resume Statistics
============================
Incomplete downloads: 2
- One Piece Episode 906: 75% complete (186MB/248MB)
- Attack on Titan Episode 7: 30% complete (73MB/245MB)

Total resumeable data: 259MB
```

#### Resume Downloads
```bash
autopahe --resume
```

**Expected Output:**
```
🔄 Resuming interrupted downloads...
✓ Resumed One Piece Episode 906: [####################] 100% - 00:00:45
✓ Resumed Attack on Titan Episode 7: [####################] 100% - 00:01:30

🎉 All downloads resumed and completed!
```

---

<a id="streaming-features"></a>

## 📺 Streaming Features

### Streaming Commands

| Command | Description | Example |
|---------|-------------|---------|
| `-st TEXT` | Stream episode(s) | `-st "1-3"` |
| `--player TEXT` | Choose media player | `--player vlc` |
| `-p TEXT` | Set streaming quality | `-p 720` |

### Supported Players
- `mpv` - Lightweight, feature-rich
- `vlc` - Cross-platform media player
- `mplayer` - Classic media player
- `default` - Auto-detect best available

### Streaming Examples

#### Single Episode Stream
```bash
autopahe -s "Jujutsu Kaisen" -i 0 -st 1
```

**Expected Output:**
```
🔍 Searching for: Jujutsu Kaisen
[0] Jujutsu Kaisen (2020) - TV - 24 episodes - Status: Finished Airing
✓ Selected: Jujutsu Kaisen

📺 Streaming episode 1 (720p)...
🔗 Stream URL: https://kwik.si/e/abc123def456
🎬 Launching default player...

✓ Streaming started. Player will open automatically.
```

#### Multiple Episodes Stream
```bash
autopahe -s "Attack on Titan" -i 0 -st "1-3" --player mpv
```

**Expected Output:**
```
🔍 Searching for: Attack on Titan
[0] Attack on Titan (2013) - TV - 25 episodes - Status: Finished Airing
✓ Selected: Attack on Titan

📺 Streaming episodes 1-3 with MPV...
🔗 Episode 1 URL: https://kwik.si/e/abc123def456
🎬 MPV launched for episode 1

✓ Episode 1 complete. Starting episode 2...
🔗 Episode 2 URL: https://kwik.si/e/def456ghi789
🎬 MPV launched for episode 2

✓ Streaming session complete! (3 episodes)
```

#### High Quality Stream
```bash
autopahe -s "Demon Slayer" -i 0 -st 1 -p 1080 --player vlc
```

**Expected Output:**
```
🔍 Searching for: Demon Slayer
[0] Demon Slayer: Kimetsu no Yaiba (2020) - TV - 26 episodes - Status: Finished Airing
✓ Selected: Demon Slayer: Kimetsu no Yaiba

📺 Streaming episode 1 (1080p) with VLC...
🔗 Stream URL: https://kwik.si/e/xyz789uvw012
🎬 VLC launched for 1080p stream

✓ High-quality streaming started.
```

---

<a id="record-management"></a>

## 📊 Record Management

### Basic Record Operations

| Command | Description | Example |
|---------|-------------|---------|
| `-R view` | View all records | `-R view` |
| `-R search TEXT` | Search records | `-R search "naruto"` |
| `-R delete ID/TITLE` | Delete record | `-R delete 3` |

### Record Management Examples

#### View All Records
```bash
autopahe -R view
```

**Expected Output:**
```json
{
    "1": {
        "title": "Attack on Titan",
        "keyword": "aot",
        "Main Page": "https://animepahe.com/anime/attack-on-titan",
        "type": "TV",
        "cover_photo": "https://i.animepahe.ru/posters/aot.jpg",
        "rating": 9.0,
        "status": "Completed",
        "current_episode": 87,
        "max_episode": 87,
        "year_aired": 2013,
        "about": "Humanity fights for survival against giant humanoid Titans"
    },
    "2": {
        "title": "Demon Slayer",
        "keyword": "demon",
        "Main Page": "https://animepahe.com/anime/demon-slayer",
        "type": "TV", 
        "cover_photo": "https://i.animepahe.ru/posters/demon.jpg",
        "rating": 8.5,
        "status": "Watching Episode 15",
        "current_episode": 15,
        "max_episode": 26,
        "year_aired": 2020,
        "about": "A young boy becomes a demon slayer to save his sister"
    }
}
```

#### Search Records
```bash
autopahe -R search "demon"
```

**Expected Output:**
```json
{
    "2": {
        "title": "Demon Slayer",
        "keyword": "demon",
        "Main Page": "https://animepahe.com/anime/demon-slayer",
        "type": "TV",
        "cover_photo": "https://i.animepahe.ru/posters/demon.jpg",
        "rating": 8.5,
        "status": "Watching Episode 15",
        "current_episode": 15,
        "max_episode": 26,
        "year_aired": 2020,
        "about": "A young boy becomes a demon slayer to save his sister"
    }
}
```

### Advanced Record Operations

| Command | Description | Example |
|---------|-------------|---------|
| `-R progress ID EP` | Update episode progress | `-R progress 2 20` |
| `-R rate ID SCORE` | Rate anime (0-10) | `-R rate 2 9.5` |
| `-R rename ID "TITLE"` | Rename anime | `-R rename 2 "Demon Slayer S1"` |
| `-R set-keyword ID KEY` | Set custom keyword | `-R set-keyword 2 "kimetsu"` |
| `-R list-status STATUS` | Filter by status | `-R list-status "watching"` |

#### Update Progress and Rating
```bash
autopahe -R progress 2 20
autopahe -R rate 2 9.5
```

**Expected Output:**
```
✓ Updated progress: Demon Slayer -> 20
✓ Rated Demon Slayer -> 9.5
```

#### Rename and Set Keyword
```bash
autopahe -R rename 2 "Demon Slayer: Kimetsu no Yaiba"
autopahe -R set-keyword 2 "kimetsu"
```

**Expected Output:**
```
✓ Renamed.
✓ Keyword updated.
```

#### Filter by Status
```bash
autopahe -R list-status "watching"
```

**Expected Output:**
```json
{
    "2": {
        "title": "Demon Slayer: Kimetsu no Yaiba",
        "keyword": "kimetsu",
        "Main Page": "https://animepahe.com/anime/demon-slayer",
        "type": "TV",
        "cover_photo": "https://i.animepahe.ru/posters/demon.jpg",
        "rating": 9.5,
        "status": "Watching Episode 20",
        "current_episode": 20,
        "max_episode": 26,
        "year_aired": 2020,
        "about": "A young boy becomes a demon slayer to save his sister"
    }
}
```

### Import/Export Records

| Command | Description | Example |
|---------|-------------|---------|
| `-R export FILE FORMAT` | Export records | `-R export backup.json json` |
| `-R import FILE` | Import records | `-R import backup.json` |

#### Export to JSON
```bash
autopahe -R export my_anime_backup.json json
```

**Expected Output:**
```
✓ Exported to my_anime_backup.json
```

#### Export to CSV
```bash
autopahe -R export my_anime_records.csv csv
```

**Expected Output:**
```
✓ Exported to my_anime_records.csv
```

#### Import from Backup
```bash
autopahe -R import my_anime_backup.json
```

**Expected Output:**
```
✓ Imported records.
```

---

<a id="collection-management"></a>

## 🗂️ Collection Management

### Collection Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--collection stats` | Show collection statistics | `--collection stats` |
| `--collection view` | View collection overview | `--collection view` |
| `--collection show TITLE` | Show anime details | `--collection show "Naruto"` |
| `--collection episodes TITLE` | List episodes | `--collection episodes "Naruto"` |
| `--collection search QUERY` | Search collection | `--collection search "shonen"` |
| `--collection organize` | Organize collection | `--collection organize` |
| `--collection duplicates` | Find duplicates | `--collection duplicates` |
| `--collection export PATH` | Export collection | `--collection export backup.json` |
| `--collection import PATH` | Import collection | `--collection import backup.json` |

### Collection Examples

#### Collection Statistics
```bash
autopahe --collection stats
```

**Expected Output:**
```
📊 Collection Statistics
=========================
Total anime: 45
Total episodes: 1,247
Total size: 285.3 GB

By Status:
- Watching: 12 anime (267 episodes)
- Completed: 28 anime (892 episodes)  
- On Hold: 3 anime (58 episodes)
- Dropped: 2 anime (30 episodes)

By Type:
- TV Series: 38 anime
- Movies: 5 anime
- OVAs: 2 anime

By Year:
- 2020-2024: 32 anime
- 2015-2019: 10 anime
- Before 2015: 3 anime

Average Rating: 7.8/10
Most Watched Genre: Action
```

#### View Collection Overview
```bash
autopahe --collection view
```

**Expected Output:**
```
🎬 Anime Collection Overview
=============================

Currently Watching (12):
• Attack on Titan - S04E87/87 (9.0/10) ⭐
• Demon Slayer - S01E20/26 (9.5/10) ⭐
• Jujutsu Kaisen - S02E15/24 (8.7/10) ⭐
• One Piece - E1005/1000+ (8.9/10) ⭐
...

Completed (28):
• Naruto - 220/220 episodes (8.5/10) ⭐
• Death Note - 37/37 episodes (9.2/10) ⭐
• Fullmetal Alchemist - 64/64 episodes (9.0/10) ⭐
...

On Hold (3):
• My Hero Academia - S05E88/138 (8.2/10)
• Black Clover - E170/170 (8.0/10)
...

Recently Added:
• Chainsaw Man (2 days ago)
• Spy x Family (1 week ago)
```

#### Show Anime Details
```bash
autopahe --collection show "Demon Slayer"
```

**Expected Output:**
```
🎭 Demon Slayer: Kimetsu no Yaiba
==================================

📊 Basic Info:
• Type: TV Series
• Episodes: 26 (currently on 20)
• Year: 2020
• Rating: 9.5/10 ⭐
• Status: Watching Episode 20

📝 Synopsis:
A young boy becomes a demon slayer to save his sister and avenge his family. Set in Taisho-era Japan, Tanjiro Kamado's peaceful life is shattered when a demon slaughters his family...

🎬 Episodes:
• S01E01 - Cruelty (786.5MB) ✅ Watched
• S01E02 - Trainer Sakonji Urokodaki (745.2MB) ✅ Watched
...
• S01E20 - Pretend Family (812.3MB) ✅ Watched
• S01E21 - Against Fate (0MB) ⏳ Not Downloaded
...
• S01E26 - New Mission (0MB) ⏳ Not Downloaded

📈 Progress: 20/26 episodes (77% complete)
📅 Started: 2024-01-15 | Last Watched: 2024-11-28
```

#### List Episodes
```bash
autopahe --collection episodes "Attack on Titan"
```

**Expected Output:**
```
📺 Attack on Titan - All Episodes
==================================

Season 1 (13 episodes):
• S01E01 - To You, in 2000 Years: The Fall of Shiganshina (1) ✅
• S01E02 - That Day: The Fall of Shiganshina (2) ✅
• S01E03 - Dispersing Light: The Battle of Trost District (3) ✅
...
• S01E13 - Attack Titan (13) ✅

Season 2 (12 episodes):
• S02E01 - Beast Titan (14) ✅
• S02E02 - I'm Home (15) ✅
...
• S02E12 - Scream (25) ✅

Season 3 (22 episodes):
• S03E01 - Dust Storms (26) ✅
...
• S03E22 - The Other Side of the Wall (47) ✅

Season 4 (16 episodes):
• S04E01 - The Other Side of the Sea (48) ✅
...
• S04E16 - Below (87) ✅

📊 Total: 87 episodes | ✅ 87 watched | 100% complete
```

#### Search Collection
```bash
autopahe --collection search "shonen action"
```

**Expected Output:**
```
🔍 Collection Search: "shonen action"
=====================================

Found 8 matching anime:

1. Naruto (2002) - TV - 220 episodes - 8.5/10 ⭐
   Genre: Action, Adventure, Martial Arts
   Status: Completed

2. One Piece (1999) - TV - 1000+ episodes - 8.9/10 ⭐
   Genre: Action, Adventure, Comedy
   Status: Watching (E1005)

3. Attack on Titan (2013) - TV - 87 episodes - 9.0/10 ⭐
   Genre: Action, Dark Fantasy, Military
   Status: Completed

4. My Hero Academia (2016) - TV - 138 episodes - 8.2/10 ⭐
   Genre: Action, School, Superhero
   Status: On Hold (E88)

5. Jujutsu Kaisen (2020) - TV - 24 episodes - 8.7/10 ⭐
   Genre: Action, School, Supernatural
   Status: Watching (E15)

6. Black Clover (2017) - TV - 170 episodes - 8.0/10 ⭐
   Genre: Action, Magic, Fantasy
   Status: Completed

7. Demon Slayer (2020) - TV - 26 episodes - 9.5/10 ⭐
   Genre: Action, Historical, Supernatural
   Status: Watching (E20)

8. Chainsaw Man (2022) - TV - 12 episodes - 8.4/10 ⭐
   Genre: Action, Dark Fantasy, Horror
   Status: Completed
```

#### Organize Collection
```bash
autopahe --collection organize
```

**Expected Output:**
```
🗂️ Organizing Collection...
============================

Scanning download directories...
Found 1,247 anime files across 45 series

Organizing files:
• Moving files to proper folders...
• Renaming files with consistent format...
• Updating collection database...

✅ Organization complete!
• 1,247 files organized
• 45 folders created/updated
• 0 duplicate files found
• 285.3 GB total space used

Collection structure:
~/Anime/
├── Attack on Titan/
│   ├── Season 01/
│   ├── Season 02/
│   ├── Season 03/
│   └── Season 04/
├── Demon Slayer/
│   └── Season 01/
├── One Piece/
│   ├── East Blue Saga/
│   ├── Alabasta Saga/
│   └── ...
└── ...
```

#### Find Duplicates
```bash
autopahe --collection duplicates
```

**Expected Output:**
```
🔍 Duplicate Detection
======================

Scanning for duplicate anime files...
Found 3 potential duplicates:

1. Demon Slayer S01E01
   • ~/Downloads/Demon.Slayer.E01.mp4 (745.2MB)
   • ~/Anime/Demon Slayer/Season 01/Demon Slayer S01E01.mp4 (745.2MB)
   ⚠️ Same size, different locations

2. Attack on Titan S01E01  
   • ~/Downloads/aot_ep1.mp4 (678.9MB)
   • ~/Anime/Attack on Titan/Season 01/Attack on Titan S01E01.mp4 (678.9MB)
   ⚠️ Same content, different naming

3. Naruto Episode 1
   • ~/Old Anime/Naruto 1.avi (234.5MB)
   • ~/Anime/Naruto/Season 01/Naruto S01E01.mp4 (445.8MB)
   ⚠️ Different quality/format

💡 Recommendations:
• Remove downloads folder copies after verification
• Consolidate to organized collection structure
• Keep highest quality versions only

Total space that could be freed: 1.6GB
```

---

<a id="file-organization"></a>

## 📁 File Organization

### Sorting Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--sort MODE` | Sort files (all/rename/organize) | `--sort all` |
| `--sort-path PATH` | Custom sort directory | `--sort-path ~/Videos` |
| `--sort-dry-run` | Preview changes | `--sort all --sort-dry-run` |

### Sorting Modes
- `rename` - Rename files to standard format
- `organize` - Move files to organized folder structure  
- `all` - Full sorting (rename + organize)

### Sorting Examples

#### Dry Run Preview
```bash
autopahe --sort all --sort-dry-run
```

**Expected Output:**
```
🔍 Sort Preview - No Changes Will Be Made
==========================================

Files to rename (12):
• aot_ep1.mp4 → Attack on Titan S01E01.mp4
• demon_slayer_01.mp4 → Demon Slayer S01E01.mp4
• naruto_ep_001.avi → Naruto S01E01.mp4
...

Files to organize (12):
• Attack on Titan S01E01.mp4 → ~/Anime/Attack on Titan/Season 01/
• Demon Slayer S01E01.mp4 → ~/Anime/Demon Slayer/Season 01/
• Naruto S01E01.mp4 → ~/Anime/Naruto/Season 01/
...

Folder structure to create:
~/Anime/
├── Attack on Titan/
│   └── Season 01/
├── Demon Slayer/
│   └── Season 01/
└── Naruto/
    └── Season 01/

⚠️ This will move and rename 12 files. Use without --sort-dry-run to apply.
```

#### Rename Files Only
```bash
autopahe --sort rename
```

**Expected Output:**
```
🔄 Renaming Files...
====================

Renaming 12 files to standard format:
✓ aot_ep1.mp4 → Attack on Titan S01E01.mp4
✓ aot_ep2.mp4 → Attack on Titan S01E02.mp4
✓ demon_slayer_01.mp4 → Demon Slayer S01E01.mp4
✓ demon_slayer_02.mp4 → Demon Slayer S01E02.mp4
...
✓ naruto_ep_001.avi → Naruto S01E01.mp4

✅ Rename complete! 12 files renamed.
```

#### Organize Files Only
```bash
autopahe --sort organize
```

**Expected Output:**
```
📁 Organizing Files...
======================

Creating folder structure:
✓ ~/Anime/Attack on Titan/Season 01/
✓ ~/Anime/Attack on Titan/Season 02/
✓ ~/Anime/Demon Slayer/Season 01/
✓ ~/Anime/Naruto/Season 01/

Moving 12 files to organized folders:
✓ Attack on Titan S01E01.mp4 → ~/Anime/Attack on Titan/Season 01/
✓ Attack on Titan S01E02.mp4 → ~/Anime/Attack on Titan/Season 01/
✓ Demon Slayer S01E01.mp4 → ~/Anime/Demon Slayer/Season 01/
✓ Demon Slayer S01E02.mp4 → ~/Anime/Demon Slayer/Season 01/
✓ Naruto S01E01.mp4 → ~/Anime/Naruto/Season 01/
...

✅ Organization complete! 12 files moved into 4 folders.
```

#### Full Sorting (Rename + Organize)
```bash
autopahe --sort all --sort-path ~/Videos/Anime
```

**Expected Output:**
```
🗂️ Full Sorting Operation
==========================

Target directory: ~/Videos/Anime

Step 1: Renaming files...
✓ aot_ep1.mp4 → Attack on Titan S01E01.mp4
✓ demon_slayer_01.mp4 → Demon Slayer S01E01.mp4
✓ naruto_ep_001.avi → Naruto S01E01.mp4
...
✅ 12 files renamed

Step 2: Creating folder structure...
✓ ~/Videos/Anime/Attack on Titan/Season 01/
✓ ~/Videos/Anime/Attack on Titan/Season 02/
✓ ~/Videos/Anime/Demon Slayer/Season 01/
✓ ~/Videos/Anime/Naruto/Season 01/
✅ 4 folders created

Step 3: Moving files to folders...
✓ Attack on Titan S01E01.mp4 → ~/Videos/Anime/Attack on Titan/Season 01/
✓ Attack on Titan S01E02.mp4 → ~/Videos/Anime/Attack on Titan/Season 01/
✓ Demon Slayer S01E01.mp4 → ~/Videos/Anime/Demon Slayer/Season 01/
✓ Demon Slayer S01E02.mp4 → ~/Videos/Anime/Demon Slayer/Season 01/
✓ Naruto S01E01.mp4 → ~/Videos/Anime/Naruto/Season 01/
...
✅ 12 files organized

🎉 Full sorting complete! Collection organized at ~/Videos/Anime/
```

---

<a id="cache--performance"></a>

## 💾 Cache & Performance

### Cache Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--cache clear` | Clear all cache | `--cache clear` |
| `--cache stats` | Show cache statistics | `--cache stats` |

### Cache Examples

#### View Cache Statistics
```bash
autopahe --cache stats
```

**Expected Output:**
```
📊 Cache Statistics
===================

API Response Cache:
• Total entries: 156
• Cache size: 2.4 MB
• Hit rate: 73.2% (114 hits / 156 requests)
• Oldest entry: 5 hours 42 minutes old
• Newest entry: 2 minutes old

Cookie Cache:
• Sessions stored: 3
• Cookie size: 45.2 KB
• Valid sessions: 2
• Expired sessions: 1

Browser Cache:
• Cache location: ~/.cache/autopahe/
• Total size: 124.7 MB
• Temp files: 0
• Cleanup needed: No

Performance Benefits:
• 156 API calls avoided (73.2% hit rate)
• ~45 seconds response time saved
• Reduced DDoS-Guard challenges by 68%

⚡ Cache is working efficiently! Next cleanup in 2 hours 18 minutes.
```

#### Clear Cache
```bash
autopahe --cache clear
```

**Expected Output:**
```
🧹 Clearing Cache...
===================

Clearing API response cache...
✓ Removed 156 cache entries (2.4 MB)

Clearing cookie cache...
✓ Removed 3 session files (45.2 KB)

Clearing browser cache...
✓ Removed 124.7 MB of temporary data

Clearing log files...
✓ Removed autopahe.log (1.2 MB)

🎉 Cache cleared successfully!
• Total freed: 127.4 MB
• All sessions reset
• Fresh start on next run
```

### Performance Tuning

#### Optimize Download Speed
```bash
# Sequential downloads (most stable)
autopahe -s "Anime" -i 0 -md "1-10" -w 1

# Parallel downloads (faster but risky)
autopahe -s "Anime" -i 0 -md "1-10" -w 2

# High quality with retry limit
autopahe -s "Anime" -i 0 -md "1-5" -p 1080 --max-retries 5
```

#### Reduce Memory Usage
```bash
# Lower quality for large batches
autopahe -s "Anime" -i 0 -md "1-50" -p 480

# Clear cache periodically
autopahe --cache clear

# Use verbose logging to monitor resources
autopahe -s "Anime" -i 0 -md "1-10" --verbose
```

---

<a id="notifications--monitoring"></a>

## 🔔 Notifications & Monitoring

### Notification Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--notify` | Enable notifications | `--notify` |
| `--summary PERIOD` | Show statistics | `--summary "this week"` |
| `-dt PERIOD` | Execution data | `-dt "today"` |

### Notification Examples

#### Download with Notifications
```bash
autopahe -s "Demon Slayer" -i 0 -md "1-3" --notify
```

**Expected Output:**
```
🔍 Searching for: Demon Slayer
[0] Demon Slayer: Kimetsu no Yaiba (2020) - TV - 26 episodes - Status: Finished Airing
✓ Selected: Demon Slayer

📥 Downloading episodes 1-3 with notifications...
[####################] 100% Episode 1 - 545.7MB - 00:03:42
🔔 Download complete: Demon Slayer S01E01

[####################] 100% Episode 2 - 542.3MB - 00:03:38  
🔔 Download complete: Demon Slayer S01E02

[####################] 100% Episode 3 - 548.1MB - 00:03:45
🔔 Download complete: Demon Slayer S01E03

🎉 Batch download complete! 🎉
🔔 All 3 episodes downloaded successfully
```

### Statistics Examples

#### Today's Activity
```bash
autopahe -dt "today"
```

**Expected Output:**
```
📊 Today's Activity - 2024-11-29
=================================

Downloads:
• Episodes downloaded: 8
• Total size: 3.2 GB
• Average quality: 720p
• Success rate: 100% (8/8)

Anime Activity:
• Demon Slayer: 3 episodes (E1-3)
• Attack on Titan: 5 episodes (E84-88)

Performance:
• Total time: 28 minutes 45 seconds
• Average speed: 1.8 MB/s
• Cache hits: 12/15 (80%)

Search Activity:
• Searches performed: 3
• Results found: 12
• Fuzzy matches: 2

⏰ Most active: 2:00 PM - 4:00 PM
🎯 Favorite genre: Action
```

#### Weekly Summary
```bash
autopahe --summary "this week"
```

**Expected Output:**
```
📈 Weekly Summary - Nov 23 to Nov 29, 2024
==========================================

Download Statistics:
• Total episodes: 47
• Total size: 18.7 GB
• Average quality: 720p
• Success rate: 96.8% (47/48)

Top Downloads:
1. One Piece - 15 episodes (4.8 GB)
2. Attack on Titan - 12 episodes (3.2 GB) 
3. Demon Slayer - 8 episodes (2.9 GB)
4. Jujutsu Kaisen - 7 episodes (2.4 GB)
5. My Hero Academia - 5 episodes (1.4 GB)

Daily Breakdown:
• Mon: 6 episodes (2.1 GB)
• Tue: 8 episodes (3.2 GB)
• Wed: 12 episodes (4.8 GB)
• Thu: 7 episodes (2.7 GB)
• Fri: 9 episodes (3.4 GB)
• Sat: 5 episodes (1.5 GB)
• Sun: 0 episodes (0 GB)

Performance Metrics:
• Average download speed: 2.1 MB/s
• Cache efficiency: 74.3%
• Failed downloads: 1 (retry successful)
• Total time: 2 hours 34 minutes

Collection Growth:
• New anime added: 3
• Episodes watched: 23
• Anime completed: 1

🏆 Most productive day: Wednesday (12 episodes)
📈 Trend: +23% from last week
```

#### Custom Date Range
```bash
autopahe --summary "from 2024-11-01 to 2024-11-30"
```

**Expected Output:**
```
📊 Monthly Summary - November 2024
===================================

Downloads: 156 episodes (52.3 GB)
Anime: 18 different series
Success Rate: 97.4% (156/160)

Top Anime:
1. One Piece - 45 episodes
2. Attack on Titan Final Season - 28 episodes  
3. Demon Slayer Entertainment District - 22 episodes
4. Jujutsu Kaisen S2 - 18 episodes
5. Chainsaw Man - 12 episodes

Quality Distribution:
• 1080p: 23 episodes (14.7%)
• 720p: 98 episodes (62.8%) 
• 480p: 35 episodes (22.4%)

Performance:
• Total download time: 8 hours 42 minutes
• Average speed: 1.7 MB/s
• Cache hits: 234/312 (75.0%)

Collection Status:
• Started: 5 new anime
• Completed: 3 anime
• Currently watching: 8 anime
• On hold: 2 anime

🎯 Monthly goal achieved: 150+ episodes
📈 Growth: +18 anime in collection
```

---

<a id="configuration-system"></a>

## ⚙️ Configuration System

### Configuration Commands

| Command | Description | Example |
|---------|-------------|---------|
| `--write-config [PATH]` | Create sample config | `--write-config` |
| `--config PATH` | Use custom config | `--config /path/to/config.ini` |

### Creating Configuration

#### Generate Default Config
```bash
autopahe --write-config
```

**Expected Output:**
```
📝 Creating configuration file...
✓ Configuration written to: ~/.config/autopahe/config.ini

🎯 Configuration created! Edit this file to customize settings.
```

#### Custom Config Location
```bash
autopahe --write-config ~/my-autopahe-config.ini
```

**Expected Output:**
```
📝 Creating configuration file...
✓ Configuration written to: ~/my-autopahe-config.ini

🎯 Custom configuration created! Use --config ~/my-autopahe-config.ini to load it.
```

### Configuration File Structure

#### Complete Config Example
```ini
[defaults]
# Browser choice: firefox, chrome, chromium
browser = firefox

# Video quality: 360, 480, 720, 1080, best, worst
resolution = 720

# Parallel download workers (1 = sequential, use >1 with caution)
workers = 1

# Custom download directory (optional)
download_dir = /home/user/Videos/Anime

# Enable desktop notifications
notifications = true

# Auto-sort downloaded files
sort_on_complete = true
sort_mode = all
sort_path = /home/user/Videos/Anime

# Logging level: DEBUG, INFO, WARNING, ERROR
log_level = INFO

# Maximum retry attempts for failed downloads
max_retries = 3

# Fuzzy search threshold (0.0-1.0)
fuzzy_threshold = 0.6

# Prefer English dubbed versions
prefer_dub = false

# Media player for streaming
media_player = mpv

[cache]
# Cache duration in hours
api_cache_duration = 6
cookie_cache_duration = 24

# Enable performance monitoring
enable_stats = true

[collection]
# Auto-update collection on download
auto_update_collection = true

# Collection database path
database_path = ~/.config/autopahe/collection.json

[advanced]
# Enable verbose logging by default
verbose = false

# User agent string
user_agent = AutoPahe/3.3.2

# Request timeout in seconds
timeout = 30

# Enable debug mode
debug = false
```

### Loading Configuration

Config files are loaded in this priority order:
1. `--config /path/to/config.ini` (explicit command line)
2. `~/.config/autopahe/config.ini` (user config)
3. `~/.autopahe.ini` (home directory)
4. `./autopahe.ini` (current directory)

#### Using Custom Config
```bash
autopahe --config ~/my-autopahe-config.ini -s "Anime" -i 0 -d 1
```

#### Environment Variables
```bash
# Set custom config location
export AUTOPAHE_CONFIG=~/work/autopahe.ini

# Set custom download directory  
export AUTOPAHE_DOWNLOAD_DIR=~/Downloads/Anime

# Set custom cache directory
export AUTOPAHE_CACHE_DIR=~/cache/autopahe

# Use with environment variables
autopahe -s "Anime" -i 0 -d 1
```

---

<a id="advanced-workflows"></a>

## 🔄 Advanced Workflows

### Complete Anime Management Workflow

#### Step 1: Search and Select
```bash
# Search with filters
autopahe -s "Demon Slayer" --year 2020 --status "Finished Airing"
```

**Expected Output:**
```
🔍 Searching for: Demon Slayer (Year: 2020, Status: Finished Airing)
[0] Demon Slayer: Kimetsu no Yaiba (2020) - TV - 26 episodes - Status: Finished Airing
✓ Found 1 result matching filters.
```

#### Step 2: Download with Notifications
```bash
# Download first season with notifications
autopahe -s "Demon Slayer" -i 0 --season 1 -p 1080 --notify
```

**Expected Output:**
```
📥 Downloading Season 1 (episodes 1-26) with notifications...
[####################] 100% Episode 1/26 - 545.7MB - 00:03:42
🔔 Download complete: Demon Slayer S01E01
...
[####################] 100% Episode 26/26 - 548.1MB - 00:03:45
🔔 Download complete: Demon Slayer S01E26

🎉 Season 1 complete! (26 episodes, 14.2GB total)
🔔 Batch download complete!
```

#### Step 3: Add to Collection
```bash
# Add to collection and set watch status
autopahe -s "Demon Slayer" -i 0 --watch-status "watching" --watch-progress 5
```

**Expected Output:**
```
✓ Added to collection: Demon Slayer
✓ Watch status updated: watching
✓ Progress updated: 5 episodes watched
```

#### Step 4: Organize Files
```bash
# Organize downloaded files
autopahe --sort all --sort-path ~/Anime
```

**Expected Output:**
```
🗂️ Full Sorting Operation
✅ 26 files renamed and organized at ~/Anime/Demon Slayer/Season 01/
```

#### Step 5: Update Progress
```bash
# Update watching progress
autopahe -R progress "Demon Slayer" 10
autopahe -R rate "Demon Slayer" 9
```

**Expected Output:**
```
✓ Updated progress: Demon Slayer -> 10
✓ Rated Demon Slayer -> 9.0
```

### Batch Operations Workflow

#### Multiple Anime Download
```bash
# Download multiple anime in sequence
autopahe -s "Attack on Titan" -i 0 --season 1 --notify
autopahe -s "Demon Slayer" -i 0 --season 1 --notify  
autopahe -s "Jujutsu Kaisen" -i 0 --season 1 --notify
```

#### Collection Management
```bash
# View collection statistics
autopahe --collection stats

# Find and organize duplicates
autopahe --collection duplicates
autopahe --collection organize

# Export collection backup
autopahe --collection export ~/anime_backup.json
```

### Streaming Workflow

#### Binge Watch Session
```bash
# Stream multiple episodes
autopahe -s "One Piece" -i 0 -st "900-905" --player mpv

# Update progress after watching
autopahe -R progress "One Piece" 905
autopahe --watch-progress 905
```

#### Quality Testing
```bash
# Test different qualities
autopahe -s "Demon Slayer" -i 0 -st 1 -p 480 --player vlc
autopahe -s "Demon Slayer" -i 0 -st 1 -p 720 --player vlc  
autopahe -s "Demon Slayer" -i 0 -st 1 -p 1080 --player vlc
```

### Maintenance Workflow

#### Weekly Cleanup
```bash
# Clear cache and check stats
autopahe --cache clear
autopahe --cache stats

# Review weekly activity
autopahe --summary "this week"

# Backup collection
autopahe --collection export ~/backups/anime_weekly_$(date +%Y%m%d).json
```

#### Monthly Organization
```bash
# Monthly statistics
autopahe --summary "this month"

# Full collection organization
autopahe --collection organize
autopahe --sort all

# Export comprehensive backup
autopahe -R export ~/backups/records_monthly_$(date +%Y%m%d).json
autopahe --collection export ~/backups/collection_monthly_$(date +%Y%m%d).json
```

---

<a id="troubleshooting"></a>

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### DDoS-Guard Protection
**Symptoms**: Captcha challenges, blocked access, slow responses

**Solutions**:
```bash
# Wait and retry with sequential downloads
autopahe -s "Anime" -i 0 -d 1 -w 1

# Clear cache and cookies
autopahe --cache clear

# Try different browser
autopahe -s "Anime" -i 0 -d 1 -b chrome

# Use verbose mode for debugging
autopahe -s "Anime" -i 0 -d 1 --verbose
```

#### Download Failures
**Symptoms**: Episodes fail to download, incomplete files

**Solutions**:
```bash
# Check resume status
autopahe --resume-stats

# Resume interrupted downloads
autopahe --resume

# Increase retry limit
autopahe -s "Anime" -i 0 -d 1 --max-retries 5

# Use lower quality for stability
autopahe -s "Anime" -i 0 -d 1 -p 480
```

#### Performance Issues
**Symptoms**: Slow downloads, high memory usage

**Solutions**:
```bash
# Optimize for performance
autopahe -s "Anime" -i 0 -md "1-10" -w 1 -p 720

# Monitor with verbose logging
autopahe -s "Anime" -i 0 -md "1-5" --verbose

# Clear cache regularly
autopahe --cache clear

# Check system resources
autopahe --cache stats
```

#### Streaming Issues
**Symptoms**: Stream won't play, player errors

**Solutions**:
```bash
# Try different player
autopahe -s "Anime" -i 0 -st 1 --player vlc
autopahe -s "Anime" -i 0 -st 1 --player mpv

# Test different quality
autopahe -s "Anime" -i 0 -st 1 -p 480

# Check internet connection
autopahe -s "Anime" -i 0 -l 1  # Get link to test manually
```

### Debug Mode

#### Enable Full Debugging
```bash
# Enable verbose logging
autopahe -s "Anime" -i 0 -d 1 --verbose

# Monitor log file in real-time
tail -f autopahe.log

# Check system status
autopahe --cache stats
autopahe --resume-stats
```

#### Reset and Recovery
```bash
# Complete reset
autopahe --cache clear
rm ~/.config/autopahe/config.ini
autopahe --write-config

# Test with basic command
autopahe -s "test" -i 0 -d 1 -p 480
```

### Platform-Specific Issues

#### Windows Issues
```bash
# Windows-specific settings
autopahe -s "Anime" -i 0 -d 1 -b chrome --workers 1

# Check file permissions
autopahe --sort all --sort-dry-run
```

#### Linux Issues
```bash
# Install missing dependencies
sudo apt install libnotify-bin  # For notifications
sudo apt install mpv  # For streaming

# Linux-specific paths
autopahe --config ~/.config/autopahe/linux-config.ini
```

#### macOS Issues
```bash
# macOS specific settings
autopahe -s "Anime" -i 0 -d 1 -b chrome

# Homebrew dependencies
brew install mpv
brew install vlc
```

---

<a id="getting-help"></a>

## 📞 Getting Help

### Support Resources

- **GitHub Issues**: [Report bugs and request features](https://github.com/haxsysgit/autopahe/issues)
- **Discussions**: [Community support and discussions](https://github.com/haxsysgit/autopahe/discussions)
- **Documentation**: [Main README for basic usage](README.md)
- **Version Info**: Check your version with `autopahe -v`

### Reporting Issues

When reporting issues, include:
1. AutoPahe version (`autopahe -v`)
2. Operating system
3. Command that failed
4. Error message (use `--verbose`)
5. Log file content (`autopahe.log`)

### Feature Requests

Request features via:
- GitHub Issues with "enhancement" label
- GitHub Discussions for community feedback
- Direct contributions via Pull Requests

---

<a id="pro-tips"></a>

## 🎓 Pro Tips

### Power User Techniques

1. **Batch Scripting**: Create shell scripts for common workflows
2. **Cron Jobs**: Schedule automatic downloads with cron
3. **Remote Usage**: Use via SSH for remote download management
4. **API Integration**: Combine with other tools using JSON exports
5. **Network Optimization**: Use VPNs or proxies for region restrictions

### Performance Optimization

1. **Cache Management**: Clear cache monthly for optimal performance
2. **Parallel Downloads**: Use `-w 2` for fast networks, `-w 1` for stability
3. **Quality Selection**: Use 720p for balance, 1080p for quality
4. **Storage Management**: Organize files regularly to save space
5. **Network Timing**: Download during off-peak hours for better speeds

### Automation Ideas

```bash
# Daily new episode check
#!/bin/bash
autopahe -s "Following Anime" -i 0 --notify

# Weekly organization
#!/bin/bash  
autopahe --collection organize
autopahe --sort all

# Monthly backup
#!/bin/bash
DATE=$(date +%Y%m%d)
autopahe -R export ~/backups/records_$DATE.json
autopahe --collection export ~/backups/collection_$DATE.json
```

---

**Master AutoPahe with these comprehensive features! 🚀**

*AutoPahe v3.3.4+ - Cross-platform anime automation at its finest.*
