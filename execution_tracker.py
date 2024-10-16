# execution_tracker.py
import json
import os
import time
from datetime import datetime, timedelta

# Initialize counters and timings
cwd = os.path.dirname(os.path.abspath(__file__))
# print(os.path.expandvars(cwd))
script_run_count = 0
first_run_time = datetime.now()

if not os.path.exists("json_data"):
    os.mkdir(os.path.join(cwd, "json_data"))
    

DATA_FILE = os.path.join(cwd, "json_data/execution_data.py")


# Function to log the execution time and run count
def log_execution_time(start_time):
    """
    Logs the execution time and updates run count and total time for the current day.

    Args:
        start_time (float): The time when the script started, obtained using time.perf_counter().
    """
    global script_run_count

    finish_time = time.perf_counter()
    execution_duration_secs = round(finish_time - start_time, 2)

    # Calculate minutes and hours
    execution_duration_mins = round(execution_duration_secs / 60, 2)
    execution_duration_hours = round(execution_duration_secs / 3600, 2)

    # Load existing data or create new structure
    data = load_execution_data()
    today = datetime.now().date().isoformat()

    # Update today's data
    if today not in data:
        data[today] = {
            'run_count': 0,
            'total_time_secs': 0,
            'total_time_mins': 0,
            'total_time_hours': 0,
            'average_time_secs': 0,
            'average_time_mins': 0,
            'average_time_hours': 0,
        }

    # Update data for today
    data[today]['run_count'] += 1
    data[today]['total_time_secs'] += execution_duration_secs
    data[today]['total_time_mins'] += execution_duration_mins
    data[today]['total_time_hours'] += execution_duration_hours

    # Calculate averages
    run_count = data[today]['run_count']
    data[today]['average_time_secs'] = data[today]['total_time_secs'] / run_count
    data[today]['average_time_mins'] = data[today]['total_time_mins'] / run_count
    data[today]['average_time_hours'] = data[today]['total_time_hours'] / run_count

    # Save the updated data
    save_execution_data(data)

    script_run_count += 1

# Load execution data from a file
def load_execution_data():
    """
    Loads the execution data from a JSON file.

    Returns:
        dict: A dictionary containing execution data. If the file doesn't exist, returns an empty dictionary.
    """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return {}

# Save execution data to a file
def save_execution_data(data):
    """
    Saves the execution data to a JSON file.

    Args:
        data (dict): A dictionary containing the execution data to be saved.
    """
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Function to reset the run count at midnight
def reset_run_count():
    """
    Resets the script run count at midnight by checking if the current date has changed.
    """
    global first_run_time, script_run_count

    now = datetime.now()
    if now.date() != first_run_time.date():
        script_run_count = 0
        first_run_time = now

# Function to print execution statistics
def print_execution_stats():
    """
    Prints the execution statistics for all available data in the JSON file.
    """
    data = load_execution_data()
    for date, stats in data.items():
        print(f"Date: {date}, Runs: {stats['run_count']}, Total Time: {stats['total_time_secs']} seconds, Average Time: {stats['average_time_secs']} seconds")

# Function to get execution stats
def get_execution_stats(date_input):
    """
    Retrieves execution statistics for the specified date or date range.

    Args:
        date_input (str): A string indicating the date or date range. 
                          Accepted formats include:
                          1. "today" - for today's stats.
                          2. "yesterday" - for stats from the previous day.
                          3. "last X days" - for stats from the last X days.
                          4. "last week" - for stats from the last week.
                          5. "this week" - for stats from the current week.
                          6. "X weeks ago" - for stats from X weeks ago.
                          7. "last month" - for stats from the last month.
                          8. "X months ago" - for stats from X months ago.

    Returns:
        dict or None: A dictionary containing execution stats for the specified date(s),
                      or None if no stats are found.
    """
    # Define the date format
    date_format = '%Y-%m-%d'

    # Ensure execution_data.json exists; create it if not
    file_path = DATA_FILE
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)

    # Load execution data from JSON file
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error retrieving execution stats: {e}")
        return None

    # Get today's date
    today = datetime.now().date()

    # Handle different date inputs
    if date_input.lower() == "today":
        stats={}
        date_key = today.strftime(date_format)
        
        if date_key in data:
            stats[date_key] = data.get(date_key, None)

        return stats if stats else None

    elif date_input.lower() == "yesterday":
        stats={}
        yesterday = today - timedelta(days=1)
        date_key = yesterday.strftime(date_format)

        if date_key in data:
            stats[date_key] = data.get(date_key, None)

        return stats if stats else None

    elif "last" in date_input and "days" in date_input:
        days = int(date_input.split()[1])
        stats = {}

        for i in range(days):
            day = today - timedelta(days=i)
            date_key = day.strftime(date_format)

            if date_key in data:
                stats[date_key] = data[date_key]
        return stats if stats else None

    elif date_input.lower() == "last week":
        stats = {}
        for i in range(7):
            day = today - timedelta(days=i)
            date_key = day.strftime(date_format)

            if date_key in data:
                stats[date_key] = data[date_key]

        return stats if stats else None

    elif date_input.lower() == "this week":
        stats = {}
        start_of_week = today - timedelta(days=today.weekday())

        for i in range(7):
            day = start_of_week + timedelta(days=i)
            date_key = day.strftime(date_format)

            if date_key in data:
                stats[date_key] = data[date_key]

        return stats if stats else None

    elif "weeks ago" in date_input:
        weeks = int(date_input.split()[0])
        target_date = today - timedelta(weeks=weeks)
        date_key = target_date.strftime(date_format)

        return data.get(date_key, None)

    elif date_input.lower() == "last month":
        last_month = today.replace(day=1) - timedelta(days=1)
        month_key = last_month.strftime(date_format)

        return data.get(month_key, None)

    elif "months ago" in date_input:
        months = int(date_input.split()[0])
        target_date = today - timedelta(days=months * 30)
        date_key = target_date.strftime(date_format)
        
        return data.get(date_key, None)

    else:
        print("Invalid input. Please provide a valid date or date range.")
        return None
