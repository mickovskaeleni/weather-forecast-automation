# **Weather Forecast Automation**

This project automates the process of fetching weather data, cleaning and standardizing it, storing it in BigQuery, and sending daily email updates with the forecast of rainy locations. The process is automated using cron jobs and Make.

## **Table of Contents**
1. [Project Setup](#project-setup)
2. [Dependencies](#dependencies)
3. [Python Code](#python-code)
4. [BigQuery Setup](#bigquery-setup)
5. [Cron Jobs Setup](#cron-jobs-setup)
6. [Make Automation](#make-automation)

---

## **Project Setup**

### **Clone the repository:**

```bash
git clone https://github.com/your-username/weather-forecast-automation.git
```

### **Navigate to the project directory:**

```bash
cd weather-forecast-automation
```

### **Create a Virtual Environment:**

```bash
python3 -m venv venv
```

### **Activate the virtual environment:**

For macOS/Linux:

```bash
source venv/bin/activate
```

For Windows:

```bash
venv\Scripts\activate
```

### **Install the dependencies:**

```bash
pip install -r requirements.txt
```

### **Set up environment variables:**

  1. Create a .env file in the root of your project directory.

  2. Add your API keys and Google Cloud credentials:

```bash
OPENWEATHER_API_KEY=your_openweather_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_cloud_credentials.json
```

## **Dependencies**

The following Python libraries are required to run the project. You can install all the dependencies using the `requirements.txt` file provided.

- `requests`: Used to make HTTP requests to the OpenWeather API and fetch weather data.
- `openai`: Used to generate human-readable weather summaries using OpenAI's GPT-3.
- `google-cloud-bigquery`: Used for interacting with Google BigQuery to store weather data.
- `python-dotenv`: Loads environment variables from a `.env` file for storing sensitive information (API keys and credentials).
- `google-api-core`: A core library required for BigQuery interactions.
- `grpcio`: Required for Google API client libraries, including BigQuery.

To install all the dependencies, simply run:

```bash
pip install -r requirements.txt
```

### **Required Python Version:**

This project requires Python 3.6+. It’s recommended to create a virtual environment to manage the dependencies.

## **Python Code**

The Python scripts in this project are responsible for fetching weather data, cleaning and standardizing it, and inserting it into BigQuery. Below are the detailed Python files used in the project.

### **`fetch_data.py`**

This script fetches weather data from the OpenWeatherMap API for a list of European capital cities, generates human-readable summaries using OpenAI's GPT-3, and returns the enhanced data.

### **`main.py`**

This script processes the weather data fetched by fetch_data.py, creates a table in BigQuery if it doesn't exist, and inserts the data into BigQuery.

## **BigQuery Setup**

### **1. Create BigQuery Dataset:**
- Go to **Google Cloud Console** > **BigQuery**.
- Create a new dataset named `weather_data`.

### **2. Create the following tables:**
- **`weather_forecast`**: This table stores the raw weather data fetched from the OpenWeatherMap API.
- **`weather_forecast_cleaned`**: This table stores the cleaned and standardized weather data.
- **`daily_rainy_forecasts`**: This table stores the filtered rainy forecasts for each day.

You can create the tables directly in the BigQuery Console or using SQL queries.

### **3. Create Scheduled Queries:**

#### **Query 1: Clean and Standardize Data**
This query will clean and standardize the weather data. It removes NULL values, standardizes weather descriptions (to lowercase), and removes duplicates by considering only the latest data for each city for a given day. The query runs daily at **6:00 AM UTC**.

```sql
-- Create or replace the cleaned table with standardization, removal of NULLs, and duplicates based on city and day
CREATE OR REPLACE TABLE `usecase-weather-project.weather_data.weather_forecast_cleaned` AS
WITH cleaned_data AS (
    -- Step 1: Remove rows with NULL values for city, weather, and temperature
    SELECT 
        city,
        temperature,
        weather,
        timestamp,
        forecast_summary
    FROM 
        `usecase-weather-project.weather_data.weather_forecast`
    WHERE
        city IS NOT NULL
        AND weather IS NOT NULL
        AND temperature IS NOT NULL
),
standardized_data AS (
    -- Step 2: Standardize weather descriptions to lowercase
    SELECT 
        city,
        temperature,
        LOWER(weather) AS standardized_weather,  -- Convert to lowercase for consistency
        timestamp,
        forecast_summary
    FROM cleaned_data
),
final_cleaned_data AS (
    -- Step 3: Remove duplicate records for the same city and day, keeping the most recent (max timestamp)
    SELECT
        city,
        temperature,
        standardized_weather AS weather,
        timestamp,
        forecast_summary
    FROM (
        SELECT 
            city,
            temperature,
            standardized_weather,
            timestamp,
            forecast_summary,
            ROW_NUMBER() OVER(PARTITION BY city, DATE(timestamp) ORDER BY timestamp DESC) AS row_num
        FROM standardized_data
    )
    WHERE row_num = 1  -- Keep only the most recent record for each city and day
)

-- Save the cleaned and deduplicated data to the new table
SELECT * FROM final_cleaned_data;
```
### **Query 2: Daily Rainy Forecasts**

This query filters the `weather_forecast_cleaned` table to include only rainy locations for the current day (only most recent records per day per city). The query runs daily at **6:03 AM UTC** and stores the result in the `daily_rainy_forecasts` table.

```sql
CREATE OR REPLACE TABLE `usecase-weather-project.weather_data.daily_rainy_forecasts` AS
WITH latest_weather AS (
    SELECT 
        city,
        temperature,
        weather,
        DATE(timestamp) AS forecast_date,  -- Extract the date part of the timestamp
        forecast_summary,
        ROW_NUMBER() OVER (PARTITION BY city, DATE(timestamp) ORDER BY timestamp DESC) AS row_num  -- Get the most recent record per city and day
    FROM 
        `usecase-weather-project.weather_data.weather_forecast_cleaned`
    WHERE
        LOWER(weather) LIKE '%rain%'  -- Filter for rainy weather
)

SELECT 
    city,
    temperature,
    weather,
    forecast_date,  -- Use the date part of the timestamp
    forecast_summary
FROM latest_weather
WHERE row_num = 1;  -- Only keep the latest record for each city per day
```
### **Table: `daily_rainy_forecasts`**

The `daily_rainy_forecasts` table is designed to store filtered weather data for cities where rain is expected. This table is updated daily by the scheduled query to only include rainy forecasts for the current day.

The table contains the following columns:

- **`city`**: The name of the city (e.g., "Prague").
- **`temperature`**: The current temperature in that city, measured in Celsius.
- **`weather`**: The weather description (e.g., "light rain", "overcast clouds").
- **`forecast_date`**: The date when the weather data was recorded.
- **`forecast_summary`**: A human-readable summary of the weather forecast for the city, generated using OpenAI's GPT model.

### **Scheduled Query Setup for Daily Rainy Forecasts**

To automate this process, you can schedule the query to run daily at **6:03 AM UTC**. Follow the steps below to schedule the query in BigQuery:

1. **Go to BigQuery Console** and navigate to **Scheduled Queries**.
2. Click on **Create Scheduled Query**.
3. In the **Query** section, paste the SQL query provided above.
4. For the **Target Table**, select `usecase-weather-project.weather_data.daily_rainy_forecasts`.
5. Set the **Schedule** to run **daily at 6:03 AM UTC**.
6. Save the scheduled query.

This will ensure that every morning at 6:03 AM UTC, the table is updated with the latest rainy locations for the day.

### **Cron Jobs Setup**

To automate the weather data retrieval and insertion into BigQuery, you can set up a **cron job** to run the Python script (`main.py`) on your local machine.

1. Open the crontab editor by running the following command:
```bash
crontab -e
```

2. Add the following cron job to run the script daily at 5:55 AM UTC:
```bash
55 5 * * * /path/to/your/venv/bin/python /path/to/your/project/main.py
```

Make sure to replace `/path/to/your/venv` with the actual path to your Python virtual environment and `/path/to/your/project` with the path to your project directory.

3. Save and exit the editor. This will execute the Python script every day at **5:55 AM UTC**, which will fetch the weather data and insert it into BigQuery.

## **Make Automation**

Once the daily weather data is available in BigQuery, you can set up an automation workflow in Make (formerly known as Integromat) to send the daily rainy forecasts to your email.

### 1. Create a Make (formerly Integromat) Account:
If you don’t already have an account, sign up for free at [Make](https://make.com).

### 2. Create a Scenario in Make:
Create a new scenario in Make and import the `make_blueprint.json` (having 3 modules: BigQuery, Text Aggreagator and Send an Email)

### **3. Set up Automation to Run Daily (some time after the Daily Rainy Forecast scheduled query) :**
After creating the scenario, set the automation to run daily (for example at **8:30 AM CET**). This will ensure you receive a daily email with the weather forecast for rainy locations.

---

## **License**

This project is licensed under the MIT License.

---

This section of the README covers the **`daily_rainy_forecasts`** table, the scheduling of the query to filter rainy locations, the cron job setup for running the Python script, and how to automate the daily email notifications using Make. This ensures that you receive daily updates about rainy locations (capitals) in Europe.

---


