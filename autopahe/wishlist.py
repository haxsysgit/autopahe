import json
import os

WISHLIST_FILE = 'Anime_Wishlist.json'


def ensure_file_exists():
    if not os.path.isfile(WISHLIST_FILE):
        with open(WISHLIST_FILE, 'w') as f:
            json.dump({}, f)



def load_wishlist():
    ensure_file_exists()
    with open(WISHLIST_FILE, 'r') as f:
        return json.load(f)



def save_wishlist(data):
    with open(WISHLIST_FILE, 'w') as f:
        json.dump(data, f, indent=4)



def add_or_update_anime(name, rating, current_episode, max_episode, date_started, best_character):
    wishlist = load_wishlist()
    
    # Find the next available index
    next_index = max([int(key) for key in wishlist.keys()] or [0]) + 1
    
    wishlist[str(next_index)] = {
        "name": name,
        "rating": rating,
        "status":False,
        "current_episode": current_episode,
        "max_episode":max_episode,
        "date_started": date_started,
        "best_character": best_character
    }
    
    save_wishlist(wishlist)
    
    print(f"'{name}' has been added/updated with index {next_index}.")

    updated_list = load_wishlist()

    for index, details in updated_list.items():

        if details["current_episode"] == 0:
            updated_list[index]["status"] = "Not Started Watching"

        elif details["current_episode"] < details["max_episode"]:
            updated_list[index]["status"] = f"Watching Episode {updated_list[index]['current_episode']}"
            
        else:
            updated_list[index]["status"] = "Completed"

    save_wishlist(updated_list)
            




def get_wishlist():
    wishlist = load_wishlist()
    entries = []
    
    for index, details in wishlist.items():
        entries.append((int(index), details['name']), details['status'])

    
    
    for index, name, status in entries:
        print(f"({index}) Name: {name}\n    Status: {status}\n")



def main():
    while True:
        print("\nAnime Wishlist Management\n")
        print("    1. Add/Update an anime")
        print("    2. View all wishlist entries")
        print("    3. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == '1':
            name = input("Enter the name of the anime: ").strip()
            rating = int(input("\nEnter the rating (1-10): "))
            current_episode = int(input("\nEnter the current episode number: "))
            max_episode = int(input("\nHow many episodes in the anime: "))
            date_started = input("\nEnter the month you started watching: ").strip()
            best_character = input("\nEnter the best character: ").strip()
            add_or_update_anime(name, rating, current_episode,max_episode, date_started, best_character)


        elif choice == '2':
            print("\nCurrent Wishlist:")
            get_wishlist()

        elif choice == '3':
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
