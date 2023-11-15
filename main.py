#!/usr/bin/python3
# -*- coding:utf-8 -*-

# Import required libraries
from io import BytesIO, StringIO
from subprocess import check_output, STDOUT
from os import system, remove, listdir, path
from time import sleep
from csv import writer, reader
from datetime import datetime
from ftplib import FTP
from picamera2 import Picamera2
from libcamera import controls
from yaml import safe_load
import serial

###########################
# Configuration and filenames
###########################
# Get unique hardware id of Raspberry Pi
# See: https://www.raspberrypi.com/documentation/computers/config_txt.html#the-serial-number-filter
# and https://raspberrypi.stackexchange.com/questions/2086/how-do-i-get-the-serial-number
def get_cpu_serial():
    '''Get the unique serial number of Raspberry Pi CPU'''
    cpuserial = "0000000000000000"
    try:
        with open('/proc/cpuinfo', 'r', encoding='utf-8') as f:
            for cpu_line in f:
                if cpu_line[0:6] == 'Serial':
                    cpuserial = cpu_line[10:26]
                    break
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

FILE_PATH = "/home/pi/"  # Path where files are saved

# Read config.yaml file from SD card
try:
    with open(f"{FILE_PATH}config.yaml", 'r', encoding='utf-8') as file:
        config = safe_load(file)
except Exception as e:
    print(f"Could not open config.yaml: {str(e)}")

cameraName = f"{config['cameraName']}_{get_cpu_serial()}" # Camera name + unique hardware serial
currentTimeCSV = datetime.today().strftime('%Y-%m-%d %H:%M:%SZ') # UTC-Time
currentTimeFilename = datetime.today().strftime('%Y%m%d_%H%M') # UTC-Time
imgFileName = f"{currentTimeFilename}Z_{cameraName}.jpg"
error = ""

###########################
# Connect to FTP server
###########################
MAX_RETRIES = 5

for i in range(MAX_RETRIES):
    try:
        ftp = FTP(config["ftpServerAddress"], timeout=5)
        ftp.login(user=config["username"], passwd=config["password"])
        CONNECTED_TO_FTP = True
        break
    except Exception as e:
        if i > 1:
            error += f"Could not connect to FTP server: {str(e)}, attempt {i+1}/5 failed - trying again in 5 seconds."
        print(f"Could not connect to FTP server: {str(e)}, attempt {i+1}/5 failed - trying again in 5 seconds.")
        CONNECTED_TO_FTP = False
        sleep(5) # Wait 5 seconds and try again

# Go to custom directory in FTP server if specified
try:
    if config["ftpDirectory"] != "" and CONNECTED_TO_FTP:

        ftp_directory_list = ftp.nlst()

        if config["ftpDirectory"] not in ftp_directory_list:
            ftp.mkd(config["ftpDirectory"])

        ftp.cwd(config["ftpDirectory"])

except Exception as e:
    error += f"Could not change directory on FTP server: {str(e)}"
    print(f"Could not change directory on FTP server: {str(e)}")

# Go to folder with camera name + unique hardware serial number or create it
try:
    if config["multipleCamerasOnServer"] and CONNECTED_TO_FTP:

        ftp_directory_list = ftp.nlst()

        if cameraName not in ftp_directory_list:
            ftp.mkd(cameraName)

        ftp.cwd(cameraName)

except Exception as e:
    error += f"Could not change directory on FTP server: {str(e)}"
    print(f"Could not change directory on FTP server: {str(e)}")

###########################
# Settings
###########################

# Try to download settings from server
try:
    if CONNECTED_TO_FTP:

        fileList = ftp.nlst()

        # Check if settings file exists
        if "settings.yaml" in fileList:
            with open(f"{FILE_PATH}settings.yaml", 'wb') as fp:  # Download
                ftp.retrbinary('RETR settings.yaml', fp.write)
        else:
            print("No settings file on FTP server. Creating new settings file with default settings.")
            with open(f"{FILE_PATH}settings.yaml", 'rb') as fp:
                ftp.storbinary('STOR settings.yaml', fp)
except Exception as e:
    error += f"Error with settings file: {str(e)}"
    print(f'Error with settings file: {str(e)}')

