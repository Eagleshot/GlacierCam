#!/bin/sh

# Install packages
PACKAGES="python3-picamera2 minicom"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y $PACKAGES 

# Download python script to /home/pi
exec wget -O /home/pi/main.py https://raw.githubusercontent.com/Eagleshot/main/master/main.py

# Enable python script to run on boot
sudo chmod +x /home/pi/main.py # Execution permissions
sudo sed -i '$i/home/pi/main.py &' /etc/rc.local

# TODO Give python script permissions needed to run

# Enable camera and other hardware interfaces
sudo raspi-config nonint do_camera 0

# Disable LED and other unused hardware
sudo raspi-config nonint do_led 1
sudo raspi-config nonint do_i2c 1
sudo raspi-config nonint do_spi 1
sudo raspi-config nonint do_serial 1

# TODO Enable read-only filesystem


