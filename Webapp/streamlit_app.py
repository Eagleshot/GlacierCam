"""Webserver for the Eagleshot GlacierCam - https://github.com/Eagleshot/GlacierCam"""
from ftplib import FTP
from io import BytesIO
from datetime import datetime
import streamlit as st
from PIL import Image
import pandas as pd
from yaml import safe_load
import altair as alt
import pytz
from suntime import Sun, SunTimeException
import requests

# FTP server credentials
FTP_HOST = st.secrets["FTP_HOST"]
FTP_USERNAME = st.secrets["FTP_USERNAME"]
FTP_PASSWORD = st.secrets["FTP_PASSWORD"]

# TODO: Latitude and longitude overwrite
location_overwrite = True
latitude = 46.87
longitude = 9.88
heigth = 1200

# Login status
if "userIsLoggedIn" not in st.session_state:
    st.session_state.userIsLoggedIn = False

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
with st.sidebar:

    # Select the camera if multiple cameras are available
    if len(st.secrets["FTP_FOLDER"]) > 1:
        st.header("Kamera auswählen")
        FTP_FOLDER = st.selectbox(
            "Bitte wählen Sie eine Kamera aus:",
            options=st.secrets["FTP_FOLDER"],
            index=0,
        )
    else:
        FTP_FOLDER = st.secrets["FTP_FOLDER"][0]

# Connect to the FTP server
ftp = FTP(FTP_HOST, FTP_USERNAME, FTP_PASSWORD)

# Change the working directory to the FTP folder
ftp.cwd(FTP_FOLDER)

# Get the list of files from the FTP server
ftp.cwd("save") # TODO Remove
files = ftp.nlst()
ftp.cwd("..") # TODO Remove

# Only show the image files
imgFiles = [file for file in files if file.endswith(".jpg")]

# Placeholder for the image
imagePlaceholder = st.empty()

@st.cache_data(show_spinner=False, ttl=60)
def getFileLastModifiedDate(filename: str) -> datetime:
    '''Get the last modification date of a file on the FTP server.'''
    last_modified = ftp.sendcmd(f"MDTM {filename}")
    last_modified = datetime.strptime(last_modified[4:], '%Y%m%d%H%M%S') # Convert last modification date to datetime
    last_modified = timezone.localize(last_modified) # Convert last modification date to local timezone

    return last_modified

@st.cache_data(show_spinner=False, ttl=60)
def get_file_ftp(filename: str) -> None:
    '''Download a file from the FTP server.'''
    # Retrieve the file data
    ftp.retrbinary(f"RETR {filename}", open(filename, 'wb').write)

# Get settings from server
get_file_ftp("settings.yaml")

with open('settings.yaml', encoding='utf-8') as file:
    settings = safe_load(file)


# Camera name
if "cameraName" in settings:
    cameraname = settings["cameraName"]
elif len(imgFiles) > 0:
    cameraname = imgFiles[-1][15:-21]
else:
    cameraname = FTP_FOLDER

st.title(cameraname, anchor=False)

# Camera ID
if len(imgFiles) > 0:
    camera_ID = imgFiles[-1][-20:-4]
else:
    camera_ID = "ERROR000000000"

# Download diagnostics file
get_file_ftp("diagnostics.csv")
df = pd.read_csv('diagnostics.csv', encoding='utf-8')

# Rename the columns
# TODO Also read first line
# TODO: Maybe do column naming in the main.py script
df.rename(columns={df.columns[0]: 'Timestamp'}, inplace=True)
df.rename(columns={df.columns[1]: 'Next Startup'}, inplace=True)
df.rename(columns={df.columns[2]: 'Battery Voltage (V)'}, inplace=True)
df.rename(columns={df.columns[3]: 'Internal Voltage (V)'}, inplace=True)
df.rename(columns={df.columns[4]: 'Internal Current (A)'}, inplace=True)
df.rename(columns={df.columns[5]: 'Temperature (°C)'}, inplace=True)
df.rename(columns={df.columns[6]: 'Signal Quality'}, inplace=True)
df.rename(columns={df.columns[7]: 'Latitude'}, inplace=True)
df.rename(columns={df.columns[8]: 'Longitude'}, inplace=True)
df.rename(columns={df.columns[9]: 'Heigth'}, inplace=True)
df.rename(columns={df.columns[10]: 'Error'}, inplace=True)

# Convert the timestamp to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d %H:%M:%SZ')