# Read settings file
try:
    with open(f"{FILE_PATH}settings.yaml", 'r', encoding='utf-8') as file:
        settings = safe_load(file)
except Exception as e:
    print(f"Could not open settings.yaml: {str(e)}")

###########################
# Time synchronization
###########################

def run_witty_pi_4_command(command: str) -> str:
    '''Send a command to Witty Pi 4'''
    try:
        command = f"cd /home/pi/wittypi && . ./utilities.sh && {command}"
        output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=5)
        output = output.replace("\n", "")
        return output
    except Exception as e:
        print(f"Could not send Witty Pi 4 command: {str(e)}")
        return "ERROR"

def sync_witty_pi_time_with_network():
    '''Sync WittyPi clock with network time'''

    # See: https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-how-to-synchronise-time-with-internet-on-boot/
    try:
        output = run_witty_pi_4_command("net_to_system && system_to_rtc")
        print(f"Time synchronized with network: {output}")
    except Exception as e:
        # error += f"Could not synchronize time with network: {str(e)}" # TODO Return error value
        print(f"Could not synchronize time with network: {str(e)}")

try:
    if settings["timeSync"] and CONNECTED_TO_FTP:
        sync_witty_pi_time_with_network()
except Exception as e:
    error += f"Could not synchronize time with network: {str(e)}"
    print(f"Could not synchronize time with network: {str(e)}")

###########################
# Schedule script
###########################
def generate_schedule(startTimeHour: int, startTimeMinute: int, intervalMinutes: int, maxDurationMinute: int, repetitionsPerday: int):
    '''Generate a startup schedule file for Witty Pi 4'''

    # Basic validity check of parameters
    if not 0 < startTimeHour < 24:
        startTimeHour = 8

    if not 0 < startTimeMinute < 60:
        startTimeMinute = 0

    if not 0 < intervalMinutes < 1440:
        intervalMinutes = 30

    if not 0 < maxDurationMinute < 1440:
        maxDurationMinute = 5

    if not 0 < repetitionsPerday < 250:
        repetitionsPerday = 8

    if ((repetitionsPerday * intervalMinutes) + startTimeMinute + (startTimeHour * 60)) > 1440:
        repetitionsPerday = 1

    # 2037 is the maximum year for WittyPi
    formatted_start_time = f"{startTimeHour:02d}:{startTimeMinute:02d}"
    schedule = f"BEGIN\t2020-01-01 {formatted_start_time}:00\nEND\t2037-12-31 23:59:59\n"

    for i in range(repetitionsPerday):
        schedule += f"ON\tM{maxDurationMinute}\n"

        # Last off is different
        if i < repetitionsPerday - 1:
            schedule += f"OFF\tM{intervalMinutes - maxDurationMinute}\n"

    # Turn camera off for the rest of the day
    remaining_minutes = 1440 - (repetitionsPerday * intervalMinutes) + (intervalMinutes - maxDurationMinute)
    remaining_hours = remaining_minutes // 60
    remaining_minutes = remaining_minutes % 60

    schedule += f"OFF\tH{remaining_hours}"
    if remaining_minutes > 0:
        schedule += f" M{remaining_minutes}"

    return schedule

try:
    schedule = generate_schedule(settings["startTimeHour"], settings["startTimeMinute"], settings["intervalMinutes"], settings["maxDurationMinute"], settings["repetitionsPerday"])
except Exception as e:
    error += f"Failed to generate schedule with setting: {str(e)}"
    print(f"Failed to generate schedule with setting: {str(e)}")

    schedule = generate_schedule(8, 0, 30, 5, 8)

# Compare old schedule file to new one
try:
    SCHEDULE_FILE_PATH = "/home/pi/wittypi/schedule.wpi"

    if path.exists(SCHEDULE_FILE_PATH):
        with open(SCHEDULE_FILE_PATH, "r", encoding='utf-8') as f:
            oldSchedule = f.read()

        # Write new schedule file if it changed
        if oldSchedule != schedule:
            print("Writing and applying new schedule file.")
            with open(SCHEDULE_FILE_PATH, "w", encoding='utf-8') as f:
                f.write(schedule)
        else:
            print("Schedule did not change.")
    else:
        print("Writing and applying new schedule file.")
        with open(SCHEDULE_FILE_PATH, "w", encoding='utf-8') as f:
            f.write(schedule)
