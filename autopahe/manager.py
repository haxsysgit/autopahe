import json
import os

DATABASE_FILE = "./animerecord.json"

def ensure_file_exists():
    """
    Ensure the database file exists. If not, create an empty JSON file.
    """
    if not os.path.isfile(DATABASE_FILE):
        with open(DATABASE_FILE, 'w') as f:
            json.dump({}, f)

def load_database():
    """
    Load the database from the JSON file.
    """
    ensure_file_exists()  # Ensure the file exists before loading
    with open(DATABASE_FILE, 'r') as f:
        return json.load(f)

def save_database(data):
    """
    Save the provided data to the JSON database file.
    """
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=4)  # Pretty-print the JSON with an indent of 4 spaces

def get_next_index(database):
    """
    Get the next available index for a new record.
    """
    # Find the maximum index from existing keys or default to 0 if the database is empty
    return max([int(key) for key in database.keys()] or [0]) + 1

def update_entry(record, database=None):
    """
    Update an existing record in the database.
    """

    if database is None:
        database = load_database()  # Load the current database only if not passed as an argument
    

    keyword = record[0]
    title = record[1].get('title')
    
    # Find the index of the existing record by matching the keyword
    existing_index = next((index for index, data in database.items() if data["keyword"] == keyword), None)
    
    if existing_index is None:
        print(f"No existing record found for keyword '{keyword}'. Adding as new record.")
        add_new_record(record, database)  # If no existing record, add it as a new record
        return
    
    # Extract record details
    anime_type = record[1].get('type')
    max_episode = record[1].get('episodes')
    year = record[1].get('year')
    cover = record[1].get('poster')
    
    changes = []  

    for k,v in database.items():
        if database[k]['keyword'] == keyword :
            changes.append(database[k]['about'])
            # print(changes)
            changes.append(database[k]['current_episode'])
            # print(changes)     


    
    about = changes[1]
    current_episode = changes[0]
    # print(f'Current_episode : {current_episode}')


    # print(f'Current_episode : {current_episode}')
    
    
    # Handle the different possible lengths of the record input
    if len(record) == 3:
        # Check if the third item is the 'about' field or the 'current_episode' information
        if ',' in record[2] and len(record[2]) < 30:
            current_episode = int(record[2].split(',')[-1])  # Treat it as episode info
            # print(f'Current_episode : {current_episode}')

        else:
            about = record[2]  # Treat it as 'about'

    elif len(record) == 4:
        about = record[2]  # Third element is the 'about' description
        current_episode_info = record[3]
        current_episode = int(current_episode_info.split(',')[-1]) if isinstance(current_episode_info, str) and all(part.isdigit() for part in current_episode_info.split(',')) else int(current_episode_info)

    

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
        "keyword": keyword,
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

def add_new_record(record, database):
    """
    Add a new record to the database.
    """
    next_index = get_next_index(database)
    
    # Extract record details
    anime_type = record[1].get('type')
    max_episode = record[1].get('episodes')
    year = record[1].get('year')
    cover = record[1].get('poster')

    # Identify and extract the 'about' and 'current_episode' fields
    about = ""
    current_episode = 0

    # Handle the different possible lengths of the record input
    if len(record) == 3:
        # Check if the third item is the 'about' field or the 'current_episode' information
        if ',' in record[2] and all(part.isdigit() for part in record[2].split(',')):
            current_episode = int(record[2].split(',')[-1])  # Treat it as episode info
        else:
            about = record[2]  # Treat it as 'about'
    elif len(record) == 4:
        about = record[2]  # Third element is the 'about' description
        current_episode_info = record[3]
        current_episode = int(current_episode_info.split(',')[-1]) if isinstance(current_episode_info, str) and all(part.isdigit() for part in current_episode_info.split(',')) else int(current_episode_info)
    
    
    # Determine the status based on the current episode
    status = "Not Started Watching"
    if current_episode > 0:
        if current_episode < max_episode:
            status = f"Watching Episode {current_episode}"
        else:
            status = "Completed"

    # Add the new record to the database
    database[next_index] = {
        "title": record[1].get('title'),
        "keyword": record[0],
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

def process_record(record, update=False):
    """
    Process and add a new record to the database. If the record exists, update it if `update` is True.
    """
    database = load_database()  # Load the current database
    
    keyword = record[0]
    
    # Check if the record already exists in the database by keyword
    existing_index = next((index for index, data in database.items() if data["keyword"] == keyword), None)
    
    if existing_index is not None:
        # If record already exists, update it only if `update` is True
        if update:
            print(f"Record with keyword '{keyword}' already exists. Updating it.")
            update_entry(record, database)
        else:
            print(f"Record with keyword '{keyword}' already exists. No action taken.")
    else:
        print(f"Adding new record with keyword '{keyword}'.")
        add_new_record(record, database)

def search_record(query):
    """
    Search for records in the database that match the query.
    """
    database = load_database()  # Load the current database
    
    results = {}  # Initialize a dictionary to hold search results
    
    # Iterate over each record in the database
    for key, value in database.items():
        lower_query = query.lower()  # Convert query to lowercase for case-insensitive search
        
        # Check if the query is present in the 'keyword' or 'title' fields
        if lower_query in value["keyword"].lower() or lower_query in value["title"].lower():
            results[key] = value  # Add matching record to results
    
    return results  # Return the search results

def print_all_records():
    """
    Print all records from the database in a formatted JSON.
    """
    database = load_database()  # Load the current database
    print(json.dumps(database, indent=4))  # Print database with indentation for readability

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
'The world is in the midst of the industrial revolution when horrific creatures emerge from a mysterious virus, ripping through the flesh of humans to sate their never-ending appetite. The only way to kill these beings, known as "Kabane," is by destroying their steel-coated hearts. However, if bitten by one of these monsters, the victim is doomed to a fate worse than death, as the fallen rise once more to join the ranks of their fellow undead.Only the most fortified of civilizations have survived this turmoil, as is the case with the island of Hinomoto, where mankind has created a massive wall to protect themselves from the endless hordes of Kabane. The only way into these giant fortresses is via heavily-armored trains, which are serviced and built by young men such as Ikoma. Having created a deadly weapon that he believes will easily pierce through the hearts of Kabane, Ikoma eagerly awaits the day when he will be able to fight using his new invention. Little does he know, however, that his chance will come much sooner than he expected...',

]

if __name__ == '__main__':
    process_record(sample, update=True)
