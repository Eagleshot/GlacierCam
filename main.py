#!/usr/bin/python3
# -*- coding:utf-8 -*-

# Import required libraries
from picamera2 import Picamera2
from libcamera import controls
from ftplib import FTP
from datetime import datetime
from time import sleep
from csv import writer
from os import system, remove
from io import BytesIO, StringIO
from subprocess import check_output, STDOUT
from yaml import safe_load

# TODO: See https://pyyaml.org/wiki/PyYAMLDocumentation -> safe load / security

###########################
# Time synchronization
###########################

def syncWittyPiTimeWithNetwork():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && net_to_system && system_to_rtc"
        output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True)
        output = output.replace("\n", "")
        print(f"Time synchronized with network: {output}")
    except Exception as e:
        error += f"Could not synchronize time with network: {str(e)}"
        print(f"Could not synchronize time with network: {str(e)}")

syncWittyPiTimeWithNetwork()

###########################
# Configuration and filenames
###########################
# Get unique hardware id of Raspberry Pi
# See: https://www.raspberrypi.com/documentation/computers/config_txt.html#the-serial-number-filter
# and https://raspberrypi.stackexchange.com/questions/2086/how-do-i-get-the-serial-number
def getCPUSerial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    cpuserial = line[10:26]
                    break
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

filePath = "/home/pi/"  # Path where files are saved

# Read config.yaml file
try:
    with open(f"{filePath}config.yaml", 'r') as file:
        config = safe_load(file)
except Exception as e:
    print(f"Could not open config.yaml: {str(e)}")

cameraName = f"{config['cameraName']}_{getCPUSerial()}" # Camera name + unique hardware serial
currentTime = datetime.today().strftime('%d%m%Y_%H%M')
imgFileName = f"{currentTime}_{cameraName}.jpg"

###########################
# Connect to FTP server
###########################
ftp = FTP(config["ftpServerAddress"], timeout=120)
ftp.login(user=config["username"], passwd=config["password"])

# Custom directory if specified
if config["ftpDirectory"] != "":
    try:
        ftp.cwd(config["ftpDirectory"])
    except:
        ftp.mkd(config["ftpDirectory"])
        ftp.cwd(config["ftpDirectory"])

# Go to folder with camera name + unique hardware serial number or create it
if config["multipleCamerasOnServer"] == True:
    try:
        ftp.cwd(cameraName)
    except:
        ftp.mkd(cameraName)
        ftp.cwd(cameraName)

###########################
# Settings
###########################

# TODO work with read only file system - OK?
# TODO Fix upload settings.yaml -> NEEDS SUDO
# TODO Do some checks if downloaded settings were valid?

# Try to download settings from server
try:
    with open(f"{filePath}settings.yaml", 'wb') as fp:  # Download
        ftp.retrbinary('RETR settings.yaml', fp.write)
except Exception as e:
    print(f'No config file found. Creating new settings file with default settings: {str(e)}')

    # Upload config file if none exists
    with open(f"{filePath}settings.yaml", 'rb') as fp:  # Download
        ftp.storbinary('STOR settings.yaml', fp)

# Read settings file
try:
    with open(f"{filePath}settings.yaml", 'r') as file:
        settings = safe_load(file)
except Exception as e:
    print(f"Could not open settings.yaml: {str(e)}")

###########################
# Readings
###########################
csvFileName = "diagnostics.csv"
currentSignalQuality = ""
currentGPSPosLat = "-"
currentGPSPosLong = "-"
error = ""

###########################
# Setup camera
###########################
camera = Picamera2()
cameraConfig = camera.create_still_configuration() # Automatically selects the highest resolution possible

# TODO Camera resolution
# https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
# Table 6. Stream- specific configuration parameters
if settings["resolution"] != ["0", "0"]:
    try:
        cameraConfig = camera.create_still_configuration({"size": (settings["resolution"][0], settings["resolution"][1])})
    except Exception as e:
        error += f"Could not set camera resolution: {str(e)}"
        print(f"Could not set camera resolution: {str(e)}")

# TODO If -1 set to autofocus
if settings["lensPosition"] > -1:
    try:
        camera.set_controls({"AfMode": controls.AfModeEnum.Manual,
                            "LensPosition": settings["lensPosition"]})
    except Exception as e:
        error += f"Could not set lens position: {str(e)}"
        print(f"Could not set lens position: {str(e)}")
else:
    try:
        camera.set_controls({"AfMode": controls.AfModeEnum.Auto})
    except Exception as e:
        error += f"Could not set lens position: {str(e)}"
        print(f"Could not set lens position: {str(e)}")

###########################
# Capture image
###########################
try:
    camera.start_and_capture_file(filePath + imgFileName, capture_mode=cameraConfig, delay=3, show_preview=False)
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
    with open(filePath + imgFileName, 'rb') as file:
        ftp.storbinary(f"STOR {imgFileName}", file)
        print(f"Successfully uploaded {imgFileName}")

    # Delete last image
    remove(filePath + imgFileName)

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
        currentTemperature = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True)
        currentTemperature = currentTemperature.replace("\n", "")
        currentTemperature = currentTemperature.split(" / ")[0] # Remove the Farenheit reading
        print(f"Temperature: {currentTemperature}")
        return currentTemperature
    except Exception as e:
        error += f"Could not get temperature: {str(e)}"
        print(f"Could not get temperature: {str(e)}")
        return "-"

# Battery voltage
def getWittyPiBatteryVoltage():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && get_input_voltage"
        currentBatteryVoltage = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True) + "V"
        currentBatteryVoltage = currentBatteryVoltage.replace("\n", "")
        print(f"Battery voltage: {currentBatteryVoltage}")
        return currentBatteryVoltage
    except Exception as e:
        error += f"Could not get battery voltage: {str(e)}"
        print(f"Could not get battery voltage: {str(e)}")
        return "-"