except Exception as e:
    error += f"Failed to write schedule file: {str(e)}"
    print(f"Failed to write schedule file: {str(e)}")

def apply_schedule_witty_pi_4(max_retries: int = 5) -> str:
    '''Apply schedule to Witty Pi 4'''
    try:
        for i in range(max_retries):
            # Apply new schedule
            command = "cd /home/pi/wittypi && sudo ./runScript.sh"
            output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=10)
            output = output.split("\n")[1:3]
            print(output)

            if not "Schedule next startup at:" in output[1]:
                print(f"Failed to apply schedule: {output[0]}")
                sync_witty_pi_time_with_network()
            else:
                print(f"{output[0]}\n{output[1]}")
                nextStartupTime = output[1][-19:]
                return nextStartupTime

    except Exception as e:
        print(f"Failed to apply schedule: {str(e)}")
        return "-"

nextStartupTime = apply_schedule_witty_pi_4()

##########################
# SIM7600G-H 4G module
###########################

# Send AT command to SIM7600X
def send_at_command(command: str, back: str = 'OK', timeout: int = 1) -> str:
    '''Send an AT command to SIM7600X'''
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    sleep(timeout)
    if ser.inWaiting():
        sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if back not in rec_buff.decode():
        print(f"Error: AT command {command} returned {rec_buff.decode()}")
        return ""

    return rec_buff.decode()

# Get current signal quality
# https://www.manualslib.com/download/1593302/Simcom-Sim7000-Series.html
# 0 -115 dBm or less
# 1 -111 dBm
# 2...30 -110... -54 dBm
# 31 -52 dBm or greater
# 99 not known or not detectable
def get_signal_quality():
    '''Gets the current signal quality from the SIM7600G-H 4G module'''
    try:
        signal_quality = send_at_command('AT+CSQ')
        signal_quality = signal_quality[8:10]
        signal_quality = signal_quality.replace("\n", "")
        signal_quality = ''.join(ch for ch in signal_quality if ch.isdigit()) # Remove non-numeric characters
        print(f"Current signal quality: {signal_quality}")
        return signal_quality
    except Exception as e:
        # error += f"Could not get current signal quality: {str(e)}" # TODO
        print(f"Could not get current signal quality: {str(e)}")
        return ""

# Get GPS Position
def get_gps_position(max_attempts=7, delay=5):
    '''Gets the current GPS position from the SIM7600G-H 4G module'''

    current_attempt = 0

    while current_attempt < max_attempts:

        current_attempt += 1
        gps_data_raw = send_at_command('AT+CGPSINFO', back='+CGPSINFO: ')

        if gps_data_raw == 0:
            sleep(delay)
        elif ',,,,,,' in gps_data_raw:
            print('GPS not yet ready.')
            sleep(delay)
        else:
            # Additions to Demo Code Written by Tim! -> Core Electronics
            # https://core-electronics.com.au/guides/raspberry-pi/raspberry-pi-4g-gps-hat/
            gps_data_cleaned = str(gps_data_raw)[13:]

            lat = gps_data_cleaned[:2]
            small_lat = gps_data_cleaned[2:11]
            north_or_south = gps_data_cleaned[12]

            lon = gps_data_cleaned[14:17]
            small_lon = gps_data_cleaned[17:26]
            east_or_west = gps_data_cleaned[27]

            lat = float(lat) + (float(small_lat)/60)
            lon = float(lon) + (float(small_lon)/60)

            if north_or_south == 'S':
                lat = -lat
            if east_or_west == 'W':
                lon = -lon

            # TODO Sometimes heigth is not correctly extracted
            Height = gps_data_cleaned[45:49]

            str_lat = str(round(lat, 5))
            str_lon = str(round(lon, 5))
            str_height = str(Height)

            # TODO Time

            print(f"GPS position: LAT {str_lat}, LON {str_lon}, HEIGHT {str_height}")
            return str_lat, str_lon, str_height
    return "-", "-", "-"

# See Waveshare documentation
try:
    ser = serial.Serial('/dev/ttyUSB2', 115200, timeout=5)  # USB connection
    ser.flushInput()