##############################################
# Sidebar
##############################################

with st.sidebar:

    # Zeitraum auswählen
    st.header("Zeitraum auswählen")
    with st.expander("Zeitraum auswählen"):

        # Get the start and end date
        startDate = st.date_input("Startdatum", df['Timestamp'].iloc[0])
        endDate = st.date_input("Enddatum", df['Timestamp'].iloc[-1])

        # Get the start and end time
        startTime = st.time_input(
            "Startzeit", datetime.strptime("00:00", "%H:%M").time())
        endTime = st.time_input(
            "Endzeit", datetime.strptime("23:59", "%H:%M").time())

        # Combine the start and end date and time
        startDateTime = datetime.combine(startDate, startTime)
        endDateTime = datetime.combine(endDate, endTime)

        # Check if the start date is before the end date
        if startDateTime >= endDateTime:
            st.error("Das Enddatum muss nach dem Startdatum liegen.")
        else:
            # Filter the dataframe
            df = df[(df['Timestamp'] >= startDateTime)
                    & (df['Timestamp'] <= endDateTime)]

    # Zeitzone auswählen
    # TODO
    st.header("Zeitzone auswählen", help="Zeitzone der Kamera auswählen.")
    timezone_selection = st.selectbox(
        "Bitte wählen Sie eine Zeitzone aus:",
        options=pytz.all_timezones,
        index=pytz.all_timezones.index('Europe/Zurich'),
    )
    timezone = pytz.timezone(timezone_selection)

    # Login
    # TODO Improve security (e.g. multiple login attempts)
    st.header("Login")
    password = st.text_input("Bitte loggen Sie sich ein um die Einstellungen anzupassen.",
                                placeholder="Passwort eingeben", type="password")
    if password == st.secrets["FTP_PASSWORD"]:

        st.success("Erfolgreich eingeloggt.")
        st.session_state.userIsLoggedIn = True

# Select slider if multiple images are available
if len(imgFiles) > 1:
    selected_file = st.select_slider(
        "Wähle ein Bild aus",
        label_visibility="hidden",  # Hide the label
        options=imgFiles,
        value=imgFiles[-1],
        # Format the timestamp and dont show date if it is today
        format_func=lambda x: f"{x[9:11]}:{x[11:13]} Uhr" if x[:8] == datetime.now(
        timezone).strftime("%Y%m%d") else f"{x[:4]}.{x[4:6]}.{x[6:8]} {x[9:11]}:{x[11:13]} Uhr"
    )
elif len(imgFiles) == 1:
    selected_file = imgFiles[0]
else:
    st.write("Keine Bilder vorhanden.")

@st.cache_data(show_spinner=False, ttl=3600)
def get_image_ftp(selected_file):
    '''Get an image from the FTP server'''
    image_data = BytesIO() 
    ftp.cwd("save") # TODO Cleanup
    ftp.retrbinary(f"RETR {selected_file}", image_data.write)
    ftp.cwd("..") # TODO Cleanup
    image = Image.open(image_data)

    # Rotate the image
    # image = image.rotate(180, expand=True)

    return image_data, image

# Get the image file from the FTP server
if len(files) > 0:
    image_data, image = get_image_ftp(selected_file)

    # Display the image with the corresponding timestamp
    imagePlaceholder.image(image, use_column_width=True)

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

col1, col2, col3, col4 = st.columns(4)

try:
    timestampSelectedImage = datetime.strptime(
        selected_file[0:13], '%d%m%Y_%H%M')
    df['Timestamp'] = df['Timestamp'].dt.floor(
        'min')  # Remove seconds from timestamp
    index = df[df['Timestamp'] == timestampSelectedImage].index[0]
except:
    index = -1

col1.metric("Batterie", f"{df['Battery Voltage (V)'].iloc[index]} V")
col2.metric("Interne Spannung",
            f"{df['Internal Voltage (V)'].iloc[index]} V")
col3.metric("Temperatur", f"{df['Temperature (°C)'].iloc[index]} °C")
col4.metric("Signalqualität", df['Signal Quality'].iloc[index])

st.write("")

##############################################
# Next and last startup
##############################################

# Last startup relative to now
lastStartup = df['Timestamp'].iloc[-1]
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
nextStartup = df['Next Startup'].iloc[-1]
nextStartup = datetime.strptime(nextStartup, '%Y-%m-%d %H:%M:%S')
nextStartup = nextStartup + pd.Timedelta(minutes=1)

