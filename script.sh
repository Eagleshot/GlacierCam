#!/bin/sh

# Check if sudo is used
if [ "$(id -u)" != 0 ]; then
  echo 'This script must be run as sudo!'
  exit 1
fi

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|                   Glacier Camera Software Installation Script                |'
echo '|                                                                              |'
echo '================================================================================'
echo ''

# Install required packages
PACKAGES="minicom p7zip-full pyserial ufw" # picamera2 is preinstalled
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y $PACKAGES
sudo apt-get autoremove -y

# TODO: Sudo ufw enable?
# The firewall automatically blocks all incoming connections!
# https://www.raspberrypi.com/documentation/computers/configuration.html#install-a-firewall

# TODO Install wittyPi software
exec wget https://www.uugear.com/repo/WittyPi4/install.sh && sudo sh install.sh

# # Waveshare SIM7600G-H 4G/LTE HAT
# sudo raspi-config nonint do_serial 2 # Enable serial port communication
# exec wget "https://www.waveshare.com/w/upload/4/4e/SIM7600X-4G-HAT(B)-Demo.7z" # Download SIm-7600G-H code
# 7z x SIM7600X-4G-HAT-Demo.7z -r -o/home/pi/ # Unzip code
# sudo chmod 777 -R /home/pi/SIM7600X-4G-HAT-Demo # Make code executable
# sudo sed -i -e '$i sh /home/pi/SIM7600X-4G-HAT-Demo/Raspberry/c/sim7600_4G_hat_init &' /etc/rc.local
# cd /home/pi/SIM7600X-4G-HAT-Demo/Raspberry/c/bcm2835
# chmod +x configure && ./configure && sudo make && sudo make install

# # Download python script to /home/pi
exec wget -O /home/pi/main.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/main.py
sudo chmod +x /home/pi/main.py # Execution permissions
# Enable python script to run on boot
# TODO Do this with systemd
# https://www.youtube.com/watch?v=DUGZC-tNm2w
# sudo systemctl status myscript.service

# Download config.py
exec wget -O /home/pi/config.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/config.py

# Download settings.py
exec wget -O /home/pi/settings.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/settings.py

# Add python "/home/pi/main.py" wittyPi afterStartup.sh
# Enable camera and other hardware interfaces
sudo raspi-config nonint do_camera 0

# Disable LED and other unused hardware
# sudo raspi-config nonint do_led 1

# TODO Enable read-only filesystem


