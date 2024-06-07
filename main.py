'''GlacierCam firmware - see https://github.com/Eagleshot/GlacierCam for more information'''

from os import system, remove, listdir
from datetime import datetime, time
import logging
from logging.handlers import RotatingFileHandler
from picamera2 import Picamera2
from libcamera import controls
from yaml import safe_load
from sim7600x import SIM7600X
from witty_pi_4 import WittyPi4
from fileserver import FileServer
from settings import Settings
from data import Data

VERSION = "1.0.0.alpha3"

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

CAMERA_NAME = get_cpu_serial() # Unique hardware serial number
FILE_PATH = "/home/pi/"  # Path where files are saved
data = Data()
data.add('version', VERSION)


# Error logging
file_handler = RotatingFileHandler(f"{FILE_PATH}log.txt", mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logging.basicConfig(level=logging.WARNING, handlers=[file_handler, stream_handler])

# Read config file from SD card
try:
    with open(f"{FILE_PATH}config.yaml", 'r', encoding='utf-8') as file:
        config = safe_load(file)
except Exception as e:
    logging.critical("Could not open config.yaml: %s", str(e))

###########################
# Connect to fileserver
###########################

fileserver = FileServer(config["ftpServerAddress"], config["username"], config["password"])
CONNECTED_TO_SERVER = fileserver.connected()

# Go to custom directory on fileserver if specified
try:
    # Custom directory
    if config["ftpDirectory"] != "" and CONNECTED_TO_SERVER:
        fileserver.change_directory(config["ftpDirectory"], True)

    # Custom camera directory
    if config["multipleCamerasOnServer"] and CONNECTED_TO_SERVER:
        fileserver.change_directory(CAMERA_NAME, True)
except Exception as e:
    logging.warning("Could not change directory on fileserver: %s", str(e))

###########################
# Settings
###########################
try:
    if CONNECTED_TO_SERVER:
        file_list = fileserver.list_files()

        # Check if settings file exists
        if "settings.yaml" in file_list:
            fileserver.download_file("settings.yaml", FILE_PATH)
        else:
            logging.warning("No settings file on server. Creating new file with default settings.")
            fileserver.upload_file("settings.yaml", FILE_PATH)
except Exception as e:
    logging.critical("Could not download settings file from FTP server: %s", str(e))

try: # Read settings file
    settings = Settings(f"{FILE_PATH}settings.yaml")
except Exception as e:
    logging.critical("Could not open settings.yaml: %s", str(e))

try: # Set log level according to settings
    logging.getLogger().setLevel(settings.get("logLevel"))
except Exception as e:
    logging.warning("Could not change log level: %s", str(e))

###########################
# Time synchronization
###########################
try:
    wittyPi = WittyPi4()

    if settings.get("timeSync") and CONNECTED_TO_SERVER:
        wittyPi.sync_time_with_network()
except Exception as e:
    logging.warning("Could not synchronize time with network: %s", str(e))

TIMESTAMP_CSV = datetime.today().strftime('%Y-%m-%d %H:%MZ') # UTC-Time
TIMESTAMP_FILENAME = datetime.today().strftime('%Y%m%d_%H%MZ') # UTC-Time
data.add('timestamp', TIMESTAMP_CSV)

###########################
# Generate schedule
###########################
try:
    battery_voltage = wittyPi.get_battery_voltage()
    data.add('battery_voltage', battery_voltage)

    battery_voltage_half = settings.get("batteryVoltageHalf")
    battery_voltage_quarter = (battery_voltage_half-settings.get("lowVoltageThreshold"))*0.5

    # Battery voltage between 50% and 25%
    if battery_voltage_quarter < battery_voltage < battery_voltage_half:
        settings.set("intervalMinutes", int(settings.get("intervalMinutes")*2)) # TODO
        logging.warning("Battery voltage <50%.")
    elif battery_voltage <= battery_voltage_quarter: # Battery voltage <=25%
        settings.set("repetitionsPerday", 1) # TODO
        logging.warning("Battery voltage <=25%.")

except Exception as e:
    logging.warning("Could not get battery voltage: %s", str(e))

try:
    wittyPi.set_interval_length(settings.get("intervalMinutes"), settings.get("intervalHours"))

    if settings.get("enableSunriseSunset"): #TODO
        wittyPi.set_start_end_time_sunrise(settings.get("latitude"), settings.get("longitude"))
    else:
        wittyPi.set_start_time(time(settings.get("startTimeHour"), settings.get("startTimeMinute")))
        wittyPi.set_end_time(time(settings.get("endTimeHour"), settings.get("endTimeMinute")))

    wittyPi.generate_schedule()
except Exception as e:
    logging.warning("Failed to generate schedule: %s", str(e))

###########################
# Apply schedule
###########################
try:
    next_startup_time = wittyPi.apply_schedule()
    data.add('next_startup_time', f"{next_startup_time}Z")
except Exception as e:
    logging.critical("Could not apply schedule: %s", str(e))

##########################
# SIM7600G-H 4G module
###########################
try:
    sim7600 = SIM7600X()
except Exception as e:
    logging.warning("Could not open serial connection with 4G module: %s", str(e))

# Enable GPS to read out position later
try:
    if settings.get("enableGPS"):
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
    resolution = settings.get("resolution")

    if MIN_RESOLUTION < resolution[0] < MAX_RESOLUTION[0] and MIN_RESOLUTION < resolution[1] < MAX_RESOLUTION[1]:
        size = (resolution[0], resolution[1])
        cameraConfig = camera.create_still_configuration({"size": size})

except Exception as e:
    logging.critical("Could not setup camera: %s", str(e))

###########################
# Capture image
###########################
try:
    image_filename = f'{TIMESTAMP_FILENAME}_{settings.get("cameraName")}.jpg'
    camera.start_and_capture_file(FILE_PATH + image_filename, capture_mode=cameraConfig, delay=2, show_preview=False)
except Exception as e:
    logging.critical("Could not start camera and capture image: %s", str(e))

try:
    camera.stop()
except Exception as e:
    logging.warning("Could not stop camera: %s", str(e))

###########################
# Upload image(s) to file server
###########################
try:
    if CONNECTED_TO_SERVER:
        for file in listdir(FILE_PATH): # Upload all images
            if file.endswith(".jpg"):
                fileserver.upload_file(file, FILE_PATH)

                # Delete uploaded image from Raspberry Pi
                remove(FILE_PATH + file)
except Exception as e:
    logging.critical("Could not upload image to fileserver: %s", str(e))

###########################
# Set voltage thresholds
###########################
try:
    wittyPi.set_low_voltage_threshold(settings.get("lowVoltageThreshold"))
    wittyPi.set_recovery_voltage_threshold(settings.get("recoveryVoltageThreshold"))
except Exception as e:
    logging.warning("Could not set voltage thresholds: %s", str(e))

###########################
# Get readings
###########################
try:
    data.add('temperature', wittyPi.get_temperature())
    data.add('internal_voltage', wittyPi.get_internal_voltage())
    # data.add('internal_current', wittyPi.get_internal_current())
    data.add('signal_quality', sim7600.get_signal_quality())
except Exception as e:
    logging.warning("Could not get readings: %s", str(e))

###########################
# Get GPS position
###########################
try:
    if settings.get("enableGPS"):
        latitude, longitude, height, _ = sim7600.get_gps_position()
        sim7600.stop_gps_session()
        data.add('latitude', latitude)
        data.add('longitude', longitude)
        data.add('height', height)
except Exception as e:
    logging.warning("Could not get GPS coordinates: %s", str(e))

###########################
# Uploading sensor data
###########################

# Append new measurements to log or create new log file if none exists
try:
    DIAGNOSTICS_FILENAME = "diagnostics.yaml"
    diagnostics_filepath = f"{FILE_PATH}{DIAGNOSTICS_FILENAME}"

    # Check if is connected to file server
    if CONNECTED_TO_SERVER:
        data.load_diagnostics()
        fileserver.append_file_from_bytes(DIAGNOSTICS_FILENAME, data.get_data_as_bytes())
    else:
        # Append new measurement to local YAML file
        data.append_diagnostics_to_file()
except Exception as e:
    logging.warning("Could not append new measurements to log: %s", str(e))

###########################
# Upload log data
###########################
try:
    if CONNECTED_TO_SERVER:
        fileserver.append_file("log.txt", FILE_PATH)
        remove(f"{FILE_PATH}log.txt")

    if settings.get("uploadExtendedDiagnostics") and CONNECTED_TO_SERVER:
        fileserver.append_file("wittyPi.log", f"{FILE_PATH}wittypi/")
        fileserver.append_file("schedule.log", f"{FILE_PATH}wittypi/")
except Exception as e:
    logging.warning("Could not upload diagnostics data: %s", str(e))

###########################
# Quit file server session
###########################
try:
    if CONNECTED_TO_SERVER:
        fileserver.quit()
except Exception as e:
    logging.warning("Could not close file server session: %s", str(e))

###########################
# Shutdown Raspberry Pi if enabled
###########################
try:
    if settings.get("shutdown") or settings.get("shutdown") is None:
        logging.info("Shutting down now.")
        system("sudo shutdown -h now")
except Exception as e:
    system("sudo shutdown -h now")
