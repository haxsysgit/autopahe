import json
import os
import csv
import tempfile
import shutil
import logging
import time
from pathlib import Path

# Cross-platform file locking support
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Import centralized configuration
from config import DATABASE_FILE, BACKUPS_DIR

cwd = os.path.dirname(os.path.abspath(__file__))
# Use central project-level json_data directory
root_dir = os.path.dirname(cwd)
json_dir = os.path.join(root_dir, "json_data")
if not os.path.exists(json_dir):
    os.makedirs(json_dir, exist_ok=True)
# DATABASE_FILE = os.path.join(json_dir, "animerecord.json")  # Removed this line


def ensure_file_exists():
    """
    Ensure the database file exists. If not, create an empty JSON file.
    """
    try:
        if not os.path.isfile(DATABASE_FILE):
            with open(DATABASE_FILE, 'w') as f:
                json.dump({}, f)
                logging.debug(f"Created new database file: {DATABASE_FILE}")
    except Exception as e:
        logging.error(f"Failed to create database file: {e}")
        raise

def load_database():
    """
    Load the database from the JSON file with proper error handling.
    """
    ensure_file_exists()
    try:
        with open(DATABASE_FILE, 'r') as f:
            # Use file locking to prevent concurrent access issues (Unix only)
            if HAS_FCNTL:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            data = json.load(f)
            if HAS_FCNTL:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Validate data structure
            if not isinstance(data, dict):
                logging.warning("Database corrupted, creating new empty database")
                return {}
            return data
    except json.JSONDecodeError as e:
        logging.error(f"Database JSON decode error: {e}")
        # Create backup of corrupted file
        backup_file = f"{DATABASE_FILE}.corrupted.{int(time.time())}"
        try:
            shutil.copy2(DATABASE_FILE, backup_file)
            logging.info(f"Corrupted database backed up to: {backup_file}")
        except Exception as backup_error:
            logging.error(f"Failed to backup corrupted database: {backup_error}")
        return {}
    except Exception as e:
        logging.error(f"Failed to load database: {e}")
        raise