# Check if next startup is in the future
if nextStartup < now:
    next_last_startup_text += "."
else:
    timeDifference = nextStartup - now
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

# Overwrite latitude and longitude if available
if location_overwrite:
    df['Latitude'] = latitude
    df['Longitude'] = longitude
    df['Heigth'] = heigth

dfMap = df[df['Latitude'] != "-"]
dfMap = dfMap[dfMap['Longitude'] != "-"]

@st.cache_data(show_spinner=False, ttl=300)
def get_weather_data(latitude: float, longitude: float) -> dict:
    '''Get weather data from OpenWeatherMap.'''
    # Get weather data from OpenWeatherMap
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{BASE_URL}appid={st.secrets['OPENWEATHER_API_KEY']}&lat={latitude}&lon={longitude}&units=metric&lang=de"
    response = requests.get(complete_url, timeout=5)

    # Convert the response to json
    weather_data = response.json()

    return weather_data

# Check if OpenWeather API key is set and location is available
if st.secrets["OPENWEATHER_API_KEY"] != "" and not dfMap.empty:

    latitude = float(dfMap['Latitude'].iloc[-1])
    longitude = float(dfMap['Longitude'].iloc[-1])

    # Get weather data from OpenWeatherMap
    weather_data = get_weather_data(latitude, longitude)

    if weather_data["cod"] == 200:

        # Convert temperature to celsius
        current_temperature = int(weather_data["main"]["temp"])
        current_pressure = weather_data["main"]["pressure"]
        current_humidity = weather_data["main"]["humidity"]

        # Wind speed and direction
        wind_speed = round(weather_data["wind"]["speed"], 1)
        wind_direction = weather_data["wind"]["deg"]

        # Convert wind direction to text
        if wind_direction > 337.5:
            WIND_DIRECTION_TEXT = "N"
        elif wind_direction > 292.5:
            WIND_DIRECTION_TEXT = "NW"
        elif wind_direction > 247.5:
            WIND_DIRECTION_TEXT = "W"
        elif wind_direction > 202.5:
            WIND_DIRECTION_TEXT = "SW"
        elif wind_direction > 157.5:
            WIND_DIRECTION_TEXT = "S"
        elif wind_direction > 122.5:
            WIND_DIRECTION_TEXT = "SE"
        elif wind_direction > 67.5:
            WIND_DIRECTION_TEXT = "E"
        elif wind_direction > 22.5:
            WIND_DIRECTION_TEXT = "NE"
        else:
            WIND_DIRECTION_TEXT = "N"

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

        col1.header("Wetter", anchor=False)
        # col1.caption(f"{name}, {country}")
        col1.text("")
        col1.markdown(f"### :grey[Temperatur: {current_temperature} °C]")
        col2.text("")
        col2.text("")
        col2.text("")
        col2.text("")
        col2.image(icon_image, caption=weather_description)
        st.text("")

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        col1.metric("Wind", f"{wind_speed} m/s",
                    delta=WIND_DIRECTION_TEXT, delta_color="off")
        col2.metric("Luftdruck", f"{current_pressure} hPa")
        col3.metric("Luftfeuchtigkeit", f"{current_humidity} %")
        col4.metric("Sichtweite", f"{visibility}")

        st.text("")
        st.markdown(
            "Daten von [OpenWeatherMap](https://openweathermap.org).")

        st.divider()

##############################################
# Sunrise and sunset
##############################################

try:
    if not dfMap.empty:
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

except SunTimeException as e:
    print(f"Error with SunTime: {e}")

##############################################
# Charts
##############################################

# Battery Voltage
st.header("Batterie", anchor=False)
st.write(f"Letzte Messung: {str(df['Battery Voltage (V)'].iloc[-1])} V")

chart = alt.Chart(df).mark_line().encode(
    x=alt.X('Timestamp:T', axis=alt.Axis(
        title='Timestamp', labelAngle=-45)),
    y=alt.Y('Battery Voltage (V):Q', axis=alt.Axis(
        title='Battery Voltage (V)')),
    tooltip=['Timestamp:T', 'Battery Voltage:Q']
).interactive()
st.altair_chart(chart, use_container_width=True)

# Internal Voltage
st.header("Interne Spannung", anchor=False)
st.write(f"Letzte Messung: {str(df['Internal Voltage (V)'].iloc[-1])} V")

