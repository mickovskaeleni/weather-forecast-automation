import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
import logging
import time

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from environment variables
API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
client = OpenAI(
    # This is the default and can be omitted
    api_key=OPENAI_API_KEY,
)

# List of European capital cities
CITIES = [
    'Tirana', 'Andorra la Vella', 'Yerevan', 'Vienna', 'Baku', 'Minsk', 'Brussels', 'Sarajevo', 'Sofia', 'Zagreb',
    'Nicosia', 'Prague', 'Copenhagen', 'Tallinn', 'Helsinki', 'Paris', 'Tbilisi', 'Berlin', 'Athens', 'Budapest',
    'Reykjavik', 'Dublin', 'Rome', 'Nur-Sultan', 'Pristina', 'Riga', 'Vaduz', 'Vilnius', 'Luxembourg City', 'Valletta',
    'Chisinau', 'Monaco', 'Podgorica', 'Amsterdam', 'Skopje', 'Oslo', 'Warsaw', 'Lisbon', 'Bucharest', 'Moscow',
    'San Marino', 'Belgrade', 'Bratislava', 'Ljubljana', 'Madrid', 'Stockholm', 'Bern', 'Ankara', 'Kyiv', 'London'
]

# OpenWeatherMap API URL
URL = 'http://api.openweathermap.org/data/2.5/weather'

# Set up logging
logging.basicConfig(filename="error_log.txt", level=logging.ERROR)

def generate_summary(weather_data):
    """Use OpenAI's GPT to generate a human-readable weather summary."""

    response = client.responses.create(
    model="gpt-3.5-turbo",
    instructions="You are a weather forecast summarizer. Your task is to summarize the weather data provided in a human-readable format.",
    input=f"Provide a short and conscise weather forecast summary that doesn't exceed the limit of 999 characters for the following data: {weather_data}",
    )

    return response.output_text

def fetch_weather_data():
    """Fetch weather data for a list of cities from the OpenWeatherMap API."""
    weather_data = []

    for city in CITIES:
        attempts = 3
        for attempt in range(attempts):
            try:
                params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
                response = requests.get(URL, params=params)

                # If the response is successful, process the data
                if response.status_code == 200:
                    city_data = response.json()

                    # Generate the summary for the city using OpenAI's LLM
                    forecast_summary = generate_summary(city_data)
                    city_data['forecast_summary'] = forecast_summary
                    weather_data.append(city_data)
                    break  # Break the retry loop if successful
                else:
                    logging.error(f"Failed to get data for {city}. Status Code: {response.status_code}")
                    time.sleep(5)  # Wait before retrying

            except Exception as e:
                logging.error(f"Error while fetching data for {city}: {e}")
                time.sleep(5)  # Wait before retrying

    return weather_data