def save_database(data):
    """
    Save the provided data to the JSON database file with atomic write and error handling.
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    # Create temporary file in same directory for atomic operation
    temp_file = None
    try:
        # Create backup before overwriting (if file exists) - with rotation
        if os.path.exists(DATABASE_FILE):
            _rotate_backups()
            backup_file = f"{DATABASE_FILE}.backup.{int(time.time())}"
            shutil.copy2(DATABASE_FILE, backup_file)
            logging.debug(f"Created backup: {backup_file}")
        
        temp_fd, temp_file = tempfile.mkstemp(
            prefix='.animerecord_tmp_', 
            dir=os.path.dirname(DATABASE_FILE)
        )
        
        with os.fdopen(temp_fd, 'w') as f:
            # Cross-platform file locking (Unix only, Windows will skip)
            if HAS_FCNTL:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            else:
                logging.debug("File locking not available on this platform")
            
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
            
            if HAS_FCNTL:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
        # Atomic move - this is the critical operation
        shutil.move(temp_file, DATABASE_FILE)
        logging.debug(f"Database saved successfully: {DATABASE_FILE}")
        
    except Exception as e:
        logging.error(f"Failed to save database: {e}")
        # Clean up temp file if it exists
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception:
                pass
        raise

def _rotate_backups():
    """
    Rotate backup files to prevent disk bloat - keep only last 5 backups.
    """
    try:
        backup_pattern = f"{DATABASE_FILE}.backup.*"
        backup_files = []
        
        for filename in os.listdir(os.path.dirname(DATABASE_FILE)):
            if filename.startswith(os.path.basename(DATABASE_FILE) + ".backup."):
                full_path = os.path.join(os.path.dirname(DATABASE_FILE), filename)
                backup_files.append((full_path, os.path.getmtime(full_path)))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups, keep only 5 most recent
        for backup_file, _ in backup_files[5:]:
            try:
                os.unlink(backup_file)
                logging.debug(f"Removed old backup: {backup_file}")
            except Exception as e:
                logging.warning(f"Failed to remove old backup {backup_file}: {e}")
                
    except Exception as e:
        logging.warning(f"Backup rotation failed: {e}")

def backup_database():
    """
    Create a manual backup of the current database.
    """
    try:
        if os.path.exists(DATABASE_FILE):
            timestamp = int(time.time())
            backup_file = f"{DATABASE_FILE}.manual_backup.{timestamp}"
            shutil.copy2(DATABASE_FILE, backup_file)
            logging.info(f"Manual backup created: {backup_file}")
            return backup_file
        else:
            logging.warning("Database file does not exist, cannot create backup")
            return None
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return None

def get_next_index(database):
    """
    Get the next available index for a new record with validation.
    """
    try:
        if not database or not isinstance(database, dict):
            return 1
        # Validate that all keys are numeric
        numeric_keys = []
        for key in database.keys():
            try:
                numeric_keys.append(int(key))
            except ValueError:
                logging.warning(f"Non-numeric key found in database: {key}")
        return max(numeric_keys or [0]) + 1
    except Exception as e:
        logging.error(f"Error getting next index: {e}")
        return 1

def _find_index(database, key_or_title):
    """Resolve a record identifier which may be an index (str/int) or title."""
    # Direct index
    if isinstance(key_or_title, int) or (isinstance(key_or_title, str) and key_or_title.isdigit()):
        key = str(int(key_or_title))
        if key in database:
            return key
        return None
    # By title
    t = str(key_or_title).strip().lower()
    for k, v in database.items():
        if v.get("title", "").lower() == t:
            return k
    return None

def update_entry(record, database=None):
    """
    Update an existing record in the database with validation.
    """
    try:
        if not record or len(record) < 2:
            raise ValueError("Invalid record format")
        
        if database is None:
            database = load_database()
        
        # Validate record structure
        if not isinstance(record[1], dict) or 'title' not in record[1]:
            raise ValueError("Record must contain title in dictionary format")
        
        title = record[1].get('title')
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        
        # Find the index of the existing record by matching the title
        existing_index = next((index for index, data in database.items() if data["title"] == title), None)
        
        if existing_index is None:
            print(f"No existing record found for title '{title}'. Adding as new record.")
            add_new_record(record, database)  # If no existing record, add it as a new record
            return
        
        # Extract record details
        keyword = record[0]
        anime_type = record[1].get('type')
        anipage = record[1].get('anime_page')
        max_episode = record[1].get('episodes')
        year = record[1].get('year')
        cover = record[1].get('poster')
        
        changes = []
        for k,v in database.items():
            if database[k]['title'] == title :
                changes.append(database[k]['about'])
                changes.append(database[k]['current_episode'])
        
        about = changes[0]
        current_episode = changes[1]

        if isinstance(current_episode, str):
            current_episode = 0

        if len(record) == 3:
            if type(record[2]) == int:
                current_episode = record[2] if current_episode < record[2] else current_episode
            else:
                if ',' in record[2] and len(record[2]) < 30:
                    latest_episode = max(list(int(s) for s in record[2].split(',')))
                    current_episode = latest_episode if current_episode < latest_episode else current_episode
                else:
                    about = record[2]

        elif len(record) == 4:
            about = record[2]
            current_episode_info = record[3]
            try:
                # Safe parsing of episode numbers
                episodes = [int(s.strip()) for s in str(current_episode_info).split(',') if s.strip().isdigit()]
                if not episodes:
                    logging.warning("No valid episode numbers found in record")
                    episodes = [0]
                latest_episode = max(episodes)
                current_episode = latest_episode if current_episode < latest_episode else current_episode
            except (ValueError, AttributeError) as e:
                logging.error(f"Error parsing episode info: {e}")
                current_episode = 0

        # Determine the status based on the current episode
        status = "Not Started Watching"
        try:
            if current_episode > 0:
                if current_episode < max_episode:
                    status = f"Watching Episode {current_episode}"
                else:
                    status = "Completed"
        except TypeError:
            print(f"\n{current_episode} is currently str,'>' not supported between instances of 'str' and 'int'")
            pass

        # Update the existing record with new details
        database[existing_index] = {
            "title": title,
            "Main Page": anipage,
            "type": anime_type,
            "cover_photo": cover,
            "rating": 0,
            "status": status,
            "current_episode": current_episode,
            "max_episode": max_episode,
            "year_aired": year,
            "about": about
        }
        save_database(database)  # Save the updated database
    
    except Exception as e:
        logging.error(f"Failed to update record: {e}")
        raise

def add_new_record(record, database):
    """
    Add a new record to the database with validation.
    """
    try:
        if not record or len(record) < 2:
            raise ValueError("Invalid record format")
        
        next_index = get_next_index(database)
        
        # Validate and extract record details
        keyword = str(record[0]) if record[0] else ""
        
        if not isinstance(record[1], dict):
            raise ValueError("Record data must be a dictionary")
        
        title = record[1].get('title')
        if not title or not isinstance(title, str):
            raise ValueError("Title must be a non-empty string")
        anime_type = record[1].get('type')
        max_episode = record[1].get('episodes')
        anipage = record[1].get('anime_page')
        year = record[1].get('year')
        cover = record[1].get('poster')

        about = ""
        current_episode = 0

        if len(record) == 3:
            if ',' in record[2] and all(part.isdigit() for part in record[2].split(',')):
                current_episode = int(record[2].split(',')[-1])
            else:
                about = record[2]
        elif len(record) == 4:
            about = record[2]
            current_episode_info = record[3]
            try:
                # Safe parsing of episode numbers
                episodes = [int(s.strip()) for s in str(current_episode_info).split(',') if s.strip().isdigit()]
                if not episodes:
                    logging.warning("No valid episode numbers found in record")
                    episodes = [0]
                current_episode = max(episodes)
            except (ValueError, AttributeError) as e:
                logging.error(f"Error parsing episode info: {e}")
                current_episode = 0

        status = "Not Started Watching"
        if current_episode > 0:
            if current_episode < max_episode:
                status = f"Watching Episode {current_episode}"
            else:
                status = "Completed"

        database[next_index] = {
            "title": title,
            "keyword": keyword,
            "Main Page": anipage,
            "type": anime_type,
            "cover_photo": cover,
            "rating": 0,
            "status": status,
            "current_episode": current_episode,
            "max_episode": max_episode,
            "year_aired": year,
            "about": about
        }
        save_database(database)
    
    except Exception as e:
        logging.error(f"Failed to add new record: {e}")
        raise

def process_record(record, update=False, quiet=False):
    """
    Process and add a new record to the database. If the record exists, update it if `update` is True.
    """
    database = load_database()
    
    title = record[1].get('title')
    
    # Check if the record already exists in the database by title
    existing_index = next((index for index, data in database.items() if data["title"] == title), None)
    
    if existing_index is not None:
        if update:
            if not quiet:
                print(f"\nRecord with title '{title}' already exists. Updating it.\n")
            update_entry(record, database)
        else:
            if not quiet:
                print(f"\nRecord with title '{title}' already exists. No action taken.\n")
    else:
        if not quiet:
            print(f"\nAdding new record with title '{title}'.")
        add_new_record(record, database)

def delete_record(key_or_title):
    """Delete a record by index or exact title."""
    db = load_database()
    idx = _find_index(db, key_or_title)
    if idx is None:
        print("Record not found.")
        return False
    removed = db.pop(idx)
    save_database(db)
    print(f"Deleted: {removed.get('title')}")
    return True

def update_progress(key_or_title, current_episode):
    """Update current episode progress and recalculates status."""
    db = load_database()
    idx = _find_index(db, key_or_title)
    if idx is None:
        print("Record not found.")
        return False
    try:
        ce = int(current_episode)
    except Exception:
        print("Invalid episode number")
        return False
    db[idx]["current_episode"] = ce
    max_ep = db[idx].get("max_episode") or 0
    if ce <= 0:
        db[idx]["status"] = "Not Started Watching"
    elif ce < max_ep:
        db[idx]["status"] = f"Watching Episode {ce}"
    else:
        db[idx]["status"] = "Completed"
    save_database(db)
    print(f"Updated progress: {db[idx]['title']} -> {ce}")
    return True

def rate_record(key_or_title, rating):
    """Set a rating 0-10."""
    db = load_database()
    idx = _find_index(db, key_or_title)
    if idx is None:
        print("Record not found.")
        return False
    try:
        r = float(rating)
    except Exception:
        print("Invalid rating")
        return False
    r = max(0.0, min(10.0, r))
    db[idx]["rating"] = r
    save_database(db)
    print(f"Rated {db[idx]['title']} -> {r}")
    return True

def rename_title(key_or_title, new_title):
    db = load_database()
    idx = _find_index(db, key_or_title)
    if idx is None:
        print("Record not found.")
        return False
    db[idx]["title"] = str(new_title)
    save_database(db)
    print("Renamed.")
    return True

def set_keyword(key_or_title, keyword):
    db = load_database()
    idx = _find_index(db, key_or_title)
    if idx is None:
        print("Record not found.")
        return False
    db[idx]["keyword"] = str(keyword)
    save_database(db)
    print("Keyword updated.")
    return True

def list_by_status(status):
    db = load_database()
    s = status.lower()
    out = {k: v for k, v in db.items() if s in str(v.get("status", "")).lower()}
    print(json.dumps(out, indent=4))
    return out

def export_records(path, fmt="json"):
    db = load_database()
    fmt = fmt.lower()
    if fmt == "json":
        with open(path, 'w') as f:
            json.dump(db, f, indent=4)
        print(f"Exported to {path}")
        return True
    if fmt == "csv":
        # Flatten reasonable fields
        fields = [
            "index", "title", "keyword", "type", "status", "current_episode",
            "max_episode", "year_aired", "rating", "Main Page", "cover_photo"
        ]
        with open(path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for k, v in db.items():
                row = {"index": k}
                row.update({
                    "title": v.get("title"),
                    "keyword": v.get("keyword"),
                    "type": v.get("type"),
                    "status": v.get("status"),
                    "current_episode": v.get("current_episode"),
                    "max_episode": v.get("max_episode"),
                    "year_aired": v.get("year_aired"),
                    "rating": v.get("rating"),
                    "Main Page": v.get("Main Page"),
                    "cover_photo": v.get("cover_photo"),
                })
                w.writerow(row)
        print(f"Exported to {path}")
        return True
    print("Unsupported format (use json or csv)")
    return False

def import_records(path):
    db = load_database()
    with open(path, 'r') as f:
        incoming = json.load(f)
    # Merge; if key collision, find next index
    for k, v in incoming.items():
        if k in db:
            nk = str(get_next_index(db))
            db[nk] = v
        else:
            db[k] = v
    save_database(db)
    print("Imported records.")
    return True

def search_record(query):
    """
    Search for records in the database that match the query.
    """
    database = load_database()
    
    results = {}
    
    for key, value in database.items():
        lower_query = query.lower()
        if lower_query in value["title"].lower() or lower_query in value["keyword"].lower():
            results[key] = value
    
    return results

def print_all_records():
    """
    Print all records from the database in a formatted JSON.
    """
    database = load_database()
    print(json.dumps(database, indent=4))

# Example usage
sample = [
    'kabaneri',
    {
        'id': 875,
        'title': 'Koutetsujou no Kabaneri',
        'type': 'TV',
        'episodes': 12,
        'status': 'Finished Airing',
        'season': 'Spring',
        'year': 2016,
        'score': 7.27,
        'poster': 'https://i.animepahe.ru/posters/3c01c83a35626201293b677d166226fcef7e13b00b875991907f1a54aebad626.jpg',
        'session': 'fccced41-eb03-ea7c-ceaf-13b40bad9cd3'
    },
    'The world is in the midst of the industrial revolution when horrific creatures emerge from a mysterious virus...'
]

if __name__ == '__main__':
    process_record(sample, update=True)
