import streamlit as st  
from io import BytesIO
from PIL import Image
import requests

# Check if OpenWeather API key is set
if st.secrets["OPENWEATHER_API_KEY"] != "":

    # Get the weather data from openweathermap
    lat = 46.8655
    lon = 9.5423

    # Get weather data from OpenWeatherMap
    base_url = "http://api.openweathermap.org/data/2.5/weather?"

    complete_url = base_url + "appid=" + \
        st.secrets["OPENWEATHER_API_KEY"] + "&lat=" + \
        str(lat) + "&lon=" + str(lon) + "&units=metric&lang=de"
    
    # Get the response
    response = requests.get(complete_url)

    # Convert the response to json
    weather_data = response.json()

    if weather_data["cod"] == 200:

        # Get City and Country
        city = weather_data["name"]
        country = weather_data["sys"]["country"]

        st.header(f"Wetter in {city}, {country}", divider="gray", anchor=False)

        # Convert temperature to celsius
        current_temperature = int(weather_data["main"]["temp"])
        current_feels_like_temperature = weather_data["main"]["feels_like"]
        current_pressure = weather_data["main"]["pressure"]
        current_humidity = weather_data["main"]["humidity"]

        # Wind
        wind_data = weather_data["wind"]
        wind_speed = weather_data["wind"]["speed"].__round__(1)
        wind_direction = weather_data["wind"]["deg"]

        # Convert wind direction to text
        if wind_direction > 337.5:
            wind_direction_text = "N"
        elif wind_direction > 292.5:
            wind_direction_text = "NW"
        elif wind_direction > 247.5:
            wind_direction_text = "W"
        elif wind_direction > 202.5:
            wind_direction_text = "SW"
        elif wind_direction > 157.5:
            wind_direction_text = "S"
        elif wind_direction > 122.5:
            wind_direction_text = "SE"
        elif wind_direction > 67.5:
            wind_direction_text = "E"
        elif wind_direction > 22.5:
            wind_direction_text = "NE"
        else:
            wind_direction_text = "N"

        # Get icon
        icon = weather_data["weather"][0]["icon"]

        # Get the icon from openweathermap
        icon_url = f"http://openweathermap.org/img/wn/{icon}@4x.png"

        # Download the icon
        icon_data = BytesIO()
        icon_response = requests.get(icon_url)
        icon_data.write(icon_response.content)
        icon_image = Image.open(icon_data)

        # Description
        weather_description = weather_data["weather"][0]["description"]

        # Visibility
        visibility = weather_data["visibility"].__round__(1)
        
        if visibility < 1000:
            visibility = f"{visibility}m"
        else:
            visibility = f"{visibility/1000}km"
        
        st.text("")
        col1, col2 = st.columns([1.3, 1])

        col1.subheader("")
        col1.subheader("")
        col1.subheader(f"Zustand: {weather_description}")
        col1.subheader(f"Temperatur: {current_temperature}°C")
        col2.image(icon_image)

        st.text("")

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        col1.metric("Wind", f"{wind_speed}m/s {wind_direction_text}")
        col2.metric("Luftdruck", f"{current_pressure}hPa")
        col3.metric("Feuchtigkeit", f"{current_humidity}%")
        col4.metric("Sichtbarkeit", f"{visibility}")

        st.text("")

        # Get location id
        location_id = weather_data["id"]
        st.markdown(
            f"Daten von [OpenWeatherMap](https://openweathermap.org).")
