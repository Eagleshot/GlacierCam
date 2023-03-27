#!/bin/sh

# Install packages
PACKAGES="python3-picamera2 minicom p7zip-full"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y $PACKAGES 


# Waveshare SIM7600G-H 4G/LTE HAT
sudo raspi-config nonint do_serial 2 # Enable serial port communication
exec wget https://www.waveshare.com/w/upload/2/29/SIM7600X-4G-HAT-Demo.7z # Download SIm-7600G-H code
exec 7z x SIM7600X-4G-HAT-Demo.7z -r -o/home/pi # Unzip code
sudo chmod 777 -R /home/pi/SIM7600X-4G-HAT-Demo # Make code executable
sudo sed -i -e '$i sh /home/pi/SIM7600X-4G-HAT-Demo/Raspberry/c/sim7600_4G_hat_init &' /etc/rc.local
cd /home/pi/SIM7600X-4G-HAT-Demo/Raspberry/c/bcm2835
chmod +x configure && ./configure && sudo make && sudo make install

# Download python script to /home/pi
exec wget -O /home/pi/main.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/main.py
sudo chmod +x /home/pi/main.py # Execution permissions
sudo sed -i -e '$i/home/pi/main.py &' /etc/rc.local # Enable python script to run on boot



# Enable camera and other hardware interfaces
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_i2c 0

# Disable LED and other unused hardware
# sudo raspi-config nonint do_led 1

# TODO Enable read-only filesystem