except Exception as e:
    error += f"Could not open serial connection with 4G module: {str(e)}"
    print (f"Could not open serial connection with 4G module: {str(e)}")

###########################
# Enable GPS
###########################
try:
    # Enable GPS to later read out position
    if settings["enableGPS"]:
        print('Start GPS session.')
        send_at_command('AT+CGPS=1,1')
except Exception as e:
    error += f"Could not start GPS: {str(e)}"
    print(f"Could not start GPS: {str(e)}")

###########################
# Setup camera
###########################

try:
    camera = Picamera2()
    cameraConfig = camera.create_still_configuration() # Selects highest resolution by default

    # https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
    # Table 6. Stream- specific configuration parameters
    MIN_RESOLUTION = 64
    MAX_RESOLUTION = (4608, 2592)
    resolution = settings["resolution"]

    if MIN_RESOLUTION < resolution[0] < MAX_RESOLUTION[0] and MIN_RESOLUTION < resolution[1] < MAX_RESOLUTION[1]:
        size = (resolution[0], resolution[1])
        cameraConfig = camera.create_still_configuration({"size": size})

except Exception as e:
    error += f"Could not set custom camera resolution: {str(e)}"
    print(f"Could not set custom camera resolution: {str(e)}")

# Focus settings
try:
    if settings["lensPosition"] > -1:
        camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": settings["lensPosition"]})
    else:
        camera.set_controls({"AfMode": controls.AfModeEnum.Auto})
except Exception as e:
    error += f"Could not set lens position: {str(e)}"
    print(f"Could not set lens position: {str(e)}")

###########################
# Capture image
###########################
try:
    camera.start_and_capture_file(FILE_PATH + imgFileName, capture_mode=cameraConfig, delay=2, show_preview=False)
except Exception as e:
    error += f"Could not start camera and capture image: {str(e)}"
    print(f"Could not start camera and capture image: {str(e)}")

###########################
# Stop camera
###########################
try:
    camera.stop()
except Exception as e:
    error += f"Could not stop camera: {str(e)}"
    print(f"Could not stop camera: {str(e)}")

###########################
# Upload to ftp server and then delete last image
###########################

try:
    if CONNECTED_TO_FTP:
        # Upload all images in FILE_PATH
        for file in listdir(FILE_PATH):
            if file.endswith(".jpg"):
                with open(FILE_PATH + file, 'rb') as imgFile:
                    ftp.storbinary(f"STOR {file}", imgFile)
                    print(f"Successfully uploaded {file}")

                    # Delete uploaded image from Raspberry Pi
                    remove(FILE_PATH + file)
except Exception as e:
    error += f"Could not open image: {str(e)}"
    print(f"Could not open image: {str(e)}")

###########################
# Uploading sensor data to CSV
###########################

# Get WittyPi readings
# See: https://www.baeldung.com/linux/run-function-in-script

# Temperature
def get_temperature_witty_pi_4():
    '''Gets the current temperature reading from the Witty Pi 4 in °C'''
    try:
        temperature = run_witty_pi_4_command("get_temperature")
        temperature = temperature.split(" / ", maxsplit = 1)[0] # Remove the Farenheit reading
        temperature = temperature[:-2] # Remove °C
        print(f"Temperature: {temperature} °C")
        return temperature
    except Exception as e:
        # error += f"Could not get temperature: {str(e)}" # TODO Return error value
        print(f"Could not get temperature: {str(e)}")
        return "-"

# Battery voltage
def get_battery_voltage_witty_pi_4():
    '''Gets the battery voltage reading from the Witty Pi 4 in V'''
    try:
        battery_voltage = run_witty_pi_4_command("get_input_voltage")
        print(f"Battery voltage: {battery_voltage} V")
        return battery_voltage
    except Exception as e:
        # error += f"Could not get battery voltage: {str(e)}" # TODO Return error value
        print(f"Could not get battery voltage: {str(e)}")
        return "-"

# Raspberry Pi voltage
def get_internal_voltage_witty_pi_4():
    '''Gets the internal (5V) voltage from the Witty Pi 4 in V'''
    try:
        internal_voltage = run_witty_pi_4_command("get_output_voltage")
        print(f"Output voltage: {internal_voltage} V")
        return internal_voltage
    except Exception as e:
        # error += f"Could not get Raspberry Pi voltage: {str(e)}" # TODO Return error value
        print(f"Could not get Raspberry Pi voltage: {str(e)}")
        return "-"