# Raspberry Pi voltage
def getWittyPiVoltage():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && get_output_voltage"
        raspberryPiVoltage = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True) + "V"
        raspberryPiVoltage = raspberryPiVoltage.replace("\n", "")
        print(f"Output voltage: {raspberryPiVoltage}")
        return raspberryPiVoltage
    except Exception as e:
        error += f"Could not get Raspberry Pi voltage: {str(e)}"
        print(f"Could not get Raspberry Pi voltage: {str(e)}")
        return "-"

# Raspberry Pi current
def getWittyPiCurrent():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && get_output_current"
        currentPowerDraw = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True) + "A"
        currentPowerDraw = currentPowerDraw.replace("\n", "")
        print(f"Output current: {currentPowerDraw}")
        return currentPowerDraw
    except Exception as e:
        error += f"Could not get Raspberry Pi current: {str(e)}"
        print(f"Could not get Raspberry Pi current: {str(e)}")
        return "-"

# Get WittyPi readings
currentTemperature = getWittyPiTemperature()
currentBatteryVoltage = getWittyPiBatteryVoltage()
raspberryPiVoltage = getWittyPiVoltage()
currentPowerDraw = getWittyPiCurrent()

##########################
# SIM7600G-H 4G module
###########################
# See Waveshare documentation
try:
    import serial
    ser = serial.Serial('/dev/ttyUSB2', 115200)  # USB connection
    ser.flushInput()
except Exception as e:
    error += f"Could not open serial connection with 4G module: {str(e)}"
    print (f"Could not open serial connection with 4G module: {str(e)}")

# Send AT command to SIM7600X
def send_at(command, back, timeout):
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
    else:
        return rec_buff.decode()

# Get GPS Position
def getGPSPos(command, back, timeout):
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    sleep(timeout)
    if ser.inWaiting():
        sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if rec_buff != '':
        if back not in rec_buff.decode():
            print(command + ' ERROR')
            print(command + ' back:\t' + rec_buff.decode())
            return 0
        elif ',,,,,,' in rec_buff.decode():
            print('GPS is not ready')
            return 0
        else:
            # Additions to Demo Code Written by Tim! -> Core Electronics
            GPSDATA = str(rec_buff.decode())
            Cleaned = GPSDATA[13:]
            # print(Cleaned)

            Lat = Cleaned[:2]
            SmallLat = Cleaned[2:11]
            NorthOrSouth = Cleaned[12]
            # print(Lat, SmallLat, NorthOrSouth)

            Long = Cleaned[14:17]
            SmallLong = Cleaned[17:26]
            EastOrWest = Cleaned[27]
            # print(Long, SmallLong, EastOrWest)

            FinalLat = float(Lat) + (float(SmallLat)/60)
            FinalLong = float(Long) + (float(SmallLong)/60)

            if NorthOrSouth == 'S':
                FinalLat = -FinalLat
            if EastOrWest == 'W':
                FinalLong = -FinalLong

            FinalLongText = round(FinalLong, 7)
            FinalLatText = round(FinalLat, 7)

            global currentGPSPosLat
            global currentGPSPosLong
            currentGPSPosLat = str(FinalLatText)
            currentGPSPosLong = str(FinalLongText)

            print('Longitude:' + currentGPSPosLong +
                  ' Degrees - Latitude: ' + currentGPSPosLat + ' Degrees')

            return 1
    else:
        print('GPS is not ready')
        return 0

# Get GPS position
# SIM7600X-Module is already turned on
try:
    if settings["enableGPS"]  == True:
        answer = 0
        print('Start GPS session.')
        getGPSPos('AT+CGPS=1,1', 'OK', 1)
        sleep(2)
        maxAttempts = 0

        while (maxAttempts <= 10):
            maxAttempts += 1
            answer = getGPSPos('AT+CGPSINFO', '+CGPSINFO: ', 1)
            if answer == 1:  # Success
                break
            else:
                print('error %d' % answer)
                getGPSPos('AT+CGPS=0', 'OK', 1)
                sleep(1.5)
except Exception as e:
    error += f"Failed to get GPS coordinates: {str(e)}"
    print(f"Failed to get GPS coordinates: {str(e)}")

# Get cell signal quality
try:
    currentSignalQuality = send_at('AT+CSQ', 'OK', 1)[8:10]
    currentSignalQuality = currentSignalQuality.replace("\n", "")
    print(f"Cell signal quality: {currentSignalQuality}")
except Exception as e:
    error += f"Failed to get cell signal quality: {str(e)}"
    print(f"Failed to get cell signal quality: {str(e)}")

# Append new measurements to log CSV or create new CSV file if none exists
with StringIO() as csvBuffer:
    writer = writer(csvBuffer)
    newRow = [currentTime, currentBatteryVoltage, raspberryPiVoltage, currentPowerDraw, currentTemperature, currentSignalQuality, currentGPSPosLat, currentGPSPosLong, error]
    writer.writerow(newRow)
    csvData = csvBuffer.getvalue().encode('utf-8')
    ftp.storbinary(f"APPE {csvFileName}", BytesIO(csvData))

###########################
# Quit FTP session
###########################
try:
    ftp.quit()
except Exception as e:
    print(f"Could not quit FTP session: {str(e)}")

###########################
# Shutdown Raspberry Pi if enabled
###########################
if settings["shutdown"] == True:
    print('Shutting down now.')
    system("sudo shutdown -h now")
