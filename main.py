#!/usr/bin/python3
# -*- coding:utf-8 -*-

# Import required libraries
from picamera2 import Picamera2
from libcamera import controls
from ftplib import FTP
from datetime import datetime
from time import sleep
from csv import writer
from os import system, remove, listdir
from io import BytesIO, StringIO
from subprocess import check_output, STDOUT
from yaml import safe_load

###########################
# Readings
###########################
currentGPSPosLat = "-"
currentGPSPosLong = "-"
error = ""

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
try:
    ftp = FTP(config["ftpServerAddress"], timeout=120)
    ftp.login(user=config["username"], passwd=config["password"])
    connectedToFTP = True
except Exception as e:
    error += f"Could not connect to FTP server: {str(e)}"
    print(f"Could not connect to FTP server: {str(e)}")
    connectedToFTP = False

# Custom directory if specified
try:
    if config["ftpDirectory"] != "" and connectedToFTP == True:
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
    if config["multipleCamerasOnServer"] == True and connectedToFTP == True:
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

# TODO work with read only file system - OK?
# TODO Do some checks if downloaded settings were valid?

# Try to download settings from server
try:
    if connectedToFTP == True:
        with open(f"{filePath}settings.yaml", 'wb') as fp:  # Download
            ftp.retrbinary('RETR settings.yaml', fp.write)
except Exception as e:
    print(f'No config file found. Creating new settings file with default settings: {str(e)}')

    if connectedToFTP == True:
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
# Time synchronization
###########################

# TODO: Maybe check if wittypi was started with button and only sync time then?

def syncWittyPiTimeWithNetwork():
    try:
        command = "cd /home/pi/wittypi && . ./utilities.sh && net_to_system && system_to_rtc"
        output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True)
        output = output.replace("\n", "")
        print(f"Time synchronized with network: {output}")
    except Exception as e:
        error += f"Could not synchronize time with network: {str(e)}"
        print(f"Could not synchronize time with network: {str(e)}")

try:
    if settings["timeSync"] == True:
        syncWittyPiTimeWithNetwork()
except Exception as e:
    error += f"Could not synchronize time with network: {str(e)}"
    print(f"Could not synchronize time with network: {str(e)}")

###########################
# Setup camera
###########################
camera = Picamera2()
cameraConfig = camera.create_still_configuration() # Automatically selects the highest resolution possible

# https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
# Table 6. Stream- specific configuration parameters

try:
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
    camera.start_and_capture_file(filePath + imgFileName, capture_mode=cameraConfig, delay=2, show_preview=False)
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
    if connectedToFTP == True:
        # Upload all images in filePath
        for file in listdir(filePath):
            if file.endswith(".jpg"):
                with open(filePath + file, 'rb') as imgFile:
                    ftp.storbinary(f"STOR {file}", imgFile)
                    print(f"Successfully uploaded {file}")

                    # Delete last image
                    remove(filePath + file)
except Exception as e:
    # TODO: Save image to USB drive
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
# def getWittyPiCurrent():
#     try:
#         command = "cd /home/pi/wittypi && . ./utilities.sh && get_output_current"
#         currentPowerDraw = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True) + "A"
#         currentPowerDraw = currentPowerDraw.replace("\n", "")
#         print(f"Output current: {currentPowerDraw}")
#         return currentPowerDraw
#     except Exception as e:
#         error += f"Could not get Raspberry Pi current: {str(e)}"
#         print(f"Could not get Raspberry Pi current: {str(e)}")
#         return "-"

# Get WittyPi readings
currentTemperature = getWittyPiTemperature()
currentBatteryVoltage = getWittyPiBatteryVoltage()
raspberryPiVoltage = getWittyPiVoltage()
currentPowerDraw = "-" # getWittyPiCurrent()

