'''GlacierCam firmware - see https://github.com/Eagleshot/GlacierCam for more information'''

from io import BytesIO, StringIO
from os import system, remove, listdir, path
from time import sleep
from csv import writer, reader
from datetime import datetime
from ftplib import FTP
import logging
from logging.handlers import RotatingFileHandler
from picamera2 import Picamera2
from libcamera import controls
from yaml import safe_load
import suntime
from sim7600x import SIM7600X
from witty_pi_4 import sync_witty_pi_time_with_network, generate_schedule, apply_schedule_witty_pi_4, get_battery_voltage_witty_pi_4, get_temperature_witty_pi_4, set_low_voltage_treshold_witty_pi_4, set_recovery_voltage_treshold_witty_pi_4

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

# Error logging
file_handler = RotatingFileHandler(f"{FILE_PATH}log.txt", mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])

# Read config.yaml file from SD card
try:
    with open(f"{FILE_PATH}config.yaml", 'r', encoding='utf-8') as file:
        config = safe_load(file)
except Exception as e:
    logging.critical("Could not open config.yaml: %s", str(e))

CAMERA_NAME = get_cpu_serial() # Unique hardware serial number
TIMESTAMP_CSV = datetime.today().strftime('%Y-%m-%d %H:%MZ') # UTC-Time
TIMESTAMP_FILENAME = datetime.today().strftime('%Y%m%d_%H%MZ') # UTC-Time

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
            logging.warning("Could not connect to FTP server: %s, attempt %s/%s failed - trying again in 5 seconds.", str(e), i+1, MAX_RETRIES)
        else:
            logging.info("Could not connect to FTP server: %s, attempt %s/%s failed - trying again in 5 seconds.", str(e), i+1, MAX_RETRIES)

        CONNECTED_TO_FTP = False
        sleep(5) # Wait 5 seconds and try again

def change_directory(directory: str):
    '''Change directory on the file server'''
    try:
        ftp_directory_list = ftp.nlst()

        if directory not in ftp_directory_list:
            ftp.mkd(directory)

        ftp.cwd(directory)

    except Exception as e:
        logging.warning("Could not change directory on FTP server: %s", str(e))

# Go to custom directory in FTP server if specified
try:
    if config["ftpDirectory"] != "" and CONNECTED_TO_FTP:
        change_directory(config["ftpDirectory"])

except Exception as e:
    logging.warning("Could not change directory on FTP server: %s", str(e))

# Go to folder with camera name + unique hardware serial number or create it
try:
    if config["multipleCamerasOnServer"] and CONNECTED_TO_FTP:
        change_directory(CAMERA_NAME)

except Exception as e:
    logging.warning("Could not change directory on FTP server: %s", str(e))

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
            logging.info("No settings file on server. Creating new file with default settings.")
            with open(f"{FILE_PATH}settings.yaml", 'rb') as fp:
                ftp.storbinary('STOR settings.yaml', fp)
except Exception as e:
    logging.critical("Could not download settings file from FTP server: %s", str(e))

# Read settings file
try:
    with open(f"{FILE_PATH}settings.yaml", 'r', encoding='utf-8') as file:
        settings = safe_load(file)
except Exception as e:
    logging.critical("Could not open settings.yaml: %s", str(e))

###########################
# Time synchronization
###########################

try:
    if settings["timeSync"] and CONNECTED_TO_FTP:
        sync_witty_pi_time_with_network()
except Exception as e:
    logging.warning("Could not synchronize time with network: %s", str(e))

###########################
# Schedule script
###########################

# Get sunrise and sunset times
try:
    if settings["enableSunriseSunset"] and settings["latitude"] != 0 and settings["longitude"] != 0:
        sun = suntime.Sun(settings["latitude"], settings["longitude"])

        # Sunrise
        sunrise = sun.get_sunrise_time()
        logging.info("Next sunrise: %s:%s", sunrise.hour, sunrise.minute)
        sunrise = sunrise.replace(minute=15 * round(sunrise.minute / 15)) # Round to nearest 15 minutes
        settings["startTimeHour"] = sunrise.hour
        settings["startTimeMinute"] = sunrise.minute

        # Sunset
        sunset = sun.get_sunset_time()
        logging.info("Next sunset: %s:%s", sunset.hour, sunset.minute)
        time_until_sunset = sunset - sunrise
        time_until_sunset = time_until_sunset.total_seconds() / 60 # Convert to minutes
        settings["repetitionsPerday"] = int(time_until_sunset / settings["intervalMinutes"])

except Exception as e:
    logging.warning("Could not get sunrise and sunset times: %s", str(e))

try:
    battery_voltage = get_battery_voltage_witty_pi_4()

    battery_voltage_half = settings["battery_voltage_half"]
    battery_voltage_quarter = settings["battery_voltage_half"]-(settings["battery_voltage_half"]-settings["low_voltage_treshold"])/2

    if battery_voltage_quarter < battery_voltage < battery_voltage_half:
        settings["intervalMinutes"] = settings["intervalMinutes"]*2
        settings["repetitionsPerday"] = settings["repetitionsPerday"]/2
    elif battery_voltage < battery_voltage_quarter:
        settings["repetitionsPerday"] = 1

except Exception as e:
    logging.warning("Could not get battery voltage: %s", str(e))

try:
    # Generate schedule
    generate_schedule(settings["startTimeHour"], settings["startTimeMinute"], settings["intervalMinutes"], settings["repetitionsPerday"])
