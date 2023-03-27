#www.datasheets.raspberrypi.com/camera/picamera2-manual.pdf
#www.docs.python.org/3/library/ftplib.html

# Import needed libraries
from picamera2 import Picamera2
import time
from datetime import datetime
from ftplib import FTP
import config
import os

# Filename -> current date/time
# TODO Automatic station name if name is already in use
cameraName = "station1"
imgFileName =  datetime.today().strftime('%d%m%Y_%H%M_') + cameraName + ".jpg"
imgFilePath = "/home/pi/Pictures/" # Path where image is saved

# Setup camera
camera = Picamera2()
cameraConfig = camera.create_still_configuration({"size":(4608, 2592)})

# Capture image
camera.start_and_capture_file(imgFilePath + imgFileName, capture_mode = cameraConfig, delay = 3, show_preview = False)
# camera.start_and_capture_file(imgFilePath + imgFileName, delay = 3, show_preview = False)

camera.stop() # Stop camera

# Upload picture to server
ftpServerAddress = config.ftpServerAddress
username = config.username
password = config.password

ftp = FTP(ftpServerAddress)
ftp.login(user = username, passwd = password)

# ftp.dir() # Directory listing
ftp.cwd("private") # Go to folder "private"

# Upload file
with open("/home/pi/Desktop/main.py", 'rb') as file:
    ftp.storbinary(f"STOR {'main.py'}", file)
    
# Upload last image
with open(imgFilePath + imgFileName, 'rb') as file:
    ftp.storbinary(f"STOR {imgFileName}", file)

# Download and read config file
# with open(imgFilePath + 'config.txt', 'wb') as fp: # Download
#    ftp.retrbinary('retr config.txt', fp.write)
    
ftp.quit()

with open(imgFilePath + 'config.txt', 'r') as fp: # Read
    
    if 'shutdown = true' in fp.read(): # Shutdown computer if defined in loop
        print('shutting down')
        os.system("sudo shutdown -h now")