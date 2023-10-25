from ftplib import FTP
from io import BytesIO
from datetime import datetime
import streamlit as st
from PIL import Image
import pandas as pd
from yaml import safe_load
import altair as alt
import pytz
from suntime import Sun
import requests

# FTP server credentials
FTP_HOST = st.secrets["FTP_HOST"]
FTP_USERNAME = st.secrets["FTP_USERNAME"]
FTP_PASSWORD = st.secrets["FTP_PASSWORD"]

# Login status
if "userIsLoggedIn" not in st.session_state:
    st.session_state.userIsLoggedIn = False

timezone = pytz.timezone('Europe/Zurich')

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

# Hide footer and menu
# See: https://discuss.streamlit.io/t/remove-made-with-streamlit-from-bottom-of-app/1370/2
hide_streamlit_style = """<style>footer {visibility: hidden;}</style>"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Change the camera selection
with st.sidebar:

    st.header("Kamera auswählen")
    FTP_FOLDER = st.selectbox(
        "Bitte wählen Sie eine Kamera aus:",
        options=st.secrets["FTP_FOLDER"],
        index=0,
    )

# Connect to the FTP server
ftp = FTP(FTP_HOST)
ftp.login(user=FTP_USERNAME, passwd=FTP_PASSWORD)

# Change the working directory to the FTP folder
ftp.cwd(FTP_FOLDER)

# Get the list of files from the FTP server
# TODO Remove
ftp.cwd("save")
files = ftp.nlst()
ftp.cwd("..")

# Only show the image files
files = [file for file in files if file.endswith(".jpg")]

# Camera name
if len(files) > 0:
    cameraname = files[-1][14:-21]
else:
    cameraname = FTP_FOLDER

st.title(cameraname, anchor=False)

# Placeholder for the image
imagePlaceholder = st.empty()

# Download diagnostics.csv as file with utf-8 encoding
# TODO Also read first line
ftp.retrbinary('RETR diagnostics.csv', open('df.csv', 'wb').write)
df = pd.read_csv('df.csv', encoding='utf-8')

# Rename the columns
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
df['Timestamp'] = pd.to_datetime(
df['Timestamp'], format='%Y-%m-%d %H:%M:%S')

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

        # Filter the dataframe
        df = df[(df['Timestamp'] >= startDateTime)
                & (df['Timestamp'] <= endDateTime)]

    # Login
    # TODO Improve security (e.g. multiple login attempts)
    st.header("Login")
    password = st.text_input("Bitte loggen Sie sich ein um die Einstellungen anzupassen.",
                                placeholder="Passwort eingeben", type="password")
    if password == st.secrets["FTP_PASSWORD"]:

        st.success("Erfolgreich eingeloggt.")
        st.session_state.userIsLoggedIn = True

# Select slider if multiple images are available
if len(files) > 1:
    selected_file = st.select_slider(
        "Wähle ein Bild aus",
        label_visibility="hidden",  # Hide the label
        options=files,
        value=files[-1],
        # Format the timestamp and dont show date if it is today
        format_func=lambda x: f"{x[9:11]}:{x[11:13]} Uhr" if x[:8] == datetime.now(
            timezone).strftime("%d%m%Y") else f"{x[:2]}.{x[2:4]}.{x[4:8]} {x[9:11]}:{x[11:13]} Uhr",
    )
elif len(files) == 1:
    selected_file = files[0]
else:
    st.write("Keine Bilder vorhanden.")

# Get the image file from the FTP server
if len(files) > 0:
    image_data = BytesIO()
    ftp.cwd("save")
    ftp.retrbinary(f"RETR {selected_file}", image_data.write)
    ftp.cwd("..")
    image = Image.open(image_data)

    # Rotate the image
    image = image.rotate(180, expand=True)

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

# TODO Maybe add delta
col1, col2, col3, col4 = st.columns(4)

try:
    timestampSelectedImage = datetime.strptime(
        selected_file[0:13], '%d%m%Y_%H%M')
    df['Timestamp'] = df['Timestamp'].dt.floor(
        'min')  # Remove seconds from timestamp
    index = df[df['Timestamp'] == timestampSelectedImage].index[0]
except:
    index = -1

col1.metric("Batterie", f"{df['Battery Voltage (V)'].iloc[index]}V")
col2.metric("Interne Spannung",
            f"{df['Internal Voltage (V)'].iloc[index]}V")
col3.metric("Temperatur", f"{df['Temperature (°C)'].iloc[index]}°C")
col4.metric("Signalqualität", df['Signal Quality'].iloc[index])

st.write("")

##############################################
# Next and last startup
##############################################

# Last startup relative to now
lastStartup = df['Timestamp'].iloc[-1]
now = datetime.now(timezone).replace(tzinfo=None)
timeDifference = now - lastStartup.replace(tzinfo=None)

# Write difference in hours and minutes
nextLastStartupText = "Letzter Start vor "

if timeDifference.days > 1:
    nextLastStartupText = nextLastStartupText + \
        str(timeDifference.days) + " Tagen, "
elif timeDifference.days == 1:
    nextLastStartupText = nextLastStartupText + \
        str(timeDifference.days) + " Tag, "

if timeDifference.seconds//3600 > 0:
    nextLastStartupText = nextLastStartupText + \
        str(timeDifference.seconds//3600) + " Stunden und "

if (timeDifference.seconds//60) % 60 > 1:
    nextLastStartupText = nextLastStartupText + \
        str((timeDifference.seconds//60) % 60) + " Minuten"
else:
    nextLastStartupText = nextLastStartupText + "weniger als eine Minute"

# Print next startup relative to now
nextStartup = df['Next Startup'].iloc[-1]
nextStartup = datetime.strptime(nextStartup, '%Y-%m-%d %H:%M:%S')
nextStartup = nextStartup + pd.Timedelta(minutes=1)

# Check if next startup is in the future
if nextStartup < now:
    nextLastStartupText += "."
else:
    timeDifference = nextStartup - now
    nextLastStartupText = nextLastStartupText + " - nächster Start in "
    if timeDifference.seconds//3600 > 0:
        nextLastStartupText = nextLastStartupText + \
            str(timeDifference.seconds//3600) + " Stunden und " + \
            str((timeDifference.seconds//60) % 60) + " Minuten."
    elif (timeDifference.seconds//60) % 60 > 1:
        nextLastStartupText = nextLastStartupText + \
            str((timeDifference.seconds//60) % 60) + " Minuten."
    else:
        nextLastStartupText = nextLastStartupText + "weniger als einer Minute."

st.write(nextLastStartupText)

st.divider()

##############################################
# Weather widget
##############################################

dfMap = df[df['Latitude'] != "-"]
dfMap = dfMap[dfMap['Longitude'] != "-"]

# Get the latitude and longitude
lon = float(dfMap['Latitude'].iloc[-1])
lat = float(dfMap['Longitude'].iloc[-1])

# Check if OpenWeather API key is set
if st.secrets["OPENWEATHER_API_KEY"] != "":

    # # Reverse geocoding with OpenWeatherMap
    # base_url = "http://api.openweathermap.org/geo/1.0/reverse?"

    # complete_url = base_url + "lat=" + str(lat) + "&lon=" + str(lon) + "&limit=1&appid=" + st.secrets["OPENWEATHER_API_KEY"]

    # # Get the response
    # response = requests.get(complete_url)

    # # Convert the response to json
    # reverse_geocoding_data = response.json()

    # location_name = reverse_geocoding_data[0]["name"]
    # country = reverse_geocoding_data[0]["country"]

    # Get weather data from OpenWeatherMap
    base_url = "http://api.openweathermap.org/data/2.5/weather?"

    complete_url = base_url + "appid=" + \
        st.secrets["OPENWEATHER_API_KEY"] + "&lat=" + \
        str(lat) + "&lon=" + str(lon) + "&units=metric&lang=de"

    # Get the response
    response = requests.get(complete_url, timeout=5)

    # Convert the response to json
    weather_data = response.json()

    if weather_data["cod"] == 200:

        # Convert temperature to celsius
        current_temperature = int(weather_data["main"]["temp"])
        current_pressure = weather_data["main"]["pressure"]
        current_humidity = weather_data["main"]["humidity"]

        # Wind speed and direction
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
            visibility = f"{visibility}m"
        else:
            visibility = f"{int(visibility/1000)}km"

        col1, col2 = st.columns([1.5, 1])

        col1.header("Wetter", anchor=False)
        # col1.caption(f"{name}, {country}")
        col1.text("")
        col1.markdown(f"### :grey[Temperatur: {current_temperature}°C]")
        col2.text("")
        col2.text("")
        col2.text("")
        col2.text("")
        col2.image(icon_image, caption=weather_description)

        st.text("")

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        col1.metric("Wind", f"{wind_speed}m/s",
                    delta=wind_direction_text, delta_color="off")
        col2.metric("Luftdruck", f"{current_pressure}hPa")
        col3.metric("Luftfeuchtigkeit", f"{current_humidity}%")
        col4.metric("Sichtweite", f"{visibility}")

        st.text("")
        st.markdown(
            "Daten von [OpenWeatherMap](https://openweathermap.org).")

        st.divider()

##############################################
# Sunrise and sunset
##############################################

try:
    sun = Sun(lat, lon)
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

except:
    pass

##############################################
# Charts
##############################################

# Battery Voltage
st.header("Batterie", anchor=False)
st.write(f"Letzte Messung: {str(df['Battery Voltage (V)'].iloc[-1])}V")

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
st.write(f"Letzte Messung: {str(df['Internal Voltage (V)'].iloc[-1])}V")

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
st.write(f"Letzte Messung: {str(df['Temperature (°C)'].iloc[-1])}°C")

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

st.header("Standort", anchor=False)

# Remove rows with no coordinates
dfMap = df[df['Latitude'] != "-"]
dfMap = dfMap[dfMap['Longitude'] != "-"]

if dfMap.empty:
    st.write("Keine Koordinaten in diesem Zeitraum vorhanden.")
else:
    # Convert the latitude and longitude to float
    # TODO Latitude and longitude are switched in camera
    last_latitude = float(dfMap['Longitude'].iloc[-1])
    last_longitude = float(dfMap['Latitude'].iloc[-1])

    st.map(pd.DataFrame({'lat': [last_latitude], 'lon': [last_longitude]}))

    # Print coordinates
    st.write(
        f"Breitengrad: {last_latitude}, Längengrad: {last_longitude}, Höhe: {dfMap['Heigth'].iloc[-1]}m - [Google Maps](https://www.google.com/maps/search/?api=1&query={last_latitude},{last_longitude})")

    # Print timestamp
    st.markdown(
        f"Letztes Standortupdate: {df['Timestamp'].iloc[-1].strftime('%d.%m.%Y %H:%M Uhr')}")

# Add a linebreak
st.write("")
st.write("")


# Read settings.yaml and display it
ftp.retrbinary('RETR settings.yaml', open('settings.yaml', 'wb').write)

# Display the settings
with st.expander("Einstellungen"):

    with open('settings.yaml', encoding='utf-8') as file:
        settings = safe_load(file)

    # Display the settings
    st.write(settings)

# settings.yaml
# {
#     "lensPosition": 0
#     "resolution": [
#         0:
#         0
#         1:
#         0
#     ]
#     "startTimeHour": 6
#     "startTimeMinute": 0
#     "intervalMinutes": 10
#     "maxDurationMinute": 5
#     "repetitionsPerday": 96
#     "timeSync": false
#     "enableGPS": false
#     "shutdown": true
# }

# TODO Settings
if st.session_state.userIsLoggedIn:
    with st.expander("Einstellungen anpassen"):

        st.write("Einstellungen anpassen")
        st.write("")
        st.write("Autofokus einstellen")
        autofocus = st.toggle(
            "Autofokus", help="Aktiviert den automatischen Autofokus der Kamera. Kann deaktiviert werden um den Fokus manuell einzustellen.")

        if not autofocus:
            lensPosition = st.slider("Linsenposition", 0, 1023, 0)

        st.write("")
        timeSync = st.toggle(
            "Zeitsynchronisation", help="Aktiviert die Zeitsynchronisation der Kamera.")
        enableGPS = st.toggle(
            "GPS aktivieren", help="Aktiviert die GPS Funktion der Kamera.")
        shutdown = st.toggle(
            "Shutdown", help="Kamera nach Bildaufnahme ausschalten.")

        # Zeitzone auswählen
        st.header("Zeitzone auswählen")
        timezone_selection = st.selectbox(
            "Bitte wählen Sie eine Zeitzone aus:",
            options=pytz.all_timezones,
            index=pytz.all_timezones.index('Europe/Zurich'),
        )
        # timezone = pytz.timezone(timezone_selection)

# Display the dataframe
with st.expander("Diagnosedaten"):

    st.dataframe(df)

    # Download diagnostics.csv
    st.download_button(
        label="Rohdaten herunterladen 📝",
        data=df.to_csv().encode("utf-8"),
        file_name="diagnostics.csv",
        mime="text/csv",
        use_container_width=True
    )

    # files = ftp.nlst()

    # # Check if wittyPiDiagnostics.txt exists
    # if "wittyPiDiagnostics.txt" in files:

    #     # Retrieve the file data
    #     ftp.retrbinary("RETR wittyPiDiagnostics.txt", open('wittyPiDiagnostics.txt', 'wb').write)

    #     # Get last modification date
    #     lastModified = ftp.sendcmd("MDTM wittyPiDiagnostics.txt")
    #     lastModified = datetime.strptime(lastModified[4:], '%Y%m%d%H%M%S') # Convert last modification date to datetime
    #     lastModified = timezone.localize(lastModified) # Convert last modification date to local timezone

    #     with open('wittyPiDiagnostics.txt', encoding='utf-8') as file:
    #         # Download wittyPiDiagnostics.txt
    #         st.download_button(
    #             label="WittyPi Diagnostics herunterladen 📝",
    #             data=file,
    #             file_name="wittyPiDiagnostics.txt",
    #             mime="text/plain",
    #             use_container_width=True,
    #             help=f"Letzte Änderung: {lastModified.strftime('%d.%m.%Y %H:%M Uhr')}"
    #         )

    # # Check if wittyPiSchedule.txt exists
    # if "wittyPiSchedule.txt" in files:
        
    #     # Retrieve the file data
    #     ftp.retrbinary("RETR wittyPiSchedule.txt", open('wittyPiSchedule.txt', 'wb').write)

    #     # Get last modification date
    #     lastModified = ftp.sendcmd("MDTM wittyPiSchedule.txt")
    #     lastModified = datetime.strptime(lastModified[4:], '%Y%m%d%H%M%S') # Convert last modification date to datetime
    #     lastModified = timezone.localize(lastModified) # Convert last modification date to local timezone

    #     with open('wittyPiSchedule.txt', encoding='utf-8') as file:
    #         # Download wittyPiSchedule.txt
    #         st.download_button(
    #             label="WittyPi Schedule herunterladen 📝",
    #             data=file,
    #             file_name="wittyPiSchedule.txt",
    #             mime="text/plain",
    #             use_container_width=True,
    #             help=f"Letzte Änderung: {lastModified.strftime('%d.%m.%Y %H:%M Uhr')}"
    #         )

# Display the errors
with st.expander("Fehlermeldungen"):
    # Display the errors (not nan)
    dfError = df[df['Error'].notna()]
    # Display error message and timestamp as text in reverse order
    for index, row in dfError[::-1].iterrows():
        st.write(row['Timestamp'].strftime(
            "%d.%m.%Y %H:%M:%S Uhr"), ": ", row['Error'])

    # Easteregg button which lets it snow with snow emojis
    if st.button("❄️⛄"):
        st.snow()
