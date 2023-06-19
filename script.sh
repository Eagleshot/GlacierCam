#!/bin/bash -e

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
echo '|       Step 1: Update the Raspberry Pi and install required packages          |'
echo '|                                                                              |'
echo '================================================================================'
echo ''

# Install required packages
PACKAGES=(
  "minicom"
  "p7zip-full"
  "pyserial"
  "ufw") # picamera2 is preinstalled
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ${PACKAGES[@]}
sudo apt-get autoremove -y

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|       Step 2: Install WittyPi Software                                       |'
echo '|                                                                              |'
echo '================================================================================'
# Install WittyPi Software 
wget https://www.uugear.com/repo/WittyPi4/install.sh && sudo sh install.sh

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|       Step 3: Install Waveshare SIM7600G-H 4G/LTE HAT driver                 |'
echo '|                                                                              |'
echo '================================================================================'
echo ''
# Install Waveshare SIM7600G-H 4G/LTE HAT driver
sudo raspi-config nonint do_serial 2 # Enable serial port communication

wget "https://www.waveshare.com/w/upload/4/4e/SIM7600X-4G-HAT(B)-Demo.7z" -P /tmp # Download SIm-7600G-H code
7z x /tmp/SIM7600X-4G-HAT\(B\)-Demo.7z -o/home/pi/ # Unzip code
sudo chmod 777 -R /home/pi/SIM7600X-4G-HAT\(B\)-Demo # Make code executable
sudo sed -i '$i sh /home/pi/SIM7600X-4G-HAT\(B\)-Demo/Raspberry/c/sim7600_4G_hat_init &' /etc/rc.local
cd /home/pi/SIM7600X-4G-HAT\(B\)-Demo/Raspberry/c/bcm2835
chmod +x configure && ./configure && make && sudo make install

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|       Step 4: Install Python script                                          |'
echo '|                                                                              |'
echo '================================================================================'
# Download python script to /home/pi
wget -O /home/pi/main.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/main.py
sudo chmod +x /home/pi/main.py # Execution permissions

# Download config.py
wget -O /home/pi/config.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/config.py

# Download settings.py
wget -O /home/pi/settings.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/settings.py

# Add main.py to wittyPi afterStartup.sh
echo "/usr/bin/python3 /home/pi/main.py" >> /home/pi/wittyPi/afterStartup.sh

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|       Step 5: Configure Raspberry Pi                                         |'
echo '|                                                                              |'
echo '================================================================================'
echo ''

# Enable camera and other hardware interfaces
sudo raspi-config nonint do_camera 0

# Disable LED and other unused hardware
echo "boot_delay=0" | sudo tee -a /boot/config.txt
echo "disable_splash=1" | sudo tee -a /boot/config.txt
echo "dtparam=act_led_trigger=none" | sudo tee -a /boot/config.txt
echo "dtoverlay=disable-bt" | sudo tee -a /boot/config.txt
echo "dtoverlay=disable-wifi" | sudo tee -a /boot/config.txt

# Enable the firewall
sudo ufw enable

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|              Glacier Camera Software Installation Completed!  :)             |'
echo '|                                                                              |'
echo '================================================================================'
