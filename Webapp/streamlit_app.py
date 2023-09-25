# TODO Fix nächster Start in 23 Stunden und 59 Minuten.
# TODO Add settings after login
# TODO Timelapse and timestamp comparison

import streamlit as st
from ftplib import FTP
from io import BytesIO
from PIL import Image
import pandas as pd
from yaml import safe_load
from datetime import datetime
import altair as alt
import pytz
from suntime import Sun
# import geopy

# FTP server credentials
FTP_HOST = st.secrets["FTP_HOST"]
FTP_USERNAME = st.secrets["FTP_USERNAME"]
FTP_PASSWORD = st.secrets["FTP_PASSWORD"]

# Login status
if "userIsLoggedIn" not in st.session_state:
    st.session_state.userIsLoggedIn = False

timezone = pytz.timezone('Europe/Zurich')

# Streamlit app
def main():

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
    hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
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
    files = ftp.nlst()

    # Only show the image files
    files = [file for file in files if file.endswith(".jpg")]

    # Camera name
    cameraname = files[-1][14:-21]

    st.title(cameraname)

    # Placeholder for the image
    imagePlaceholder = st.empty()

    # Download diagnosticsf.csv as file with utf-8 encoding
    ftp.retrbinary('RETR diagnostics.csv', open('df.csv', 'wb').write)
    df = pd.read_csv('df.csv', encoding='utf-8')

    # TODO Improve naming
    df.rename(columns={df.columns[0]: 'Timestamp'}, inplace=True)
    df.rename(columns={df.columns[1]: 'Next Startup'}, inplace=True)
    df.rename(columns={df.columns[2]: 'Battery Voltage (V)'}, inplace=True)
    df.rename(columns={df.columns[3]: 'Internal Voltage (V)'}, inplace=True)
    df.rename(columns={df.columns[4]: 'Internal Current (A)'}, inplace=True)
    df.rename(columns={df.columns[5]: 'Temperature (°C)'}, inplace=True)
    df.rename(columns={df.columns[6]: 'Signal Quality (arb. units)'}, inplace=True)
    df.rename(columns={df.columns[7]: 'Latitude'}, inplace=True)
    df.rename(columns={df.columns[8]: 'Longitude'}, inplace=True)
    # df.rename(columns={df.columns[9]: 'Heigth'}, inplace=True)
    df.rename(columns={df.columns[9]: 'Error'}, inplace=True)

    # Modify the columns
    df['Battery Voltage (V)'] = df['Battery Voltage (V)'].str[:-1]
    df['Battery Voltage (V)'] = df['Battery Voltage (V)'].astype(float)
    df['Internal Voltage (V)'] = df['Internal Voltage (V)'].str[:-1]
    df['Internal Voltage (V)'] = df['Internal Voltage (V)'].astype(float)
    df['Temperature (°C)'] = df['Temperature (°C)'].str[:-2]
    df['Temperature (°C)'] = df['Temperature (°C)'].astype(float)
    
    try:
        df['Signal Quality (arb. units)'] = df['Signal Quality (arb. units)'].astype(int)
    except:
        # Remove all non numeric characters
        df['Signal Quality (arb. units)'] = df['Signal Quality (arb. units)'].str.replace(r'\D', '')
        # df['Signal Quality (arb. units)'] = df['Signal Quality (arb. units)'].astype(int)


    # Format timestamp
    df["Day"] = df["Timestamp"].str[:2]
    df["Month"] = df["Timestamp"].str[2:4]
    df["Year"] = df["Timestamp"].str[4:8]  
    df["Hour"] = df["Timestamp"].str[9:11]
    df["Minute"] = df["Timestamp"].str[11:13]

    df["Timestamp"] = pd.to_datetime(df[["Year", "Month", "Day", "Hour", "Minute"]])

    # Drop the columns
    df.drop(columns=["Day", "Month", "Year", "Hour", "Minute"], inplace=True)

    with st.sidebar:

        # Zeitraum auswählen
        st.header("Zeitraum auswählen")
        with st.expander("Zeitraum auswählen"):

            # Get the start and end date
            startDate = st.date_input("Startdatum", df['Timestamp'].iloc[0])
            endDate = st.date_input("Enddatum", df['Timestamp'].iloc[-1])

            # Get the start and end time
            startTime = st.time_input("Startzeit", datetime.strptime("00:00", "%H:%M").time())
            endTime = st.time_input("Endzeit", datetime.strptime("23:59", "%H:%M").time())

            # Combine the start and end date and time
            startDateTime = datetime.combine(startDate, startTime)
            endDateTime = datetime.combine(endDate, endTime)

            # Filter the dataframe
            df = df[(df['Timestamp'] >= startDateTime) & (df['Timestamp'] <= endDateTime)]
            
        # Login
        # TODO Improve security (e.g. multiple login attempts)
        st.header("Login")
        password = st.text_input("Bitte loggen Sie sich ein um die Einstellungen anzupassen.", type="password")
        if password == st.secrets["FTP_PASSWORD"]:
            
            st.success("Erfolgreich eingeloggt.")
            st.session_state.userIsLoggedIn = True
   
    # Select slider if multiple images are available
    if len(files) > 1:
        selected_file = st.select_slider(
            "Wähle ein Bild aus",
            label_visibility="hidden", # Hide the label
            options=files,
            value=files[-1],
            # Format the timestamp and dont show date if it is today
            format_func=lambda x: f"{x[9:11]}:{x[11:13]} Uhr" if x[:8] == datetime.now(timezone).strftime("%d%m%Y") else f"{x[:2]}.{x[2:4]}.{x[4:8]} {x[9:11]}:{x[11:13]} Uhr",
        )
    else:
        selected_file = files[0]

    # Get the image file from the FTP server
    image_data = BytesIO()
    ftp.retrbinary(f"RETR {selected_file}", image_data.write)
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

    # Overview of the last measurements
    # TODO Maybe add delta
    col1, col2, col3, col4 = st.columns(4)
    timestampSelectedImage = datetime.strptime(selected_file[0:13], '%d%m%Y_%H%M')
    index = df[df['Timestamp'] == timestampSelectedImage].index[0]

    delta = df['Battery Voltage (V)'].iloc[index] - df['Battery Voltage (V)'].iloc[index-1]
    col1.metric("Batterie", f"{df['Battery Voltage (V)'].iloc[index]}V")

    delta = df['Internal Voltage (V)'].iloc[index] - df['Internal Voltage (V)'].iloc[index-1]
    col2.metric("Interne Spannung", f"{df['Internal Voltage (V)'].iloc[index]}V", f"{delta}V")

    delta = df['Temperature (°C)'].iloc[index] - df['Temperature (°C)'].iloc[index-1]
    col3.metric("Temperatur", f"{df['Temperature (°C)'].iloc[index]}°C", f"{delta}°C")

    # delta = df['Signal Quality (arb. units)'].iloc[index] - df['Signal Quality (arb. units)'].iloc[index-1]
    col4.metric("Signalqualität", df['Signal Quality (arb. units)'].iloc[index], delta)

    st.write("")
    
    # Last startup relative to now
    # TODO Tage, Monate etc. anzeigen
    lastStartup = df['Timestamp'].iloc[-1]
    now = datetime.now(timezone).replace(tzinfo=None)
    timeDifference = now - lastStartup.replace(tzinfo=None)

    # Write difference in hours and minutes
    lastStartText = "Letzter Start vor "
    if timeDifference.seconds//3600 > 0:
        lastStartText = lastStartText + str(timeDifference.seconds//3600) + " Stunden und " + str((timeDifference.seconds//60)%60) + " Minuten"
    elif (timeDifference.seconds//60)%60 > 1:
        lastStartText = lastStartText + str((timeDifference.seconds//60)%60) + " Minuten"
    else:
        lastStartText = lastStartText + "weniger als eine Minute"

    # Print next startup relative to now
    nextStartup = df['Next Startup'].iloc[-1]
    nextStartup = datetime.strptime(nextStartup, '%Y-%m-%d %H:%M:%S')
    nextStartup = nextStartup + pd.Timedelta(minutes=1)
    timeDifference = nextStartup - now
    nextStartText = lastStartText + " - nächster Start in " 
    if timeDifference.seconds//3600 > 0:
        nextStartText = nextStartText + str(timeDifference.seconds//3600) + " Stunden und " + str((timeDifference.seconds//60)%60) + " Minuten."
    elif (timeDifference.seconds//60)%60 > 1:
        nextStartText = nextStartText + str((timeDifference.seconds//60)%60) + " Minuten."
    else:
        nextStartText = nextStartText + "weniger als einer Minute."
    st.write(nextStartText)

    st.divider()

    # If openweathermap API key is set in secrets.toml
    if st.secrets["OPENWEATHER_API_KEY"] != "":
        # Get the weather data from openweathermap
        import requests
        import json

        # Lat/lon = 46°51'55.8"N 9°32'32.3"E
        lat = 46.8655
        lon = 9.5423

        # Get the weather data
        base_url = "http://api.openweathermap.org/data/2.5/weather?"

        # Complete url
        complete_url = base_url + "appid=" + st.secrets["OPENWEATHER_API_KEY"] + "&lat=" + str(lat) + "&lon=" + str(lon) + "&units=metric&lang=de"

        # Get the response
        response = requests.get(complete_url)

        # Convert the response to json
        weather_data = response.json()

        if weather_data["cod"] != "404":

            # Convert temperature to celsius
            current_temperature = weather_data["main"]["temp"]
            current_pressure = weather_data["main"]["pressure"]
            current_humidity = weather_data["main"]["humidity"]

            # Get icon 
            icon = weather_data["weather"][0]["icon"]

            # Get the icon from openweathermap
            icon_url = f"http://openweathermap.org/img/wn/{icon}@2x.png"
            
            # Download the icon
            icon_data = BytesIO()
            icon_response = requests.get(icon_url)
            icon_data.write(icon_response.content)
            icon_image = Image.open(icon_data)

            # Description
            weather_description = weather_data["weather"][0]["description"]

            # Write header and location

            st.header("Wetter")
            st.caption(weather_description)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Temperatur", f"{current_temperature}°C")
            col2.metric("Luftdruck", f"{current_pressure}hPa")
            col3.metric("Luftfeuchtigkeit", f"{current_humidity}%")
            col4.image(icon_image)

            # Get location id
            location_id = weather_data["id"]

            st.markdown(f"Daten bereitgestellt von [OpenWeatherMap](https://openweathermap.org/city/{location_id}).")

            sun = Sun(lat, lon)
            today_sr = sun.get_local_sunrise_time().strftime('%H:%M')
            today_ss = sun.get_local_sunset_time().strftime('%H:%M')

            st.write(f"Sonnenaufgang: {today_sr} Uhr - Sonnenuntergang {today_ss} Uhr")
            
            st.divider()

    # Battery Voltage
    st.header("Batterie")
    st.write(f"Letzte Messung: {str(df['Battery Voltage (V)'].iloc[-1])}V")

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Battery Voltage:Q', axis=alt.Axis(title='Battery Voltage (V)')),
        tooltip=['Timestamp:T', 'Battery Voltage:Q']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    # Internal Voltage
    st.header("Interne Spannung")
    st.write(f"Letzte Messung: {str(df['Internal Voltage (V)'].iloc[-1])}V")

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Internal Voltage:Q', axis=alt.Axis(title='Internal Voltage (V)')),
        tooltip=['Timestamp:T', 'Internal Voltage:Q']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    # Temperature
    st.header("Temperatur")
    st.write(f"Letzte Messung: {str(df['Temperature (°C)'].iloc[-1])}°C")

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Temperature:Q', axis=alt.Axis(title='Temperature (°C)')),
        tooltip=['Timestamp:T', 'Temperature:Q']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    # Signal Quality
    # See: https://www.waveshare.com/w/upload/5/54/SIM7500_SIM7600_Series_AT_Command_Manual_V1.08.pdf
    st.header("Signalqualität")
    try:
        st.write(f"Letzte Messung: {str(df['Signal Quality (arb. units)'].iloc[-1].astype(str))}")
    except:
        st.write(f"Letzte Messung: {str(df['Signal Quality (arb. units)'].iloc[-1])}")


    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Signal Quality:Q', axis=alt.Axis(title='Signal Quality (arb. units)')),
        tooltip=['Timestamp:T', 'Signal Quality:Q']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)
   
    # Show a map with camera location
    st.header("Standort")

    # Remove rows with "-" as coordinates
    dfMap = df[df['Latitude'] != "-"]
    dfMap = dfMap[dfMap['Longitude'] != "-"]
    
    if dfMap.empty:
        st.write("Keine Koordinaten in diesem Zeitraum vorhanden.")
    else:
        # Convert the latitude and longitude to float
        last_latitude = float(dfMap['Latitude'].iloc[-1])
        last_longitude = float(dfMap['Longitude'].iloc[-1])
        
        # GeoPy mit Nominatim

        lat = "46.850000"
        lon = "10.075000"
        # geolocator = geopy.geocoders.Nominatim(user_agent="GlacierCam")
        # location = geolocator.reverse(f"{lat}, {lon}", language='de')
        # st.write(f"Standort: {location.address}")
            
        # Get country
        # country = location.raw['address']['country']
        
        st.map(pd.DataFrame({'lat': [last_latitude], 'lon': [last_longitude]}))

        # Print timestamp
        st.markdown(f"Letztes Update: {df['Timestamp'].iloc[-1].strftime('%d.%m.%Y %H:%M Uhr')} - [Google Maps](https://www.google.com/maps/search/?api=1&query={last_latitude},{last_longitude})" )

    # Add a linebreak
    st.write("")
    st.write("")

    # Display the dataframe
    with st.expander("Rohdaten"):

        st.dataframe(df)

        # Download diagnostics.csv
        st.download_button(
            label="Rohdaten herunterladen 📝",
            data=df.to_csv().encode("utf-8"),
            file_name="diagnostics.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Read settings.yaml and display it
    ftp.retrbinary('RETR settings.yaml', open('settings.yaml', 'wb').write)

    # Display the settings
    with st.expander("Einstellungen"):

        with open('settings.yaml') as file:
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

    # Edit the settings
    if st.session_state.userIsLoggedIn:
        with st.expander("Einstellungen anpassen"):

            st.write("Einstellungen anpassen")
            st.write("")
            st.write("Autofokus einstellen")
            autofocus = st.toggle("Autofokus", help="Aktiviert den automatischen Autofokus der Kamera. Kann deaktiviert werden um den Fokus manuell einzustellen.")
            
            if not autofocus:
                lensPosition = st.slider("Linsenposition", 0, 1023, 0)

            st.write("")
            timeSync = st.toggle("Zeitsynchronisation", help="Aktiviert die Zeitsynchronisation der Kamera.")
            enableGPS = st.toggle("GPS aktivieren", help="Aktiviert die GPS Funktion der Kamera.")
            shutdown = st.toggle("Shutdown", help="Kamera nach Bildaufnahme ausschalten.")
            
            # Zeitzone auswählen
            # TODO
            # st.header("Zeitzone auswählen")
            # timezone_selection = st.selectbox(
            #     "Bitte wählen Sie eine Zeitzone aus:",
            #     options=pytz.all_timezones,
            #     index=pytz.all_timezones.index('Europe/Zurich'),
            # )
            # timezone = pytz.timezone(timezone_selection)
       

    # Display the errors
    with st.expander("Fehlermeldungen"):
        # Display the errors (not nan)
        dfError = df[df['Error'].notna()]
        # Display error message and timestamp as text in reverse order
        for index, row in dfError[::-1].iterrows():
            st.write(row['Timestamp'].strftime("%d.%m.%Y %H:%M:%S Uhr"), ": ", row['Error'])

        # Easteregg button which lets it snow with snow emojis
        if st.button("❄️⛄"):
            st.snow()

# Run the app
if __name__ == "__main__":
    main()
    
