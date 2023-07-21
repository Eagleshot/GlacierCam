import streamlit as st
from ftplib import FTP
from io import BytesIO
from PIL import Image
import pandas as pd
from yaml import safe_load
from datetime import datetime
import matplotlib.pyplot as plt

# Connect to the FTP server
ftp = FTP(FTP_HOST)
ftp.login(user=FTP_USERNAME, passwd=FTP_PASSWORD)

# Change the working directory to the FTP folder
ftp.cwd(FTP_FOLDER)

# Streamlit app
def main():

    # Set page title and favicon
    st.set_page_config(
        page_title="GlacierCam",
        page_icon="🏔️"
    )

    # Title
    st.title("GlacierCam 🏔️")

    imagePlaceholder = st.empty()

    # Download diagnosticsf.csv as file with utf-8 encoding
    ftp.retrbinary('RETR diagnostics.csv', open('df.csv', 'wb').write)
    df = pd.read_csv('df.csv', encoding='utf-8')

    # TODO Unique naming
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


    # Get all the characters after the 12th character from the first
    lastCharacters = files[-1][13:]

    # Only the first 12 characters of the filename are displayed
    files = [file[:13] for file in files]

    # Select slider
    selected_file = st.select_slider(
        "Wähle ein Bild aus",
        options=files,
        value=files[-1]
    )

    # Add the rest of the filename back to selected_file
    selected_file = selected_file + lastCharacters

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

    # Print last Battery Voltage
    st.write("Batteriespannung: ", df['Battery Voltage'].iloc[-1])

    # Print last temperature
    st.write("Temperatur: ", df['Temperature'].iloc[-1])

    # Print last signal quality
    st.write("Signalqualität: ", df['Signal Quality'].iloc[-1])

    # Last startup relative to now
    lastStartup = df['Timestamp'].iloc[-1]
    now = datetime.now()
    timeDifference = now - lastStartup
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
    # nextStartup = nextStartup + pd.Timedelta(minutes=1)
    now = datetime.now()
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

    # Battery Voltage
    st.title("Batteriespannung in V")
    df['Battery Voltage'] = df['Battery Voltage'].str[:-1]
    df['Battery Voltage'] = df['Battery Voltage'].astype(float)
    st.line_chart(df['Battery Voltage'])

    # Internal Voltage
    st.title("Interne Spannung in V")
    df['Internal Voltage'] = df['Internal Voltage'].str[:-1]
    df['Internal Voltage'] = df['Internal Voltage'].astype(float)
    st.line_chart(df['Internal Voltage'])

    # Temperature
    st.title("Temperatur in °C")
    df['Temperature'] = df['Temperature'].str[:-2]
    df['Temperature'] = df['Temperature'].astype(float)
    st.line_chart(df['Temperature'])

    # Signal Quality
    st.title("Signalqualität")
    df['Signal Quality'] = df['Signal Quality']
    st.line_chart(df['Signal Quality'])

    # Show a map with the location of the camera (not "-")
    st.title("Standort der Kamera")
    try:
        df = df[df['Latitude'] != '-']
        df = df[df['Longitude'] != '-']
        # Convert the latitude and longitude to float
        last_latitude = float(df['Latitude'].iloc[-1])
        last_longitude = float(df['Longitude'].iloc[-1])
        st.map(pd.DataFrame({'lat': [last_latitude], 'lon': [last_longitude]}))

        # Print timestamp
        st.write("Letztes Update: ", df['Timestamp'].iloc[-1])
    except:
        st.write("Keine Koordinaten vorhanden")

    # Read settings.yaml and display it
    ftp.retrbinary('RETR settings.yaml', open('settings.yaml', 'wb').write)
    
    # Add a divider
    st.divider()

    # Display the dataframe
    with st.expander("Rohdaten anzeigen"):
        st.dataframe(df)

        # Download diagnostics.csv
        st.download_button(
            label="Diagnosedatei herunterladen 📝",
            data=df.to_csv().encode("utf-8"),
            file_name="diagnostics.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Display the settings
    with st.expander("Einstellungen anzeigen"):

        with open('settings.yaml') as file:
            dfSettings = safe_load(file)

        st.dataframe(dfSettings)

        # Easteregg button which lets it snow
        if st.button("?"):
            st.snow()


    

# Run the app
if __name__ == "__main__":
    main()
