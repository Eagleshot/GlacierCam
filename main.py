#!/usr/bin/python3
# -*- coding:utf-8 -*-

# TODO Better exception handling

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
    '''Get the serial number of Raspberry Pi CPU'''
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
        connectedToFTP = True
        break
    except Exception as e:
        if i > 1:
            error += f"Could not connect to FTP server: {str(e)}, attempt {i+1}/5 failed - trying again in 5 seconds."
        print(f"Could not connect to FTP server: {str(e)}, attempt {i+1}/5 failed - trying again in 5 seconds.")
        connectedToFTP = False  
        sleep(5) # Wait 5 seconds and try again

# Go to custom directory in FTP server if specified
try:
    if config["ftpDirectory"] != "" and connectedToFTP:
        try:
            ftp.cwd(config["ftpDirectory"])
        except:
            ftp.mkd(config["ftpDirectory"])
            ftp.cwd(config["ftpDirectory"])
except Exception as e:
    error += f"Could not change directory on FTP server: {str(e)}"
    print(f"Could not change directory on FTP server: {str(e)}")

# Go to folder with camera name + unique hardware serial number or create it
try:
    if config["multipleCamerasOnServer"] and connectedToFTP:
        try:
            ftp.cwd(cameraName)
        except:
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
    if connectedToFTP:
        
        fileList = ftp.nlst()

        # Check if settings file exists
        if "settings.yaml" in fileList:
            with open(f"{FILE_PATH}settings.yaml", 'wb') as fp:  # Download
                ftp.retrbinary('RETR settings.yaml', fp.write)
        else:
            print("No settings file found on FTP server. Creating new settings file with default settings.")
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

def sync_witty_pi_time_with_network():
    '''Sync WittyPi clock with network time'''

    # See: https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-how-to-synchronise-time-with-internet-on-boot/
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && net_to_system && system_to_rtc"
        output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=10)
        output = output.replace("\n", "")
        print(f"Time synchronized with network: {output}")
    except Exception as e:
        # error += f"Could not synchronize time with network: {str(e)}" # TODO Return error value
        print(f"Could not synchronize time with network: {str(e)}")

try:
    if settings["timeSync"] and connectedToFTP:
        sync_witty_pi_time_with_network()
except Exception as e:
    error += f"Could not synchronize time with network: {str(e)}"
    print(f"Could not synchronize time with network: {str(e)}")

###########################
# Schedule script
###########################
def generate_schedule(startTimeHour: int, startTimeMinute: int, intervalMinutes: int, maxDurationMinute: int, repetitionsPerday: int):
    '''Generate a startup schedule file for WittyPi'''

    # Basic validity check of parameters
    if startTimeHour < 0 or startTimeHour >= 24:
        startTimeHour = 8
    
    if startTimeMinute < 0 or startTimeMinute > 60:
        startTimeMinute = 0

    if intervalMinutes < 0 or intervalMinutes > 1440:
        intervalMinutes = 30

    if maxDurationMinute < 0 or maxDurationMinute > 1440:
        maxDurationMinute = 5
    
    if repetitionsPerday < 0 or repetitionsPerday > 275:
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
    remainingMinutes = 1440 - (repetitionsPerday * intervalMinutes) + (intervalMinutes - maxDurationMinute)
    remainingHours = remainingMinutes // 60
    remainingMinutes = remainingMinutes % 60

    schedule += f"OFF\tH{remainingHours}"
    if remainingMinutes > 0:
        schedule += f" M{remainingMinutes}"
    
    return schedule

try:
    schedule = generate_schedule(settings["startTimeHour"], settings["startTimeMinute"], settings["intervalMinutes"], settings["maxDurationMinute"], settings["repetitionsPerday"])
except Exception as e:
    error += f"Failed to generate schedule with setting: {str(e)}"
    print(f"Failed to generate schedule with setting: {str(e)}")

    schedule = generate_schedule(8, 0, 30, 5, 8)

# Compare old schedule file to new one
# TODO Rewrite with better RWX permissions
try:
    with open("/home/pi/wittypi/schedule.wpi", "r", encoding='utf-8') as f:
        oldSchedule = f.read()
        
        if oldSchedule != schedule:
                
            # Write new schedule file
            print("Writing and applying new schedule file.")
            
            with open("/home/pi/wittypi/schedule.wpi", "w", encoding='utf-8') as f:
                f.write(schedule)

        else:
            print("Schedule did not change.")
except:
    # TODO: What if folder does not exist?
    # Write a new file if it doesn't exist
    with open("/home/pi/wittypi/schedule.wpi", "x", encoding='utf-8') as f:
        f.write(schedule)

