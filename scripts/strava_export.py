import requests
import os
import json
import pandas as pd
from export_data import update_google_sheet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File path to save the refresh token and activities data
REFRESH_TOKEN_PATH = f"{os.getenv('PROJECT_PATH')}/config/refresh_token.txt"
DATA_PATH = f"{os.getenv('PROJECT_PATH')}/data"

# Function to read the refresh token from file
def read_refresh_token(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read().strip()
    else:
        raise Exception(f"Refresh token file not found: {file_path}")

# Function to save the refresh token to file
def save_refresh_token(file_path, refresh_token):
    with open(file_path, 'w') as f:
        f.write(refresh_token)

# Function to get a new access token using the refresh token
# - Gets last refresh token to query API
# - Saves new refresh token and returns access token
def get_access_token():
    # Get the refresh token from the file
    REFRESH_TOKEN = read_refresh_token(REFRESH_TOKEN_PATH)

    # Retrieve the access key
    response = requests.post(
        url='https://www.strava.com/oauth/token',
        data={
            'client_id': os.getenv('STRAVA_CLIENT_ID'),
            'client_secret': os.getenv('STRAVA_CLIENT_SECRET'),
            'grant_type': 'refresh_token',
            'refresh_token': REFRESH_TOKEN
        }
    )

    # Get the access and updated refresh token
    if response.status_code == 200:
        data = response.json()
    else:
        raise Exception("Failed to refresh access token")
    
    # Save the new refresh token
    save_refresh_token(REFRESH_TOKEN_PATH, data['refresh_token'])

    # Return the access token
    return(data['access_token'])

# Download Strava activities data and save to file
def collect_strava_data():
    # Get the access token
    access_token = get_access_token()
    
    # Use the access token to fetch activities
    print("Downloading Strava data...")
    activities_response = requests.get(
        url='https://www.strava.com/api/v3/athlete/activities',
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()

    # Save activities to json file
    with open(f'{DATA_PATH}/downloads/strava_activities.json', 'w') as f:
        json.dump(activities_response, f, indent=4)

    # Create a list of dictionaries with the required fields
    activities = pd.DataFrame([
        {
            'id': activity['id'],
            'activity': activity['name'],
            'distance': activity['distance'],
            'moving_time': activity['moving_time'],
            'elapsed_time': activity['elapsed_time'],
            'date': pd.to_datetime(activity['start_date_local']).strftime('%Y-%m-%d'),
            'average_speed': activity['average_speed'],
            'max_speed': activity['max_speed'],
            'has_heartrate': activity['has_heartrate'],
            'average_heartrate': activity.get('average_heartrate', None),
            'max_heartrate': activity.get('max_heartrate', None)
        }
        for activity in activities_response
    ])

    # Load current activities save
    activities_save = pd.read_csv(f'{DATA_PATH}/strava_activities.csv', index_col=0)

    # Filter to new activities
    new_activities = activities[activities['date'] > max(activities_save['date'])]

    # Iterate over activities and collect calories/suffer score
    new_activity_info = []
    for id in new_activities['id']:
        # Use the access token to fetch activities
        new_activity_response = requests.get(
            url=f'https://www.strava.com/api/v3/activities/{id}',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        # Extract calorie and suffer score entries from json response
        new_activity_data = new_activity_response.json()
        new_activity_info.append([id, new_activity_data.get('calories'), new_activity_data.get('suffer_score')])

    # Additional activity information
    new_activity_info = pd.DataFrame(new_activity_info, columns=['id', 'calories', 'suffer_score'])

    # Join with activities
    new_activities = new_activities.merge(new_activity_info, on='id', how='left')

    # Select relevant columns for export
    activity_columns = [
        'activity', 'date', 'calories', 'distance', 
        'moving_time', 'elapsed_time', 'average_speed', 'max_speed', 
        'average_heartrate', 'max_heartrate', 'suffer_score'
    ]
    new_activities = new_activities.loc[:, activity_columns]

    if len(new_activities) > 0:
        # Combine the activities dataframes
        combined_activities = pd.concat([activities_save, new_activities], ignore_index=True)
        combined_activities.sort_values(by='date', ascending=False, inplace=True)
        combined_activities.reset_index(drop=True, inplace=True)

        # Save updated activities dataframe
        combined_activities.to_csv(f'{DATA_PATH}/strava_activities.csv')

        # Export activities to google sheets
        update_google_sheet(combined_activities, 1)
        print("Exported Strava data.")
    else:
        print("No new Strava data available.")