###########################
# Schedule script
###########################
def generate_schedule(startTimeHour, startTimeMinute, intervalMinutes, maxDurationMinute, repetitionsPerday):

    # Basic validity check of parameters
    if startTimeHour < 0 or startTimeHour > 24:
        startTimeHour = 8
    
    if startTimeMinute < 0 or startTimeMinute > 60:
        startTimeMinute = 0

    if intervalMinutes < 0 or intervalMinutes > 1440:
        intervalMinutes = 30

    if maxDurationMinute < 0 or maxDurationMinute > 1440:
        maxDurationMinute = 5
    
    if repetitionsPerday < 0 or repetitionsPerday > 275:
        repetitionsPerday = 8
    
    if ((repetitionsPerday * intervalMinutes)  + startTimeMinute + (startTimeHour * 60)) > 1440:
        repetitionsPerday = 1

    # 2037 is the maximum year for WittyPi
    formattedStartTime = "{:02d}:{:02d}".format(startTimeHour, startTimeMinute)
    schedule = f"BEGIN\t2010-01-01 {formattedStartTime}:00\nEND\t2037-12-31 23:59:59\n"
    
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
    # TODO
    schedule = generate_schedule(settings["startTimeHour"], settings["startTimeMinute"], settings["intervalMinutes"], settings["maxDurationMinute"], settings["repetitionsPerday"])

    # Compare old schedule file to new one
    try:
        with open("/home/pi/wittypi/schedule.wpi", "r") as f:
            oldSchedule = f.read()
        
            if oldSchedule != schedule:

                # Write new schedule file
                print("Writing and applying new schedule file.")
            
                with open("/home/pi/wittypi/schedule.wpi", "w") as f:
                    f.write(schedule)

            else:
                print("Schedule did not change.")
    except:
        # Write a new file if it doesn't exist
        with open("/home/pi/wittypi/schedule.wpi", "x") as f:
            f.write(schedule)
except Exception as e:
    error += f"Failed to generate schedule: {str(e)}"
    print(f"Failed to generate schedule: {str(e)}")

try:
    # Apply new schedule
    command = "cd /home/pi/wittypi && sudo ./runScript.sh"
    output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True)
    output = output.split("\n")[1:3]

    # If output contains warning
    if "Warning" in output:
        syncWittyPiTimeWithNetwork() # Sync time and try again
        output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True)
        output = output.split("\n")[1:3]
        
    print(f"{output[0]}\n{output[1]}")
    error += f"{output[0]}, {output[1]}"
except Exception as e:
    error += f"Failed to apply schedule: {str(e)}"
    print(f"Failed to apply schedule: {str(e)}")

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
# def sendATCommand(command, back, timeout):
#     rec_buff = ''
#     ser.write((command+'\r\n').encode())
#     sleep(timeout)
#     if ser.inWaiting():
#         sleep(0.01)
#         rec_buff = ser.read(ser.inWaiting())
#     if back not in rec_buff.decode():
#         print(command + ' ERROR')
#         print(command + ' back:\t' + rec_buff.decode())
#         return 0
#     else:
#         return rec_buff.decode()

# Get current signal quality
def getCurrentSignalQuality():
    rec_buff = ''
    ser.write(('AT+CSQ'+'\r\n').encode())
    sleep(1)
    if ser.inWaiting():
        sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if 'OK' not in rec_buff.decode():
        print('Error getting signal quality - back:\t' + rec_buff.decode())
        return ""
    else:
        currentSignalQuality = rec_buff.decode()[8:10]
        currentSignalQuality = currentSignalQuality.replace("\n", "")
        return currentSignalQuality

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
# TODO
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
# TODO
currentSignalQuality = ""
try:
    currentSignalQuality = getCurrentSignalQuality()
    print(f"Cell signal quality: {currentSignalQuality}")
except Exception as e:
    error += f"Failed to get cell signal quality: {str(e)}"
    print(f"Failed to get cell signal quality: {str(e)}")

# Append new measurements to log CSV or create new CSV file if none exists
try:
    # TODO Offline mode
    with StringIO() as csvBuffer:
        writer = writer(csvBuffer)
        newRow = [currentTime, currentBatteryVoltage, raspberryPiVoltage, currentPowerDraw, currentTemperature, currentSignalQuality, currentGPSPosLat, currentGPSPosLong, error]
        writer.writerow(newRow)
        csvData = csvBuffer.getvalue().encode('utf-8')
        ftp.storbinary(f"APPE diagnostics.csv", BytesIO(csvData))
except Exception as e:
    # TODO Log to USB
    print(f"Could not append new measurements to log CSV: {str(e)}")

###########################
# Quit FTP session
###########################
try:
    if connectedToFTP == True:
        ftp.quit()
except Exception as e:
    print(f"Could not quit FTP session: {str(e)}")

###########################
# Shutdown Raspberry Pi if enabled
###########################
try:
    if settings["shutdown"] == True:
        print('Shutting down now.')
        system("sudo shutdown -h now")
except Exception as e:
    # Setting not found
    system("sudo shutdown -h now")

# TODO Add comments to settings.yaml and config.yaml