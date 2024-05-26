"""Webserver for the Eagleshot GlacierCam - https://github.com/Eagleshot/GlacierCam"""
from io import BytesIO
from datetime import datetime
import hmac
from PIL import Image
import streamlit as st
import pandas as pd
import altair as alt
import pytz
from suntime import Sun
import requests
import yaml
from settings import Settings
from fileserver import FileServer
import logging # TODO

timezone = pytz.timezone('Europe/Zurich')
timezoneUTC = pytz.timezone('UTC')

# Set page title and favicon
st.set_page_config(
    page_title="GlacierCam",
    page_icon="🏔️",
    initial_sidebar_state="collapsed",
    menu_items={
        # TODO
        'Get Help': "mailto:noel@eagleshot.ch",
        'Report a bug': "mailto:noel@eagleshot.ch",
        'About': "Erstellt von [Noel Frey](https://github.com/Eagleshot) im Rahmen einer Zusammenarbeit der [FHGR](https://www.fhgr.ch/) und der [ETH Zürich](https://vaw.ethz.ch)."
    }
)

# Change the camera selection
if len(st.secrets["FTP_FOLDER"]) > 1:
    with st.sidebar:
        st.header("Kamera auswählen")
        FTP_FOLDER = st.selectbox(
            "Bitte wählen Sie eine Kamera aus:",
            options=st.secrets["FTP_FOLDER"],
            index=0,
        )
else:
    FTP_FOLDER = st.secrets["FTP_FOLDER"][0]

# Connect to the file server
FTP_HOST = st.secrets["FTP_HOST"]
FTP_USERNAME = st.secrets["FTP_USERNAME"]
FTP_PASSWORD = st.secrets["FTP_PASSWORD"]

fileserver = FileServer(FTP_HOST, FTP_USERNAME, FTP_PASSWORD)
fileserver.change_directory(FTP_FOLDER)

# Get the list of files from the FTP server
fileserver.change_directory("save") # TODO
files = fileserver.list_files()
fileserver.change_directory("..") # TODO
LOG_FILENAMEs = fileserver.list_files() # TODO

# Only show the image files
imgFiles = [file for file in files if file.endswith(".jpg")]

# Load settings from server
fileserver.download_file("settings.yaml")
settings = Settings()

# Camera name
cameraname = settings.get("cameraName")
st.title(cameraname, anchor=False)
img_placeholder = st.empty()

# Download diagnostics file
fileserver.download_file("diagnostics.yaml")

with open("diagnostics.yaml", 'r', encoding='utf-8') as file:
    data = yaml.safe_load(file)

# Convert the data into a Pandas DataFrame
df = pd.DataFrame(data)
if 'timestamp' in df.columns:
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%MZ')
elif df.empty:
    st.info("No data available at the moment.", icon="📊")

##############################################
# Sidebar
##############################################
with st.sidebar:

    # Zeitraum auswählen
    if 'timestamp' in df.columns:
        st.header("Zeitraum auswählen")
        with st.expander("Zeitraum auswählen"):

            # Get start and end date
            start_date = st.date_input("Startdatum", df['timestamp'].iloc[0])
            end_date = st.date_input("Enddatum", df['timestamp'].iloc[-1])

            # Get start and end time
            start_time = st.time_input(
                "Startzeit", datetime.strptime("00:00", "%H:%M").time())
            end_time = st.time_input(
                "Endzeit", datetime.strptime("23:59", "%H:%M").time())

            # Combine the start and end date and time
            start_dateTime = datetime.combine(start_date, start_time)
            end_dateTime = datetime.combine(end_date, end_time)

            # Check if the start date is before the end date
            if start_dateTime >= end_dateTime:
                st.error("Das Enddatum muss nach dem Startdatum liegen.")
            else:
                # Filter the dataframe
                df = df[(df['timestamp'] >= start_dateTime)
                        & (df['timestamp'] <= end_dateTime)]

    # Zeitzone auswählen
    # TODO: Automatic timezone detection
    st.header("Zeitzone auswählen")
    timezone_selection = st.selectbox(
        "Bitte wählen Sie eine Zeitzone aus:",
        options=pytz.common_timezones,
        index=pytz.common_timezones.index('Europe/Zurich'),
    )
    timezone = pytz.timezone(timezone_selection)

    # Login status
    # TODO Improve security (e.g. multiple login attempts)
    st.session_state["userIsLoggedIn"] = False

    def enter_password(password: str) -> str:
        '''Check if the entered password is correct.'''
        if hmac.compare_digest(st.session_state["password"], st.secrets["FTP_PASSWORD"]):
            st.session_state["userIsLoggedIn"] = True
            del st.session_state["password"] # Don't store the password

    st.header("Login")
    password = st.text_input("Bitte loggen Sie sich ein um die Einstellungen anzupassen.",
                                placeholder="Please Enter Password", type="password", on_change=enter_password)

