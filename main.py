'''GlacierCam firmware - see https://github.com/Eagleshot/GlacierCam for more information'''

from io import BytesIO, StringIO
from os import system, remove, listdir, path
from csv import writer, reader
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from picamera2 import Picamera2
from libcamera import controls
from yaml import safe_load
import suntime
from sim7600x import SIM7600X
from witty_pi_4 import WittyPi4
import fileserver as fs
from settings import Settings

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
LOG_LEVEL = logging.WARNING

file_handler = RotatingFileHandler(f"{FILE_PATH}log.txt", mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logging.basicConfig(level=LOG_LEVEL, handlers=[file_handler, stream_handler])

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
# Connect to fileserver
###########################

fileserver = fs.fileserver(config["ftpServerAddress"], config["username"], config["password"])
CONNECTED_TO_FTP = fileserver.connected()

# Go to custom directory on fileserver if specified
try:
    # Custom directory
    if config["ftpDirectory"] != "" and CONNECTED_TO_FTP:
        fileserver.change_directory(config["ftpDirectory"], True)

    # Custom camera directory
    if config["multipleCamerasOnServer"] and CONNECTED_TO_FTP:
        fileserver.change_directory(CAMERA_NAME, True)
except Exception as e:
    logging.warning("Could not change directory on fileserver: %s", str(e))

###########################
# Settings
###########################

# Try to download settings from server
try:
    if CONNECTED_TO_FTP:

        file_list = fileserver.list_files()

        # Check if settings file exists
        if "settings.yaml" in file_list:
            fileserver.download_file("settings.yaml", FILE_PATH)
        else:
            logging.warning("No settings file on server. Creating new file with default settings.")
            fileserver.upload_file("settings.yaml", "", FILE_PATH)
except Exception as e:
    logging.critical("Could not download settings file from FTP server: %s", str(e))

# Read settings file
try:
    settings1 = Settings()
    settings = settings1.get_settings()

except Exception as e:
    logging.critical("Could not open settings.yaml: %s", str(e))

###########################
# Time synchronization
###########################

try:
    wittyPi = WittyPi4()

    if settings["timeSync"] and CONNECTED_TO_FTP:
        wittyPi.sync_time_with_network()
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
        # TODO: Rund to nearest interval
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
    battery_voltage = wittyPi.get_battery_voltage()

    battery_voltage_half = settings["battery_voltage_half"]
    battery_voltage_quarter = settings["battery_voltage_half"]-(settings["battery_voltage_half"]-settings["low_voltage_threshold"])/2

    if battery_voltage_quarter < battery_voltage < battery_voltage_half:
        settings["intervalMinutes"] = int(settings["intervalMinutes"]*2)
        settings["repetitionsPerday"] = int(settings["repetitionsPerday"]/2)
        logging.warning("Battery voltage <50%.")
    elif battery_voltage < battery_voltage_quarter:
        settings["repetitionsPerday"] = 1
        logging.warning("Battery voltage <25%.")

except Exception as e:
    logging.warning("Could not get battery voltage: %s", str(e))

try:
    # Generate schedule
    wittyPi.generate_schedule(settings["startTimeHour"], settings["startTimeMinute"], settings["intervalMinutes"], settings["repetitionsPerday"])
except Exception as e:
    wittyPi.generate_schedule(8, 0, 30, 8)
    logging.warning("Failed to generate schedule: %s", str(e))

# Apply schedule
next_startup_time = wittyPi.apply_schedule()
next_startup_time = f"{next_startup_time}Z"

##########################
# SIM7600G-H 4G module
###########################

# See Waveshare documentation
try:
    sim7600 = SIM7600X()
except Exception as e:
    logging.warning("Could not open serial connection with 4G module: %s", str(e))

# Enable GPS
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
# Upload to fileserver and then delete last image
###########################

try:
    if CONNECTED_TO_FTP:
        # Upload all images
        for file in listdir(FILE_PATH):
            if file.endswith(".jpg"):
                fileserver.upload_file(file, "", FILE_PATH)

                # Delete uploaded image from Raspberry Pi
                remove(FILE_PATH + file)
except Exception as e:
    logging.critical("Could not upload image to fileserver: %s", str(e))

###########################
# Uploading sensor data to CSV
###########################

try:
    # If settings low voltage threshold exists
    if 2.0 <= settings["low_voltage_threshold"] <= 25.0 or settings["low_voltage_threshold"] == 0:
        wittyPi.set_low_voltage_threshold(settings["low_voltage_threshold"])

    # If settings recovery voltage threshold exists
    if 2.0 <= settings["recovery_voltage_threshold"] <= 25.0 or settings["recovery_voltage_threshold"] == 0:
        # TODO: Needs to be bigger than low_voltage_threshold
        wittyPi.set_recovery_voltage_threshold(settings["recovery_voltage_threshold"])

except Exception as e:
    logging.warning("Could not set voltage thresholds: %s", str(e))

###########################
# Get readings
###########################
temperature = "-"
internal_voltage = "-"
internal_current = "-"
signal_quality = "-"

try:
    temperature = wittyPi.get_temperature()
    internal_voltage = wittyPi.get_internal_voltage()
    internal_current = "-" # wittyPi.get_internal_current()
    signal_quality = sim7600.get_signal_quality()
except Exception as e:
    logging.warning("Could not get readings: %s", str(e))
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
            fileserver.append_file_from_bytes("diagnostics.csv", BytesIO(csvData))
        else:
            writer.writerow(newRow)
            csvData = csvBuffer.getvalue().encode('utf-8')

            # Append new row to local CSV file
            with open(f"{FILE_PATH}diagnostics.csv", 'a', newline='', encoding='utf-8') as file:
                file.write(csvData.decode('utf-8'))
except Exception as e:
    logging.warning("Could not append new measurements to log CSV: %s", str(e))

try:
    # fileserver.append_file("diagnostics.csv", "", FILE_PATH)

    # Upload WittyPi diagnostics
    if settings["uploadWittyPiDiagnostics"] and CONNECTED_TO_FTP:

        # Witty Pi log
        fileserver.append_file("wittyPi.log", "", "/home/pi/wittypi/")

        # Witty Pi schedule
        fileserver.append_file("schedule.log", "", "/home/pi/wittypi/")

except Exception as e:
    logging.warning("Could not upload diagnostics data: %s", str(e))

###########################
# Quit FTP session
###########################
try:
    if CONNECTED_TO_FTP:
        fileserver.quit()
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
