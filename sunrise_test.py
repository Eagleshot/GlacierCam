import random
import json
import time
import datetime
import requests
import pytz
import suntime

# Generate 100 random locations
locations = []
for i in range(10):
    locations.append((random.uniform(-90, 90), random.uniform(-180, 180)))

# Get sunrise and sunset times from OpenWeatherMap API
api_key = "e50a51592ca62560405aad1b5fe3a825"

for lat, lon in locations:

    # OpenWeatherMap API
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(url, timeout=5)
    data = json.loads(response.text)
    today_sr_openweathermap = data["sys"]["sunrise"]
    today_sr_openweathermap = datetime.datetime.fromtimestamp(today_sr_openweathermap)
    today_ss_openweathermap = data["sys"]["sunset"]
    today_ss_openweathermap = datetime.datetime.fromtimestamp(today_ss_openweathermap)

    # Sunrise and sunset times
    sun = suntime.Sun(lat, lon)
    try:
        today_sr_calculated = sun.get_sunrise_time()
        today_sr_calculated = pytz.utc.localize(today_sr_calculated) # Convert to offset-aware datetime object
        today_ss_calculated = sun.get_sunset_time()
        today_ss_calculated = pytz.utc.localize(today_ss_calculated) # Convert to offset-aware datetime object
    except suntime.SunTimeException as e:
        print("No sunrise today")
        continue

    # Check if the results are within 1 minute of each other
    if not abs(today_sr_openweathermap - today_sr_calculated) < datetime.timedelta(minutes=1):
        print(f"Sunrise times do not match for location {lat}, {lon}.")
        print(f"OpenWeatherMap API: {today_sr_openweathermap}")
        print(f"Calculated: {today_sr_calculated}")
        
    time.sleep(1)
