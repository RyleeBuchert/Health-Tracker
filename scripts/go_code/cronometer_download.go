package main

import (
    "context"
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

    // Get today's date in the Central Time Zone
    today := time.Now().In(loc)
    date := time.Date(today.Year(), today.Month(), today.Day(), 0, 0, 0, 0, loc)

    // Get yesterday's date
    yesterday := date.AddDate(0, 0, -1)
    
    // Download the nutrition and exercise data for today
    fmt.Println("Downloading Cronometer data...")
    nutrition, err := c.ExportDailyNutrition(context.Background(), yesterday, date)
    if err != nil {
        log.Fatalf("failed to retrieve nutrition: %s", err)
    }

    servings, err := c.ExportServings(context.Background(), yesterday, date)
    if err != nil {
        log.Fatalf("failed to retrieve servings: %s", err)
    }

    exercise, err := c.ExportExercises(context.Background(), yesterday, date)
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

    // Define the path for the CSV file
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