except Exception as e:
    generate_schedule(8, 0, 30, 8)
    logging.warning("Failed to generate schedule: %s", str(e))

# Apply schedule
next_startup_time = f"{apply_schedule_witty_pi_4()}Z"

##########################
# SIM7600G-H 4G module
###########################

# See Waveshare documentation
try:
    sim7600 = SIM7600X()
except Exception as e:
    logging.warning("Could not open serial connection with 4G module: %s", str(e))

###########################
# Enable GPS
###########################
try:
    # Enable GPS to later read out position
    if settings["enableGPS"]:
        sim7600.start_gps_session()
except Exception as e:
    logging.warning("Could not start GPS: %s", str(e))

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
    logging.critical("Could not setup camera: %s", str(e))

# Focus settings
try:
    if settings["lensPosition"] > -1:
        camera.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": settings["lensPosition"]})
    else:
        camera.set_controls({"AfMode": controls.AfModeEnum.Auto})
except Exception as e:
    logging.warning("Could not set lens position: %s", str(e))

###########################
# Capture image
###########################
image_filename = f'{TIMESTAMP_FILENAME}.jpg'
try:
    if settings["cameraName"] != "":
        image_filename = f'{TIMESTAMP_FILENAME}_{settings["cameraName"]}.jpg'
except Exception as e:
    logging.warning("Could not set custom camera name: %s", str(e))

try:
    camera.start_and_capture_file(FILE_PATH + image_filename, capture_mode=cameraConfig, delay=2, show_preview=False)
except Exception as e:
    logging.critical("Could not start camera and capture image: %s", str(e))

###########################
# Stop camera
###########################
try:
    camera.stop()
except Exception as e:
    logging.warning("Could not stop camera: %s", str(e))

###########################
# Upload to ftp server and then delete last image
###########################

try:
    if CONNECTED_TO_FTP:
        # Upload all images
        for file in listdir(FILE_PATH):
            if file.endswith(".jpg"):
                with open(FILE_PATH + file, 'rb') as imgFile:
                    ftp.storbinary(f"STOR {file}", imgFile)
                    logging.info("Successfully uploaded %s", file)

                    # Delete uploaded image from Raspberry Pi
                    remove(FILE_PATH + file)
except Exception as e:
    logging.critical("Could not upload image to FTP server: %s", str(e))

###########################
# Uploading sensor data to CSV
###########################

try:
    # If settings low voltage treshold exists
    if 2.0 <= settings["low_voltage_treshold"] <= 25.0 or settings["low_voltage_treshold"] == 0:
        set_low_voltage_treshold_witty_pi_4(settings["low_voltage_treshold"])

    # If settings recovery voltage treshold exists
    if 2.0 <= settings["recovery_voltage_treshold"] <= 25.0 or settings["recovery_voltage_treshold"] == 0:
        set_recovery_voltage_treshold_witty_pi_4(settings["recovery_voltage_treshold"])

except Exception as e:
    logging.warning("Could not set voltage tresholds: %s", str(e))

###########################
# Get readings
###########################
temperature = get_temperature_witty_pi_4()
internal_voltage = "-" # get_internal_voltage_witty_pi_4()
internal_current = "-" # get_internal_current_witty_pi_4()
signal_quality = sim7600.get_signal_quality()

###########################
# Get GPS position
###########################
try:
    latitude = "-"
    longitude = "-"
    height = "-"

    if settings["enableGPS"]:
        latitude, longitude, height = sim7600.get_gps_position()
        sim7600.stop_gps_session()

except Exception as e:
    logging.warning("Could not get GPS coordinates: %s", str(e))

###########################
# Log readings to CSV
###########################
# Append new measurements to log CSV or create new CSV file if none exists
try:
    with StringIO() as csvBuffer:
        writer = writer(csvBuffer)
        newRow = [TIMESTAMP_CSV, next_startup_time, battery_voltage, internal_voltage, internal_current, temperature, signal_quality, latitude, longitude, height]

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
                logging.warning("Could not open diagnostics.csv: %s", str(e))

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
    logging.warning("Could not append new measurements to log CSV: %s", str(e))

try:
    with open(f"{FILE_PATH}log.txt", 'rb', encoding='utf-8') as file:
        ftp.storbinary("APPE log.txt", file)

    # Upload WittyPi diagnostics
    if settings["uploadWittyPiDiagnostics"] and CONNECTED_TO_FTP:

        # Witty Pi log
        with open("/home/pi/wittypi/wittyPi.log", 'rb') as wittyPiDiagnostics:
            ftp.storbinary("APPE wittyPiDiagnostics.txt", wittyPiDiagnostics)

        # Witty Pi schedule
        with open("/home/pi/wittypi/schedule.log", 'rb') as wittyPiDiagnostics:
            ftp.storbinary("APPE wittyPiSchedule.txt", wittyPiDiagnostics)

except Exception as e:
    logging.warning("Could not upload WittyPi diagnostics: %s", str(e))

###########################
# Quit FTP session
###########################
try:
    if CONNECTED_TO_FTP:
        ftp.quit()
except Exception as e:
    logging.warning("Could not quit FTP session: %s", str(e))

###########################
# Shutdown Raspberry Pi if enabled
###########################
try:
    if settings["shutdown"]:
        logging.info("Shutting down now.")
        system("sudo shutdown -h now")
except Exception as e:
    # Setting not found
    system("sudo shutdown -h now")