try:
    # Apply new schedule
    command = "cd /home/pi/wittypi && sudo ./runScript.sh"
    output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=10)
    output = output.split("\n")[1:3]

    # If output contains warning
    if "Warning" in output[1]:
        sync_witty_pi_time_with_network() # Sync time and try again
        output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=10)
        output = output.split("\n")[1:3]

    print(f"{output[0]}\n{output[1]}")
    nextStartupTime = output[1][-19:]
except Exception as e:
    error += f"Failed to apply schedule: {str(e)}"
    print(f"Failed to apply schedule: {str(e)}")
    nextStartupTime = "-"

##########################
# SIM7600G-H 4G module
###########################

# Send AT command to SIM7600X
def sendATCommand(command, back, timeout):
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    sleep(timeout)
    if ser.inWaiting():
        sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if back not in rec_buff.decode():
        print(command + ' ERROR')
        print(command + ' back:\t' + rec_buff.decode())
        return 0
    
    return rec_buff.decode()
    
# Get current signal quality
# https://www.manualslib.com/download/1593302/Simcom-Sim7000-Series.html
# 0 -115 dBm or less
# 1 -111 dBm
# 2...30 -110... -54 dBm
# 31 -52 dBm or greater
# 99 not known or not detectable
def getCurrentSignalQuality():
    try:
        rec_buff = ''
        ser.write(('AT+CSQ\r\n').encode())
        sleep(1)
        if ser.inWaiting():
            sleep(0.01)
            rec_buff = ser.read(ser.inWaiting())
        if 'OK' not in rec_buff.decode():
            print('Error getting signal quality - back:\t' + rec_buff.decode())
            return ""
        
        currentSignalQuality = rec_buff.decode()[8:10]
        currentSignalQuality = currentSignalQuality.replace("\n", "")
        currentSignalQuality = ''.join(ch for ch in currentSignalQuality if ch.isdigit()) # Remove non-numeric characters
        return currentSignalQuality
    except Exception as e:
        # error += f"Could not get current signal quality: {str(e)}" # TODO
        print(f"Could not get current signal quality: {str(e)}")
        return ""

# Get GPS Position
currentGPSPosLat = "-"
currentGPSPosLong = "-"
currentGPSPosHeight = "-"

def getGPSPos(maxAttempts=7, delay=5):

    currentAttempt = 0

    while (currentAttempt < maxAttempts):

        currentAttempt += 1
        rec_buff = ''
        ser.write(('AT+CGPSINFO\r\n').encode())
        sleep(1)
        if ser.inWaiting():
            sleep(0.01)
            rec_buff = ser.read(ser.inWaiting())
        if rec_buff != '':
            if '+CGPSINFO: ' not in rec_buff.decode():
                print('Error:\t' + rec_buff.decode())
                sleep(delay)
            elif ',,,,,,' in rec_buff.decode(): # GPS Not ready
                sleep(delay)
            else:
                # Additions to Demo Code Written by Tim! -> Core Electronics
                # https://core-electronics.com.au/guides/raspberry-pi/raspberry-pi-4g-gps-hat/
                GPSDATA = str(rec_buff.decode())
                Cleaned = GPSDATA[13:]

                Lat = Cleaned[:2]
                SmallLat = Cleaned[2:11]
                NorthOrSouth = Cleaned[12]

                Long = Cleaned[14:17]
                SmallLong = Cleaned[17:26]
                EastOrWest = Cleaned[27]

                FinalLat = float(Lat) + (float(SmallLat)/60)
                FinalLong = float(Long) + (float(SmallLong)/60)

                if NorthOrSouth == 'S':
                    FinalLat = -FinalLat
                if EastOrWest == 'W':
                    FinalLong = -FinalLong

                # Height
                # TODO Sometimes heigth is not correctly extracted
                Height = Cleaned[45:49]

                global currentGPSPosLat
                global currentGPSPosLong
                global currentGPSPosHeight
                currentGPSPosLat = str(round(FinalLat, 5))
                currentGPSPosLong = str(round(FinalLong, 5))
                currentGPSPosHeight = str(Height)

                # TODO Time

                print(f"GPS position: LAT {currentGPSPosLat}, LON {currentGPSPosLong}, HEIGHT {currentGPSPosHeight}")
                return 1
        
    return 0
    
# See Waveshare documentation
try:
    # TODO: Test timeout
    ser = serial.Serial('/dev/ttyUSB2', 115200, parity=serial.PARITY_EVEN, timeout=10)  # USB connection
    ser.flushInput()
except Exception as e:
    error += f"Could not open serial connection with 4G module: {str(e)}"
    print (f"Could not open serial connection with 4G module: {str(e)}")

try:
    # Enable GPS to later read out position
    if settings["enableGPS"]:
        print('Start GPS session.')
        sendATCommand('AT+CGPS=1,1', 'OK', 1)
except Exception as e:
    error += f"Could not start GPS: {str(e)}"
    print(f"Could not start GPS: {str(e)}")

###########################
# Setup camera
###########################

