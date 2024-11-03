import os
import pandas as pd
from export_data import get_latest_download, update_google_sheet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory to download files
DATA_PATH = f"{os.getenv('PROJECT_PATH')}/data"

# Process Cronometer downloads and export to google sheets
def collect_cronometer_data():
    # Load nutrition masterfile
    nutrition = pd.read_csv(f"{DATA_PATH}/cronometer_nutrition.csv", index_col=0)

    # Load recent cronometer downloads
    daily_summary = pd.read_csv(get_latest_download("dailysummary"))
    daily_exercises = pd.read_csv(get_latest_download("exercises"))

    # Filter daily summary data
    daily_summary = daily_summary[daily_summary['Date'] > max(nutrition['Date'])]
    daily_summary = daily_summary[daily_summary['Completed'] == True]

    # Calculate total calories burned
    daily_exercises.rename(columns={'Day': 'Date', 'Calories Burned': 'Burned (kcal)'}, inplace=True)
    daily_exercises['Burned (kcal)'] = daily_exercises['Burned (kcal)'].abs()
    daily_exercises = daily_exercises.groupby('Date')['Burned (kcal)'].sum()
    daily_exercises = daily_exercises + 1850
    daily_exercises = daily_exercises.reset_index()

    # Merge with daily nutrition data
    cronometer_nutrition = daily_summary.merge(daily_exercises, how='left', on='Date')
    cronometer_cols = ['Date', 'Energy (kcal)', 'Burned (kcal)', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Added Sugars (g)', 'Sodium (mg)']
    cronometer_nutrition = cronometer_nutrition[cronometer_cols]
    cronometer_nutrition['Burned (kcal)'] = cronometer_nutrition['Burned (kcal)'].fillna(1850)

    # If new data is available, combine files, export to google sheets, and save
    if len(cronometer_nutrition) > 0:
        cronometer_nutrition_updated = pd.concat([nutrition, cronometer_nutrition], ignore_index=True)
        update_google_sheet(cronometer_nutrition_updated, 0)
        cronometer_nutrition_updated.to_csv(f"{DATA_PATH}/cronometer_nutrition.csv")
        print("Exported Cronometer nutrition data.")
    else:
        print("No new Cronometer nutrition data available.")

    # # Load serings masterfile
    # servings = pd.read_csv(f"{DATA_PATH}/cronometer_servings.csv", index_col=0)

    # # Load recent servings download
    # daily_servings = pd.read_csv(get_latest_download("servings"))
    
    # # Filter servings data
    # daily_servings.rename(columns={'Day': 'Date'}, inplace=True)
    # daily_servings = daily_servings[daily_servings['Date'] > max(servings['Date'])]

    # # If new data is available, combine files, export to google sheets, and save
    # if len(daily_servings) > 0 and len(cronometer_nutrition) > 0:
    #     cronometer_servings = pd.concat([servings, daily_servings], ignore_index=True)
    #     update_google_sheet(cronometer_servings, 2)
    #     cronometer_servings.to_csv(f"{DATA_PATH}/cronometer_servings.csv")
    #     print("Exported Cronometer servings data.")
    # else:
    #     print("No new Cronometer servings data available.")


if __name__ == "__main__":
    # Collect Cronometer nutrition data
    collect_cronometer_data()