# Raspberry Pi current - Not needed at the moment
def get_internal_current_witty_pi_4():
    '''Gets the internal (5V) current reading from the Witty Pi 4 in A'''
    try:
        internal_current = run_witty_pi_4_command("get_output_current")
        print(f"Output current: {internal_current} A")
        return internal_current
    except Exception as e:
        # error += f"Could not get Raspberry Pi current: {str(e)}" # TODO Return error value
        print(f"Could not get Raspberry Pi current: {str(e)}")
        return "-"

###########################
# Get readings
###########################
temperature = get_temperature_witty_pi_4()
battery_voltage = get_battery_voltage_witty_pi_4()
internal_voltage = get_internal_voltage_witty_pi_4()
internal_current = "-" # get_internal_current_witty_pi_4()
signal_quality = get_signal_quality()

###########################
# Get GPS position
###########################
try:
    latitude = "-"
    longitude = "-"
    height = "-"

    if settings["enableGPS"]:
        latitude, longitude, height = get_gps_position()
        print('Stopping GPS session.')
        send_at_command('AT+CGPS=0')

except Exception as e:
    error += f"Failed to get GPS coordinates: {str(e)}"
    print(f"Failed to get GPS coordinates: {str(e)}")

###########################
# Log readings to CSV
###########################
# Append new measurements to log CSV or create new CSV file if none exists
try:
    with StringIO() as csvBuffer:
        writer = writer(csvBuffer)
        newRow = [currentTimeCSV, nextStartupTime, battery_voltage, internal_voltage, internal_current, temperature, signal_quality, latitude, longitude, height, error]

        # Check if is connected to FTP server
        if CONNECTED_TO_FTP:
            # Check if local CSV file exists
            try:
                if path.exists(f"{FILE_PATH}diagnostics.csv"):
                    with open(f"{FILE_PATH}diagnostics.csv", 'r', encoding='utf-8') as file:
                        csvData = file.read()
                        # Write all lies to writer
                        for line in reader(StringIO(csvData)):
                            writer.writerow(line)
                    remove(FILE_PATH + "diagnostics.csv")
            except Exception as e:
                error += f"Could not open diagnostics.csv: {str(e)}"
                print(f"Could not open diagnostics.csv: {str(e)}")

            # Append new row to CSV file
            writer.writerow(newRow)
            csvData = csvBuffer.getvalue().encode('utf-8')

            # Upload CSV file to FTP server
            ftp.storbinary("APPE diagnostics.csv", BytesIO(csvData))
        else:
            writer.writerow(newRow)
            csvData = csvBuffer.getvalue().encode('utf-8')

            # Append new row to local CSV file
            with open(f"{FILE_PATH}diagnostics.csv", 'a', newline='', encoding='utf-8') as file:
                file.write(csvData.decode('utf-8'))
except Exception as e:
    print(f"Could not append new measurements to log CSV: {str(e)}")

try:
    # Upload WittyPi diagnostics
    if settings["uploadWittyPiDiagnostics"] and CONNECTED_TO_FTP:

        # Witty Pi log
        with open("/home/pi/wittypi/wittyPi.log", 'rb') as wittyPiDiagnostics:
            ftp.storbinary("APPE wittyPiDiagnostics.txt", wittyPiDiagnostics)

        # Witty Pi schedule
        with open("/home/pi/wittypi/schedule.log", 'rb') as wittyPiDiagnostics:
            ftp.storbinary("APPE wittyPiSchedule.txt", wittyPiDiagnostics)

except Exception as e:
    print(f"Could not upload WittyPi diagnostics: {str(e)}")

###########################
# Quit FTP session
###########################
try:
    if CONNECTED_TO_FTP:
        ftp.quit()
except Exception as e:
    print(f"Could not quit FTP session: {str(e)}")

###########################
# Shutdown Raspberry Pi if enabled
###########################
try:
    if settings["shutdown"]:
        print('Shutting down now.')
        system("sudo shutdown -h now")
except Exception as e:
    # Setting not found
    system("sudo shutdown -h now")
