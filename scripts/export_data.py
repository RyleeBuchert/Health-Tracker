import os
import gspread
from gspread_dataframe import set_with_dataframe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory to download files
DATA_PATH = f"{os.getenv('PROJECT_PATH')}/data"

# Retrieve the latest daily summary file from cronometer
def get_latest_download(file_name):
    # Get list of daily summary files
    files = os.listdir(f"{DATA_PATH}/downloads/")
    filtered_files = [file for file in files if file.startswith(f"{file_name}_")]
    
    # Find the most recent file
    timestamps = [file.split("_")[1].split(".")[0] for file in filtered_files]
    sorted_timestamps = sorted(timestamps, reverse=True)

    # Return path for the latest file
    return f"{DATA_PATH}/downloads/{file_name}_{sorted_timestamps[0]}.csv"

# Update the google nutrition sheet with the new data
def update_google_sheet(dataframe, sheet):
    # Connect to google service account and load gsheet
    gc = gspread.service_account(filename=f"{os.getenv('PROJECT_PATH')}/config/credentials.json")
    sh = gc.open_by_key(os.getenv("GSHEET_ID"))
    
    # Select the nutrition worksheet, clear, and update
    worksheet = sh.get_worksheet(sheet)
    worksheet.clear()
    set_with_dataframe(worksheet, dataframe)