try:
    camera = Picamera2()
    cameraConfig = camera.create_still_configuration() # Automatically selects the highest resolution possible

    # https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
    # Table 6. Stream- specific configuration parameters
    min_resolution = 64
    max_resolution = (4608, 2592)
    resolution = settings["resolution"]

    if min_resolution < resolution[0] < max_resolution[0] and min_resolution < resolution[1] < max_resolution[1]:
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
    if connectedToFTP:
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
def getWittyPiTemperature():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && get_temperature"
        currentTemperature = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=5)
        currentTemperature = currentTemperature.replace("\n", "")
        currentTemperature = currentTemperature.split(" / ", maxsplit = 1)[0] # Remove the Farenheit reading
        currentTemperature = currentTemperature[:-2] # Remove °C
        print(f"Temperature: {currentTemperature} °C")
        return currentTemperature
    except Exception as e:
        # error += f"Could not get temperature: {str(e)}" # TODO Return error value
        print(f"Could not get temperature: {str(e)}")
        return "-"

# Battery voltage
def getWittyPiBatteryVoltage():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && get_input_voltage"
        currentBatteryVoltage = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=5)
        currentBatteryVoltage = currentBatteryVoltage.replace("\n", "")
        print(f"Battery voltage: {currentBatteryVoltage} V")
        return currentBatteryVoltage
    except Exception as e:
        # error += f"Could not get battery voltage: {str(e)}" # TODO Return error value
        print(f"Could not get battery voltage: {str(e)}")
        return "-"

# Raspberry Pi voltage
# TODO Maybe make setting a setting to enable/disable additional sensor readings in the future
def getWittyPiVoltage():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && get_output_voltage"
        raspberryPiVoltage = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=5)
        raspberryPiVoltage = raspberryPiVoltage.replace("\n", "")
        print(f"Output voltage: {raspberryPiVoltage} V")
        return raspberryPiVoltage
    except Exception as e:
        # error += f"Could not get Raspberry Pi voltage: {str(e)}" # TODO Return error value
        print(f"Could not get Raspberry Pi voltage: {str(e)}")
        return "-"

# Raspberry Pi current
# Not needed at the moment
# def getWittyPiCurrent():
#     try:
#         command = "cd /home/pi/wittypi && . ./utilities.sh && get_output_current"
#         currentPowerDraw = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=5)
#         currentPowerDraw = currentPowerDraw.replace("\n", "")
#         print(f"Output current: {currentPowerDraw} A")
#         return currentPowerDraw
#     except Exception as e:
#         # error += f"Could not get Raspberry Pi current: {str(e)}" # TODO Return error value
#         print(f"Could not get Raspberry Pi current: {str(e)}")
#         return "-"

###########################
# Get readings
###########################
currentTemperature = getWittyPiTemperature()
currentBatteryVoltage = getWittyPiBatteryVoltage()
raspberryPiVoltage = getWittyPiVoltage()
currentPowerDraw = "-" # getWittyPiCurrent()
currentSignalQuality = getCurrentSignalQuality()

###########################
# Get GPS position
###########################
try:
    if settings["enableGPS"]:
        getGPSPos()
        print('Stopping GPS session.')
        sendATCommand('AT+CGPS=0', 'OK', 1)

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
        newRow = [currentTimeCSV, nextStartupTime, currentBatteryVoltage, raspberryPiVoltage, currentPowerDraw, currentTemperature, currentSignalQuality, currentGPSPosLat, currentGPSPosLong, currentGPSPosHeight, error]

        # Check if is connected to FTP server
        if connectedToFTP:
            # Check if local CSV file exists
            try:
                if path.exists(f"{FILE_PATH}diagnostics.csv"):
                    with open(f"{FILE_PATH}diagnostics.csv", 'r') as file:
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
            with open(f"{FILE_PATH}diagnostics.csv", 'a', newline='') as file:
                file.write(csvData.decode('utf-8'))
except Exception as e:
    print(f"Could not append new measurements to log CSV: {str(e)}")

try:
    # Upload WittyPi diagnostics
    if settings["uploadWittyPiDiagnostics"] and connectedToFTP:

            # Witty Pi log 
            with open("/home/pi/wittypi/wittyPi.log", 'rb') as wittyPiDiagnostics:
                ftp.storbinary("APPE wittyPiDiagnostics.txt", wittyPiDiagnostics)

            # Witty Pi schedule
            with open("/home/pi/wittypi/schedule.log", 'rb') as wittyPiDiagnostics:
                ftp.storbinary("APPE wittyPiSchedule.txt", wittyPiDiagnostics)
except Exception as e:
    print(f"Could not upload WittyPi diagnostics: {str(e)}")

###########################
# Close serial connection
###########################
try:
    ser.close()
except Exception as e:
    print(f"Could not close serial connection: {str(e)}")

###########################
# Quit FTP session
###########################
try:
    if connectedToFTP:
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
