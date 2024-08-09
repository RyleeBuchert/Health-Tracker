from cronometer_export import collect_cronometer_data
from strava_export import collect_strava_data


if __name__ == "__main__":
    # Collect Cronometer nutrition data
    collect_cronometer_data()

    # Collect Strava activities data
    collect_strava_data()


