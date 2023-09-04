import streamlit as st
from ftplib import FTP
from io import BytesIO
from PIL import Image
import pandas as pd
from yaml import safe_load
from datetime import datetime
import altair as alt
import pytz

# FTP server credentials
FTP_HOST = st.secrets["FTP_HOST"]
FTP_USERNAME = st.secrets["FTP_USERNAME"]
FTP_PASSWORD = st.secrets["FTP_PASSWORD"]

# Streamlit app
def main():

    # Set page title and favicon
    st.set_page_config(
        page_title="GlacierCam",
        page_icon="🏔️"
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

    # Title
    st.title("GlacierCam")

    # Placeholder for the image
    imagePlaceholder = st.empty()

    # Download diagnosticsf.csv as file with utf-8 encoding
    ftp.retrbinary('RETR diagnostics.csv', open('df.csv', 'wb').write)
    df = pd.read_csv('df.csv', encoding='utf-8')

    # TODO Improve naming
    df.rename(columns={df.columns[0]: 'Timestamp'}, inplace=True)
    df.rename(columns={df.columns[1]: 'Next Startup'}, inplace=True)
    df.rename(columns={df.columns[2]: 'Battery Voltage'}, inplace=True)
    df.rename(columns={df.columns[3]: 'Internal Voltage'}, inplace=True)
    df.rename(columns={df.columns[4]: 'Internal Current'}, inplace=True)
    df.rename(columns={df.columns[5]: 'Temperature'}, inplace=True)
    df.rename(columns={df.columns[6]: 'Signal Quality'}, inplace=True)
    df.rename(columns={df.columns[7]: 'Longitude'}, inplace=True)
    df.rename(columns={df.columns[8]: 'Latitude'}, inplace=True)
    df.rename(columns={df.columns[9]: 'Error'}, inplace=True)

    # Format of timestamp: 27062023_1912
    df["Day"] = df["Timestamp"].str[:2]
    df["Month"] = df["Timestamp"].str[2:4]
    df["Year"] = df["Timestamp"].str[4:8]  
    df["Hour"] = df["Timestamp"].str[9:11]
    df["Minute"] = df["Timestamp"].str[11:13]

    df["Timestamp"] = pd.to_datetime(df[["Year", "Month", "Day", "Hour", "Minute"]])

    # Drop the columns
    df.drop(columns=["Day", "Month", "Year", "Hour", "Minute"], inplace=True)

    # Get the list of files from the FTP server
    files = ftp.nlst()

    # Only show the image files
    files = [file for file in files if file.endswith(".jpg")]
   
    # Select slider
    selected_file = st.select_slider(
        "Wähle ein Bild aus",
        label_visibility="hidden", # Hide the label
        options=files,
        value=files[-1],
        # Format the timestamp
        format_func=lambda x: f"{x[:2]}.{x[2:4]}.{x[4:8]} {x[9:11]}:{x[11:13]}",
    )

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
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Batterie", df['Battery Voltage'].iloc[-1])
    col2.metric("Interne Spannung", df['Internal Voltage'].iloc[-1])
    col3.metric("Temperatur", df['Temperature'].iloc[-1])
    col4.metric("Signalqualität", df['Signal Quality'].iloc[-1])

    # Last startup relative to now
    lastStartup = df['Timestamp'].iloc[-1]
    now = datetime.now(pytz.timezone('Europe/Zurich')).replace(tzinfo=None)
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
    # Write difference in hours and minutes
    nextStartText = lastStartText + " - nächster Start in " 
    if timeDifference.seconds//3600 > 0:
        nextStartText = nextStartText + str(timeDifference.seconds//3600) + " Stunden und " + str((timeDifference.seconds//60)%60) + " Minuten."
    elif (timeDifference.seconds//60)%60 > 1:
        nextStartText = nextStartText + str((timeDifference.seconds//60)%60) + " Minuten."
    else:
        nextStartText = nextStartText + "weniger als einer Minute."
    st.write(nextStartText)

    st.divider()

    with st.sidebar:
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

    # Battery Voltage
    st.header("Batterie")
    st.write("Letzte Messung: ", df['Battery Voltage'].iloc[-1])
    df['Battery Voltage'] = df['Battery Voltage'].str[:-1]
    df['Battery Voltage'] = df['Battery Voltage'].astype(float)

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Battery Voltage:Q', axis=alt.Axis(title='Battery Voltage (V)')),
        tooltip=['Timestamp:T', 'Battery Voltage:Q']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # Internal Voltage
    st.header("Interne Spannung")
    st.write("Letzte Messung: ", df['Internal Voltage'].iloc[-1])
    df['Internal Voltage'] = df['Internal Voltage'].str[:-1]
    df['Internal Voltage'] = df['Internal Voltage'].astype(float)

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Internal Voltage:Q', axis=alt.Axis(title='Internal Voltage (V)')),
        tooltip=['Timestamp:T', 'Internal Voltage:Q']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # Temperature
    st.header("Temperatur")
    st.write("Letzte Messung: ", df['Temperature'].iloc[-1])

    df['Temperature'] = df['Temperature'].str[:-2]
    df['Temperature'] = df['Temperature'].astype(float)

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Temperature:Q', axis=alt.Axis(title='Temperature (°C)')),
        tooltip=['Timestamp:T', 'Temperature:Q']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # Signal Quality
    # See: https://www.waveshare.com/w/upload/5/54/SIM7500_SIM7600_Series_AT_Command_Manual_V1.08.pdf
    st.header("Signalqualität")
    st.write("Letzte Messung: ", df['Signal Quality'].iloc[-1].astype(str))

    df['Signal Quality'] = df['Signal Quality']

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X('Timestamp:T', axis=alt.Axis(title='Timestamp', labelAngle=-45)),
        y=alt.Y('Signal Quality:Q', axis=alt.Axis(title='Signal Quality (arb. units)')),
        tooltip=['Timestamp:T', 'Signal Quality:Q']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
   
    # Show a map with the location of the camera (not "-")
    st.header("Standort")
    try:
        dfMap = df[df['Latitude'] != '-']
        dfMap = dfMap[df['Longitude'] != '-']
        # Convert the latitude and longitude to float
        last_latitude = float(dfMap['Latitude'].iloc[-1])
        last_longitude = float(dfMap['Longitude'].iloc[-1])
        st.map(pd.DataFrame({'lat': [last_latitude], 'lon': [last_longitude]}))

        # Print timestamp
        st.write("Letztes Update: ", df['Timestamp'].iloc[-1].strftime("%d.%m.%Y %H:%M:%S Uhr"))
    except:
        st.write("Keine Koordinaten vorhanden")

    # Add a linebreak
    st.write("")
    st.write("")

    # Display the dataframe
    with st.expander("Rohdaten anzeigen"):

        # TODO get Original CSV
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
    with st.expander("Einstellungen anzeigen"):

        with open('settings.yaml') as file:
            settings = safe_load(file)

        # Display the settings
        st.write(settings)

        # Easteregg button which lets it snow with snow emojis
        if st.button("❄️⛄"):
            st.snow()

# Run the app
if __name__ == "__main__":
    main()
    