# Select slider if multiple images are available
if len(imgFiles) > 1:

    # UTC offset
    UTC_OFFSET_HOUR = int(timezone.utcoffset(datetime.now()).total_seconds() / 3600)

    selected_file = st.select_slider(
        "Wähle ein Bild aus",
        label_visibility="hidden",  # Hide the label
        options=imgFiles,
        value=imgFiles[-1],
        # Format the timestamp and dont show date if it is today
        format_func=lambda x: f"{int(x[9:11]) + UTC_OFFSET_HOUR}:{x[11:13]} Uhr" if x[:8] == datetime.now(
        timezone).strftime("%Y%m%d") else f"{x[6:8]}.{x[4:6]}.{x[:4]} {int(x[9:11]) + UTC_OFFSET_HOUR}:{x[11:13]} Uhr"
    )
elif len(imgFiles) == 1:
    selected_file = imgFiles[0]
else:
    img_placeholder.info("No images available at the moment.", icon="📷")

# Get the image file from the FTP server
if len(imgFiles) > 0:
    fileserver.change_directory("save") # TODO
    image_data = fileserver.get_file_as_bytes(selected_file)
    fileserver.change_directory("..") # TODO

    # Display the image with the corresponding timestamp
    img_placeholder.image(Image.open(image_data), use_column_width=True)

    # Download button for image
    st.download_button(
        label="Bild herunterladen 📷",
        data=image_data,
        file_name=selected_file,
        mime="image/jpeg",
        use_container_width=True
    )

    st.text("")

##############################################
# Overview of the last measurements
##############################################
if 'selected_file' in locals() or 'selected_file' in globals():
    timestampSelectedImage = datetime.strptime(selected_file[0:13], '%Y%m%d_%H%M')
    df['timestamp'] = df['timestamp'].dt.floor('min')  # Remove seconds from timestamp
    index = df[df['timestamp'] == timestampSelectedImage].index[0]
else:
    index = -1

col1, col2, col3, col4 = st.columns(4)
if 'battery_voltage' in df.columns:
    col1.metric("Batterie", f"{df['battery_voltage'].iloc[index]} V")
if 'internal_voltage' in df.columns:
    col2.metric("Interne Spannung", f"{df['internal_voltage'].iloc[index]} V")
if 'temperature' in df.columns:
    col3.metric("Temperatur", f"{df['temperature'].iloc[index]} °C")
if 'signal_quality' in df.columns:
    col4.metric("Signalqualität", df['signal_quality'].iloc[index])

##############################################
# Next and last startup
##############################################