chart = alt.Chart(df).mark_line().encode(
    x=alt.X('Timestamp:T', axis=alt.Axis(
        title='Timestamp', labelAngle=-45)),
    y=alt.Y('Internal Voltage (V):Q', axis=alt.Axis(
        title='Internal Voltage (V)')),
    tooltip=['Timestamp:T', 'Internal Voltage:Q']
).interactive()
st.altair_chart(chart, use_container_width=True)

# Temperature
st.header("Temperatur", anchor=False)
st.write(f"Letzte Messung: {str(df['Temperature (°C)'].iloc[-1])} °C")

chart = alt.Chart(df).mark_line().encode(
    x=alt.X('Timestamp:T', axis=alt.Axis(
        title='Timestamp', labelAngle=-45)),
    y=alt.Y('Temperature (°C):Q', axis=alt.Axis(title='Temperature (°C)')),
    tooltip=['Timestamp:T', 'Temperature:Q']
).interactive()
st.altair_chart(chart, use_container_width=True)

# Signal Quality
# See: https://www.waveshare.com/w/upload/5/54/SIM7500_SIM7600_Series_AT_Command_Manual_V1.08.pdf
st.header("Signalqualität", anchor=False)
st.write(f"Letzte Messung: {str(df['Signal Quality'].iloc[-1])}")

chart = alt.Chart(df).mark_line().encode(
    x=alt.X('Timestamp:T', axis=alt.Axis(
        title='Timestamp', labelAngle=-45)),
    y=alt.Y('Signal Quality:Q', axis=alt.Axis(title='Signal Quality')),
    tooltip=['Timestamp:T', 'Signal Quality:Q']
).interactive()
st.altair_chart(chart, use_container_width=True)

##############################################
# Map
##############################################

if not dfMap.empty:

    st.header("Standort", anchor=False)
    st.map(pd.DataFrame({'lat': [latitude], 'lon': [longitude]}))

    # Print coordinates
    st.write(
        f"Breitengrad: {latitude}, Längengrad: {longitude}, Höhe: {dfMap['Heigth'].iloc[-1]} m. ü. M. - [Google Maps](https://www.google.com/maps/search/?api=1&query={latitude},{longitude})")

    # Print timestamp
    if not location_overwrite:
        st.markdown(
            f"Letztes Standortupdate: {df['Timestamp'].iloc[-1].strftime('%d.%m.%Y %H:%M Uhr')}")

# Add a linebreak
st.write("")
st.write("")

##############################################
# Settings and diagnostics
##############################################

