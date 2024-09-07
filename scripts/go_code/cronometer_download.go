package main

import (
    "context"
    "encoding/csv"
    "fmt"
    "log"
    "os"
    "time"
    "path/filepath"
    "io/ioutil"
    "github.com/jrmycanady/gocronometer"
)

func main() {
    // Load Cronometer credentials from environment variables
    username := os.Getenv("CRONOMETER_EMAIL")
    password := os.Getenv("CRONOMETER_PASSWORD")

    if username == "" || password == "" {
        log.Fatalf("Cronometer credentials are not set in the environment variables")
    }

    // Create the client and login to Cronometer
    c := gocronometer.NewClient(nil)
    err := c.Login(context.Background(), username, password)
    if err != nil {
        log.Fatalf("failed to login with valid creds: %s", err)
    }

    // Get today's date in the Central Time Zone
    loc, err := time.LoadLocation("America/Chicago")
    if err != nil {
        log.Fatalf("failed to load location: %s", err)
    }
    today := time.Now().In(loc)
    todayDate := time.Date(today.Year(), today.Month(), today.Day(), 0, 0, 0, 0, loc)

    // Load existing data from the CSV file to get the most recent date
    csvFilePath := "../../data/cronometer_nutrition.csv"
    mostRecentDate, err := getMostRecentDate(csvFilePath)
    if err != nil {
        log.Fatalf("failed to get most recent date from CSV: %s", err)
    }
    
    // Calculate start date (one day after the most recent date)
    startDate := mostRecentDate.AddDate(0, 0, 1)

    // If the start date is after today's date, there's nothing to update
    if !startDate.Before(todayDate) {
        fmt.Println("Data is already up-to-date.")
        return
    }

    // Download the nutrition and exercise data between startDate and today
    fmt.Println("Downloading Cronometer data...")
    nutrition, err := c.ExportDailyNutrition(context.Background(), startDate, todayDate)
    if err != nil {
        log.Fatalf("failed to retrieve nutrition: %s", err)
    }

    servings, err := c.ExportServings(context.Background(), startDate, todayDate)
    if err != nil {
        log.Fatalf("failed to retrieve servings: %s", err)
    }

    exercise, err := c.ExportExercises(context.Background(), startDate, todayDate)
    if err != nil {
        log.Fatalf("failed to retrieve exercises: %s", err)
    }

    // Ensure the data directory exists
    dataDir := "../../data/downloads"
    if _, err := os.Stat(dataDir); os.IsNotExist(err) {
        err = os.Mkdir(dataDir, 0755)
        if err != nil {
            log.Fatalf("failed to create data directory: %s", err)
        }
    }

    // Define the path for the CSV files
    nutritionFileName := fmt.Sprintf("dailysummary_%s.csv", today.Format("20060102"))
    nutritionFilePath := filepath.Join(dataDir, nutritionFileName)

    servingsFileName := fmt.Sprintf("servings_%s.csv", today.Format("20060102"))
    servingsFilePath := filepath.Join(dataDir, servingsFileName)

    exerciseFileName := fmt.Sprintf("exercises_%s.csv", today.Format("20060102"))
    exerciseFilePath := filepath.Join(dataDir, exerciseFileName)

    // Write the CSV data to the file
    err = ioutil.WriteFile(nutritionFilePath, []byte(nutrition), 0644)
    if err != nil {
        log.Fatalf("Failed to write nutrition data to file: %s", err)
    }

    err = ioutil.WriteFile(servingsFilePath, []byte(servings), 0644)
    if err != nil {
        log.Fatalf("Failed to write servings data to file: %s", err)
    }

    err = ioutil.WriteFile(exerciseFilePath, []byte(exercise), 0644)
    if err != nil {
        log.Fatalf("Failed to write exercise data to file: %s", err)
    }
}

// getMostRecentDate reads the CSV file and returns the most recent date in the 'Date' column
func getMostRecentDate(csvFilePath string) (time.Time, error) {
    file, err := os.Open(csvFilePath)
    if err != nil {
        return time.Time{}, fmt.Errorf("unable to open CSV file: %w", err)
    }
    defer file.Close()

    reader := csv.NewReader(file)
    records, err := reader.ReadAll()
    if err != nil {
        return time.Time{}, fmt.Errorf("failed to read CSV file: %w", err)
    }

    // Check if the CSV has records
    if len(records) == 0 {
        return time.Time{}, fmt.Errorf("CSV file is empty")
    }

    // Find the 'Date' column index
    dateColumnIndex := -1
    for i, columnName := range records[0] {
        if columnName == "Date" {
            dateColumnIndex = i
            break
        }
    }

    if dateColumnIndex == -1 {
        return time.Time{}, fmt.Errorf("'Date' column not found in the CSV")
    }

    // Assuming the date format in the CSV is YYYY-MM-DD
    layout := "2006-01-02"
    var mostRecentDate time.Time

    for _, record := range records[1:] {
        dateStr := record[dateColumnIndex]

        // Skip empty or invalid date entries
        if dateStr == "" || len(dateStr) != len(layout) {
            continue
        }

        date, err := time.Parse(layout, dateStr)
        if err != nil {
            continue // Skip invalid dates
        }

        if date.After(mostRecentDate) {
            mostRecentDate = date
        }
    }

    if mostRecentDate.IsZero() {
        return time.Time{}, fmt.Errorf("no valid dates found in the CSV")
    }

    return mostRecentDate, nil
}