# Last startup relative to now
if 'timestamp' in df.columns:
    st.write("")
    lastStartup = df['timestamp'].iloc[-1]
    now = datetime.now(timezoneUTC).replace(tzinfo=None)
    timeDifference = now - lastStartup.replace(tzinfo=None)

    # Write difference in hours and minutes
    next_last_startup_text = "Letzter Start vor "

    # Days
    if timeDifference.days > 1:
        next_last_startup_text += f"{timeDifference.days} Tagen, "
    elif timeDifference.days == 1:
        next_last_startup_text += "1 Tag, "

    # Hours
    if timeDifference.seconds//3600 > 0:
        next_last_startup_text += f"{timeDifference.seconds//3600} Stunden und "

    # Minutes
    if (timeDifference.seconds//60) % 60 > 1:
        next_last_startup_text += f"{(timeDifference.seconds//60) % 60} Minuten"
    else:
        next_last_startup_text += "weniger als eine Minute"

    # Print next startup relative to now
    next_startup_time = df['next_startup_time'].iloc[-1]
    next_startup_time = datetime.strptime(next_startup_time, '%Y-%m-%d %H:%M:%SZ') or datetime(1970, 1, 1, 0, 0)
    next_startup_time = next_startup_time + pd.Timedelta(minutes=1)

    # Check if next startup is in the future
    if next_startup_time < now:
        next_last_startup_text += "."
    else:
        timeDifference = next_startup_time - now
        next_last_startup_text += " - nächster Start in "

        if timeDifference.seconds//3600 > 0:
            next_last_startup_text += f"{timeDifference.seconds//3600} Stunden und {(timeDifference.seconds//60) % 60} Minuten."
        elif (timeDifference.seconds//60) % 60 > 1:
            next_last_startup_text += f"{(timeDifference.seconds//60) % 60} Minuten."
        else:
            next_last_startup_text += "weniger als einer Minute."

    st.write(next_last_startup_text)

st.divider()

##############################################
# Weather widget
##############################################

dfMap = pd.DataFrame()

if settings.get("location_overwrite"):
    latitude = settings.get("latitude")
    longitude = settings.get("longitude")

elif 'latitude' in df.columns and 'longitude' in df.columns:
    # Get the last entry of df latitude that is not null
    last_latitude = df['latitude'].iloc[::-1].dropna().iloc[0]

    dfMap = df[(df['latitude'].notnull()) & (df['longitude'].notnull())]

    latitude = dfMap['latitude'].iloc[-1]
    longitude = dfMap['longitude'].iloc[-1]

@st.cache_data(show_spinner=False, ttl=300)
def get_weather_data(latitude: float, longitude: float) -> dict:
    '''Get weather data from OpenWeatherMap.'''
    # Get weather data from OpenWeatherMap
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{BASE_URL}appid={st.secrets['OPENWEATHER_API_KEY']}&lat={latitude}&lon={longitude}&units=metric&lang=de"
    response = requests.get(complete_url, timeout=5)
    return response.json()

# Check if OpenWeather API key is set and location is available
if st.secrets["OPENWEATHER_API_KEY"] != "" and len(dfMap) > 0:

    latitude = round(latitude, 5)
    longitude = round(longitude, 5)

    # Get weather data from OpenWeatherMap
    weather_data = get_weather_data(latitude, longitude)

    if weather_data["cod"] == 200: # Check if response is valid

        # Convert temperature to celsius
        current_temperature = int(weather_data["main"]["temp"])
        current_pressure = weather_data["main"]["pressure"]
        current_humidity = weather_data["main"]["humidity"]

        # Wind speed and direction
        wind_speed = round(weather_data["wind"]["speed"], 1)
        wind_direction = weather_data["wind"]["deg"]

        # Convert wind direction to text
        directions = ["N", "NW", "W", "SW", "S", "SE", "E", "NE", "N"]
        WIND_DIRECTION_TEXT = directions[int((wind_direction + 22.5) % 360 // 45)]

        # Get the icon from OpenWeatherMap
        icon = weather_data["weather"][0]["icon"]
        icon_url = f"http://openweathermap.org/img/wn/{icon}@4x.png"

        # Download the icon
        icon_data = BytesIO()
        icon_response = requests.get(icon_url, timeout=5)
        icon_data.write(icon_response.content)
        icon_image = Image.open(icon_data)

        # Cut off all invisible pixels
        icon_image = icon_image.crop(icon_image.getbbox())

        # Description
        weather_description = weather_data["weather"][0]["description"]

        # Visibility
        visibility = weather_data["visibility"]

        if visibility < 1000:
            visibility = f"{visibility} m"
        else:
            visibility = f"{int(visibility/1000)} km"

        col1, col2 = st.columns([1.5, 1])

        with col1:
            st.header("Wetter", anchor=False)
            # st.caption(f"{name}, {country}")
            st.text("")
            st.markdown(f"### :grey[Temperatur: {current_temperature} °C]")

        with col2:
            st.text("")
            st.text("")
            st.text("")
            st.text("")
            st.image(icon_image, caption=weather_description)

        st.text("")

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        col1.metric("Wind", f"{wind_speed} m/s",
                    delta=WIND_DIRECTION_TEXT, delta_color="off")
        col2.metric("Luftdruck", f"{current_pressure} hPa")
        col3.metric("Luftfeuchtigkeit", f"{current_humidity} %")
        col4.metric("Sichtweite", f"{visibility}")

        st.text("")
        st.markdown("Daten von [OpenWeatherMap](https://openweathermap.org).")

        st.divider()

##############################################
# Sunrise and sunset
##############################################
if len(dfMap) > 0:
    sun = Sun(latitude, longitude)
    sunrise = sun.get_sunrise_time()
    sunrise = sunrise.astimezone(timezone)
    sunrise = sunrise.strftime('%H:%M Uhr')

    sunset = sun.get_sunset_time()
    sunset = sunset.astimezone(timezone)
    sunset = sunset.strftime('%H:%M Uhr')

    st.header("Sonnenauf- und Untergang", anchor=False)
    st.text("")

    col1, col2, col3 = st.columns([0.5, 1, 1])
    col2.image("https://openweathermap.org/img/wn/01d@2x.png")
    col2.metric("Sonnenaufgang", sunrise)
    col3.image("https://openweathermap.org/img/wn/01n@2x.png")
    col3.metric("Sonnenuntergang", sunset)

    st.divider()

##############################################
# Charts
##############################################

def plot_chart(chart_title: str, y: str, unit: str = None):
    '''Create an Altair chart.'''
    y_label = f"{chart_title} ({unit})" if unit else chart_title
    if "timestamp" in df.columns and y in df.columns:
        st.header(chart_title, anchor=False)
        st.write(f"Last measurement: {str(df[y].iloc[-1])} {unit}")
        chart = alt.Chart(df).mark_line().encode(
            x=alt.X(f'{"timestamp"}:T', axis=alt.Axis(
                title="Time", labelAngle=-45)),
            y=alt.Y(f'{y}:Q', axis=alt.Axis(title=f'{y_label}')),
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

plot_chart("Battery Voltage", 'battery_voltage', "V")
plot_chart("Internal Voltage", 'internal_voltage', "V")
plot_chart("Temperature", 'temperature', "°C")
plot_chart("Signal Quality", 'signal_quality')
# See: https://www.waveshare.com/w/upload/5/54/SIM7500_SIM7600_Series_AT_Command_Manual_V1.08.pdf

##############################################
# Map
##############################################
if not dfMap.empty:
    st.divider()
    st.header("Standort", anchor=False)
    st.map(pd.DataFrame({'lat': [latitude], 'lon': [longitude]}))

    # Print coordinates
    st.write(
        f"Breitengrad: {latitude}, Längengrad: {longitude}, Höhe: {dfMap['height'].iloc[-1]} m.ü.M. - [Google Maps](https://www.google.com/maps/search/?api=1&query={latitude},{longitude})")

    # Print timestamp
    if not settings.get("location_overwrite"):
        st.markdown(f"Letztes Standortupdate: {df['timestamp'].iloc[-1].strftime('%d.%m.%Y %H:%M Uhr')}")

    st.divider()
    st.write("")
    st.write("")


##############################################
# Settings and diagnostics
##############################################

# Read settings.yaml and display it
# TODO Settings (incl. validation)
if st.session_state["userIsLoggedIn"]:
    with st.expander("Kameraeinstellungen"):

        st.write("Kamera")
        
        # Resolution
        # TODO
        resolution = st.selectbox(
            "Auflösung", options=["Automatisch", "2592x1944", "1920x1080", "1280x720", "640x480"], index=0, help="Bildauflösung der Kamera.")

        st.divider()
        st.write("Zeit")
        col1, col2 = st.columns(2)

        # Start time
        start_time = col1.time_input('Startzeit', datetime.strptime(f"{settings.get('startTimeHour')}:{settings.get('startTimeMinute')}", "%H:%M").time(), help="Startzeit der Aufnahme.")

        # Interval
        intervalTime = col2.number_input("Aufnahmeintervall", min_value=5, max_value=720, value=settings.get('intervalMinutes'), step=5, help="Aufnahmeintervall in Minuten.")

        # Repetitions per day
        repetitionsPerday = col1.number_input("Aufnahmen pro Tag", min_value=1, max_value=100, value=settings.get('repetitionsPerday'), step=1, help="Anzahl Aufnahmen pro Tag.")
        # Duration
        # durationTime = col2.number_input("Max. Aufnahmedauer", min_value=1, max_value=10, value=settings.get('maxDurationMinute'), step=1, help="Maximale Aufnahmedauer in Minuten. Das Kamerasystem wird spätestens nach dieser Zeitdauer ausgeschaltet.")
        timeSync = st.toggle(
            "Zeitsynchronisation", value=settings.get("timeSync"), help="Aktiviert die automatische Zeitsynchronisation der Kamera mit dem Internet.")

        st.divider()
        st.write("Weitere Einstellungen")
        enableGPS = st.toggle("GPS aktivieren", value = settings.get("enableGPS"),
             help="Aktiviert die GPS-Funktion der Kamera. Die GPS-Antenne muss dafür angeschlossen sein!")
        extendedDiagnostics = st.toggle(
            "Erweiterte Diagnosedaten", value=settings.get("uploadWittyPiDiagnostics"), help="Hochladen von erweiterten Diagnosedaten. Kann bei schwerwiegenderen Problemen helfen.")

        st.divider()
        st.write(":red[Danger Zone]")
        shutdown = st.toggle("Shutdown", value=settings.get("shutdown"), help="Kamera nach Bildaufnahme ausschalten. Wird diese Option deaktiviert, schaltet sich die Kamera erst verspätet aus und der Stromverbrauch ist erhöht.")

        # Validate the settings
        valid_settings = settings.is_valid()

        if not valid_settings:
            st.error("Die Einstellungen sind ungültig. Bitte überprüfen Sie die Einstellungen.")
            # settings.save_to_file("improved_settings.yaml")


        # Save the settings
        col1, col2 = st.columns([5, 1])
        if col2.button("Speichern", key="saveCameraSettings"): #TODO
            st.write("Diese Funktion ist noch nicht verfügbar.")

    with st.expander("Webeinstellungen"):
        st.write("Diese Funktion ist noch nicht verfügbar.")
        # Logo + Text
        # Image flip
        # etc.
        # Save to database?

        # Title
        st.write("Titel")
        # title = st.text_input("Titel", value=settings.get("title"), help="Titel der Webseite.")
        title = st.text_input("Titel", max_chars=50, help="Titel der Webseite.")
        description = st.text_area("Beschreibung", max_chars=1500, help="Beschreibung der Webseite.")

        # Save the settings
        col1, col2 = st.columns([5,1])
        if col2.button("Speichern"): # TODO
            st.write("Diese Funktion ist noch nicht verfügbar.", key="saveWebSettings")

# Display the dataframe
with st.expander("Measurements"):

    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No data available at the moment.", icon="📊")

    if "version" in df.columns:
        st.write(f"Firmware version: {df['version'].iloc[-1]}")

# Display error messages
with st.expander("Fehlermeldungen"):
    st.write("Diese Funktion ist noch nicht verfügbar.")
    # if not dfError.empty:
    #     # Display error message and timestamp as text in reverse order
    #     for index, row in dfError[::-1].iterrows():
    #         st.write(row['timestamp'].strftime(
    #             "%d.%m.%Y %H:%M:%S Uhr"), ": ", row['Error'])
    # else:
    #     st.write("Keine Fehlermeldungen vorhanden 🥳.")

    # Check if wittyPiDiagnostics.txt exists
    if "wittyPiDiagnostics.txt" in LOG_FILENAMEs:

        # Retrieve the file data
        fileserver.download_file("wittyPiDiagnostics.txt")

        # Get last modification date
        last_modified = fileserver.get_file_last_modified_date("wittyPiDiagnostics.txt")
        last_modified = timezone.localize(last_modified) # Convert date to local timezone

        with open('wittyPiDiagnostics.txt', encoding='utf-8') as file:
            # Download wittyPiDiagnostics.txt
            st.download_button(
                label="WittyPi Diagnostics herunterladen 📝",
                data=file,
                file_name="wittyPiDiagnostics.txt",
                mime="text/plain",
                use_container_width=True,
                help=f"Letzte Änderung: {last_modified.strftime('%d.%m.%Y %H:%M Uhr')}"
            )

    LOG_FILENAME = "log.txt"

    if LOG_FILENAME in LOG_FILENAMEs:

        # Retrieve the file data
        fileserver.download_file(LOG_FILENAME)

        # Get last modification date
        last_modified = fileserver.get_file_last_modified_date(LOG_FILENAME)
        last_modified = timezone.localize(last_modified) # Convert date to local timezone

        with open(LOG_FILENAME, encoding='utf-8') as file:
            # Download wittyPiDiagnostics.txt
            st.download_button(
                label="Logdateien herunterladen 📝",
                data=file,
                file_name=LOG_FILENAME,
                mime="text/plain",
                use_container_width=True,
                help=f"Letzte Änderung: {last_modified.strftime('%d.%m.%Y %H:%M Uhr')}"
            )

# fileserver.quit()