# Read settings.yaml and display it
# TODO Settings (incl. validation)
if True: # st.session_state.userIsLoggedIn:
    with st.expander("Kameraeinstellungen"):

        st.write("Kamera")

        autofocus_ON = False
        if settings["lensPosition"] == -1:
            autofocus_ON = True

        col1, col2 = st.columns([3,1])
        
        # Focus range slider from 0m to inf
        col2.write("")
        col2.write("")
        autofocus_ON = col2.toggle(
            "Autofokus", value=autofocus_ON, help="Aktiviert den automatischen Autofokus der Kamera oder kann deaktiviert werden um den Fokus manuell zwischen 0.1m und ∞ einzustellen.")

        focus = col1.slider(
            "Manueller Fokus", min_value=0, max_value=100, value=0, step=1, disabled=autofocus_ON, format="%d m")
        

        # Resolution
        # TODO
        resolution = st.selectbox(
            "Auflösung", options=["Automatisch", "2592x1944", "1920x1080", "1280x720", "640x480"], index=0, help="Bildauflösung der Kamera.")
        
        st.divider()
        st.write("Zeit")
        col1, col2 = st.columns(2)

        # Start time
        startTime = col1.time_input('Startzeit', datetime.strptime(f"{settings['startTimeHour']}:{settings['startTimeMinute']}", "%H:%M").time(), help="Startzeit der Aufnahme.")
     
        # Interval
        intervalTime = col2.number_input("Aufnahmeintervall", min_value=5, max_value=720, value=settings['intervalMinutes'], step=5, help="Aufnahmeintervall in Minuten.")

        # Repetitions per day
        repetitionsPerday = col1.number_input("Aufnahmen pro Tag", min_value=1, max_value=100, value=settings['repetitionsPerday'], step=1, help="Anzahl Aufnahmen pro Tag.")
        # Duration
        durationTime = col2.number_input("Max. Aufnahmedauer", min_value=1, max_value=10, value=settings['maxDurationMinute'], step=1, help="Maximale Aufnahmedauer in Minuten. Das Kamerasystem wird spätestens nach dieser Zeitdauer ausgeschaltet.")
        timeSync = st.toggle(
            "Zeitsynchronisation", value=settings["timeSync"], help="Aktiviert die automatische Zeitsynchronisation der Kamera mit dem Internet.")
        
        st.divider()
        st.write("Weitere Einstellungen")
        enableGPS = st.toggle("GPS aktivieren", value = settings["enableGPS"],
             help="Aktiviert die GPS-Funktion der Kamera. Die GPS-Antenne muss dafür angeschlossen sein!")
        extendedDiagnostics = st.toggle(
            "Erweiterte Diagnosedaten", value=settings["uploadWittyPiDiagnostics"], help="Hochladen von erweiterten Diagnosedaten. Kann bei schwerwiegenderen Problemen helfen.")
        
        st.divider()
        st.write(":red[Danger Zone]")
        shutdown = st.toggle("Shutdown", value=settings["shutdown"], help="Kamera nach Bildaufnahme ausschalten. Wird diese Option deaktiviert, schaltet sich die Kamera erst verspätet aus und der Stromverbrauch ist erhöht.")

        # Save the settings
        col1, col2 = st.columns([5,1])
        if col2.button("Speichern", key="saveCameraSettings"):
            # TODO: Save settings
            st.write("Diese Funktion ist noch nicht verfügbar.")

    with st.expander("Webeinstellungen"):
        st.write("Diese Funktion ist noch nicht verfügbar.")
        # Logo + Text
        # Image flip
        # etc.
        # Save to database?

        # Title
        st.write("Titel")
        # title = st.text_input("Titel", value=settings["title"], help="Titel der Webseite.")
        title = st.text_input("Titel", max_chars=50, help="Titel der Webseite.")
        description = st.text_area("Beschreibung", max_chars=1500, help="Beschreibung der Webseite.")

        # Save the settings
        col1, col2 = st.columns([5,1])
        if col2.button("Speichern"):
            # TODO: Save settings
            st.write("Diese Funktion ist noch nicht verfügbar.", key="saveWebSettings")

    # Display the dataframe
    with st.expander("Diagnosedaten"):

        st.dataframe(df)

        # Check if wittyPiDiagnostics.txt exists
        if "wittyPiDiagnostics.txt" in files:

            # Retrieve the file data
            ftp.retrbinary("RETR wittyPiDiagnostics.txt", open('wittyPiDiagnostics.txt', 'wb').write)

            # Get last modification date
            lastModified = getFileLastModifiedDate("wittyPiDiagnostics.txt")

            with open('wittyPiDiagnostics.txt', encoding='utf-8') as file:
                # Download wittyPiDiagnostics.txt
                st.download_button(
                    label="WittyPi Diagnostics herunterladen 📝",
                    data=file,
                    file_name="wittyPiDiagnostics.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help=f"Letzte Änderung: {lastModified.strftime('%d.%m.%Y %H:%M Uhr')}"
                )

        # Check if wittyPiSchedule.txt exists
        if "wittyPiSchedule.txt" in files:
            
            # Retrieve the file data
            ftp.retrbinary("RETR wittyPiSchedule.txt", open('wittyPiSchedule.txt', 'wb').write)

            # Get last modification date
            lastModified = getFileLastModifiedDate("wittyPiSchedule.txt")

            with open('wittyPiSchedule.txt', encoding='utf-8') as file:
                # Download wittyPiSchedule.txt
                st.download_button(
                    label="WittyPi Schedule herunterladen 📝",
                    data=file,
                    file_name="wittyPiSchedule.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help=f"Letzte Änderung: {lastModified.strftime('%d.%m.%Y %H:%M Uhr')}"
                )

        st.write("")
        st.write(f"Kamera ID: {camera_ID}")

    # Display the errors
    with st.expander("Fehlermeldungen"):
        # Display the errors (not nan)
        dfError = df[df['Error'].notna()]

        if not dfError.empty:
            # Display error message and timestamp as text in reverse order
            for index, row in dfError[::-1].iterrows():
                st.write(row['Timestamp'].strftime(
                    "%d.%m.%Y %H:%M:%S Uhr"), ": ", row['Error'])
        else:
            st.write("Keine Fehlermeldungen vorhanden 🥳.")
