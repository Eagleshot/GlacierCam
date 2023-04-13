#!/usr/bin/python3
# -*- coding:utf-8 -*-

# Import required libraries
from picamera2 import Picamera2
from ftplib import FTP
from datetime import datetime
import time
import config
import csv
import RPi.GPIO as GPIO
import os
import io

###########################
# Filenames
###########################

# Get unique hardware id of Raspberry Pi
# See: https://raspberrypi.stackexchange.com/questions/2086/how-do-i-get-the-serial-number


def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial


cpuSerial = getserial()

cameraName = config.cameraName
imgFileName = datetime.today().strftime('%d%m%Y_%H%M_') + cameraName + ".jpg"
imgFilePath = "/home/pi/"  # Path where image is saved

###########################
# Readings
###########################
csvFileName = "diagnostics.csv"
currentTime = datetime.today().strftime('%d-%m-%Y %H:%M')
currentBatteryLevel = "80"  # TODO
currentTemperature = "25.5"  # TODO
currentSignalQuality = ""  # TODO
currentGPSPosLat = ""
currentGPSPosLong = ""
error = ""

###########################
# SIM7600X
###########################
# See Waveshare documentation
try:
    import serial
    ser = serial.Serial('/dev/ttyUSB2', 115200)  # USB connection
    ser.flushInput()
except:
    error += "Could not open serial port."
    print("Could not open serial port.")

power_key = 6
rec_buff = ''
rec_buff2 = ''
time_count = 0


def send_at2(command, back, timeout):
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if back not in rec_buff.decode():
        print(command + ' ERROR')
        print(command + ' back:\t' + rec_buff.decode())
        return 0
    else:
        return rec_buff.decode()

# Get GPS Position


def send_at(command, back, timeout):
    rec_buff = ''
    ser.write((command+'\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.01)
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
            #print(Lat, SmallLat, NorthOrSouth)

            Long = Cleaned[14:17]
            SmallLong = Cleaned[17:26]
            EastOrWest = Cleaned[27]
            #print(Long, SmallLong, EastOrWest)

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


###########################
# Setup camera
###########################
camera = Picamera2()
cameraConfig = camera.create_still_configuration(
    {"size": (4608, 2592)})  # TODO

###########################
# Capture image
###########################
try:
    camera.start_and_capture_file(
        imgFilePath + imgFileName, capture_mode=cameraConfig, delay=3, show_preview=False)
except:
    error += "Could not start camera and capture image."
    print("Could not start camera and capture image.")

###########################
# Stop camera
###########################
try:
    camera.stop()
except:
    error += "Camera already stopped."
    print("Camera already stopped.")

###########################
# Upload picture to server
###########################
ftpServerAddress = config.ftpServerAddress
username = config.username
password = config.password

# TODO consider FTP_TLS, timeout = 3 minutes
ftp = FTP(ftpServerAddress, timeout=180)
ftp.login(user=username, passwd=password)

# ftp.dir() # Directory listing
ftp.cwd("private")  # Go to folder "private" TODO remove?

# Go to folder with camera name + unique hardware serial number or create it
folderName = cameraName + "_" + cpuSerial
try:
    ftp.cwd(folderName)
except:
    ftp.mkd(folderName)
    ftp.cwd(folderName)

###########################
# Upload to ftp server and then delete last image
###########################
try:
    with open(imgFilePath + imgFileName, 'rb') as file:
        ftp.storbinary(f"STOR {imgFileName}", file)
        print(f"Successfully uploaded {imgFileName}")

    # Delete last image
    os.remove(imgFilePath + imgFileName)

except:
    error += "Could not open image."
    print("Could not open image.")

###########################
# Upload main.py (this file)
###########################
# TODO remove after development
# with open("/home/pi/main.py", 'rb') as file:
#     ftp.storbinary(f"STOR {'main.py'}", file)

###########################
# Uploading sensor data to CSV
###########################

# Get GPS position
# SIM7600X-Module is already turned on
try:
    answer = 0
    print('Start GPS session.')
    rec_buff = ''
    send_at('AT+CGPS=1,1', 'OK', 1)
    time.sleep(2)
    maxAttempts = 0

    while (maxAttempts <= 35):
        maxAttempts += 1
        answer = send_at('AT+CGPSINFO', '+CGPSINFO: ', 1)
        if answer == 1:  # Success
            break
        else:
            print('error %d' % answer)
            send_at('AT+CGPS=0', 'OK', 1)
            time.sleep(1.5)
except:
    error += "Failed to get GPS coordinates"
    print("Failed to get GPS coordinates")

# Get cell signal quality
try:
    currentSignalQuality = send_at2('AT+CSQ', 'OK', 1)[8:13]
    print("Cell signal quality: " + currentSignalQuality)
except:
    error += "Failed to get cell signal quality"
    print("Failed to get cell signal quality")
# Upload data to server
newRow = [currentTime, currentBatteryLevel, currentTemperature,
          currentSignalQuality, currentGPSPosLat, currentGPSPosLong, error]

# Append new measurements to log CSV or create new CSV file if none exists
with io.StringIO() as csvBuffer:
    writer = csv.writer(csvBuffer)
    writer.writerow(newRow)
    csvData = csvBuffer.getvalue().encode('utf-8')
    ftp.storbinary(f"APPE {csvFileName}", io.BytesIO(csvData))

###########################
# Download and read config file
###########################
try:
    with open('/home/pi/config.txt', 'wb') as fp:  # Download
        ftp.retrbinary('RETR config.txt', fp.write)
except:
    print("Could not find config file!")

ftp.quit()

with open('/home/pi/config.txt', 'r') as fp:  # Read

    if 'shutdown = true' in fp.read():  # Shutdown computer if defined in loop
        print('shutting down')
        os.system("sudo shutdown -h now")
