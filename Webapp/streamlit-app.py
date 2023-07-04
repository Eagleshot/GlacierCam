import streamlit as st
from ftplib import FTP
from io import BytesIO
from PIL import Image
import pandas as pd
from datetime import datetime

# FTP server credentials
FTP_HOST = '444024-1.web.fhgr.ch'
FTP_USERNAME = '444024_1_1'
FTP_PASSWORD = 'e5tlZOhT=EoB'

# Connect to the FTP server
ftp = FTP(FTP_HOST)
ftp.login(user=FTP_USERNAME, passwd=FTP_PASSWORD)

ftp.cwd('private/Camera1_0000000038ef8b9c')


# Streamlit app
def main():

    # Download diagnosticsf.csv as file with utf-8 encoding
    ftp.retrbinary('RETR diagnostics.csv', open('df.csv', 'wb').write)
    df = pd.read_csv('df.csv', encoding='utf-8')

    # TODO Unique naming
    df.rename(columns={df.columns[0]: 'Timestamp'}, inplace=True)
    df.rename(columns={df.columns[1]: 'Battery Voltage'}, inplace=True)
    df.rename(columns={df.columns[2]: 'Internal Voltage'}, inplace=True)
    df.rename(columns={df.columns[3]: 'Battery Current'}, inplace=True)
    df.rename(columns={df.columns[4]: 'Temperature'}, inplace=True)
    df.rename(columns={df.columns[5]: 'Signal Quality'}, inplace=True)
    df.rename(columns={df.columns[6]: 'Longitude'}, inplace=True)
    df.rename(columns={df.columns[7]: 'Latitude'}, inplace=True)
    
    st.title("Display Image from FTP Server")

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

    # Only get the newest image
    files = [files[-1]]


    # Select an image file from the FTP server
    selected_file = st.selectbox("Select an image file", files)

    oldestDate = df["Timestamp"].min()
    print(oldestDate)

    # https://docs.kanaries.net/de/tutorials/Python/streamlit-datetime-slider.de
    start_time = st.slider(
        "When do you start?",
        min_value=datetime(2020, 1, 1, 9, 0),
        value=datetime(2020, 1, 1, 9, 30), 
        max_value=datetime(2020, 1, 1, 10, 0),
        format="MM/DD/YY - hh:mm")
    st.write("Start time:", start_time)

    # Get the image file from the FTP server
    image_data = BytesIO()
    ftp.retrbinary(f"RETR {selected_file}", image_data.write)
    image = Image.open(image_data)

    # Display the image
    st.image(image, caption=selected_file, use_column_width=True)

    # Plot the battery voltage
    #st.line_chart(df['Battery Voltage'])

    # Plot the internal voltage
    df['Internal Voltage'] = df['Internal Voltage'].str[:-1]
    #st.line_chart(df['Internal Voltage'])

    # Remove last 2 characters from temperature
    df['Temperature'] = df['Temperature'].str[:-2]
    # plot the temperature against the timestamp
    #st.line_chart(df['Temperature'])
    
    # Display the df
    st.dataframe(df)

    # Close the FTP connection
    ftp.quit()
    

# Run the app
if __name__ == "__main__":
    main()
