#!/bin/bash -e

# Check if script is being run with sudo
if [ "$(id -u)" != 0 ]; then
  echo 'This script must be run as sudo or as root!'
  exit 1
fi

# TODO Maybe verify the changes/add some basic error handling

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
PACKAGES="minicom p7zip-full python3-pip ufw" # picamera2 is preinstalled

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y $PACKAGES
sudo apt-get autoremove -y

# Install pyserial with pip
sudo pip3 install pyserial

# Install pyyaml with pip
sudo pip3 install pyyaml

# Install suntime
sudo pip3 install suntime

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|         Step 2: Install Waveshare SIM7600G-H 4G/LTE HAT driver               |'
echo '|                                                                              |'
echo '================================================================================'
echo ''
# Install Waveshare SIM7600G-H 4G/LTE HAT driver
# See: https://core-electronics.com.au/guides/raspberry-pi/raspberry-pi-4g-gps-hat/ (slightly modified to work with the (B) version)
sudo raspi-config nonint do_serial 2 # Enable serial port communication

wget "https://www.waveshare.com/w/upload/4/4e/SIM7600X-4G-HAT(B)-Demo.7z" -P /tmp # Download SIm-7600G-H code
7z x /tmp/SIM7600X-4G-HAT\(B\)-Demo.7z -o/home/pi/ # Unzip code
mv /home/pi/SIM7600X-4G-HAT\(B\)-Demo /home/pi/SIM7600X-4G-HAT-B-Demo # Rename folder to remove brackets which cause issues
sudo chmod 777 -R /home/pi/SIM7600X-4G-HAT-B-Demo # Make code executable

# This part is not needed, because the (B) version does not use the GPIO pins for communication
# As this also interferes with GPIO 4, it has been disabled
# sudo sed -i '$i sh /home/pi/SIM7600X-4G-HAT-B-Demo/Raspberry/c/sim7600_4G_hat_init &' /etc/rc.local

cd /home/pi/SIM7600X-4G-HAT-B-Demo/Raspberry/c/bcm2835
chmod +x configure && ./configure && make && sudo make install

# TODO Maybe delete no longer deleted install files

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|                       Step 2: Download Python scripts                        |'
echo '|                                                                              |'
echo '================================================================================'
# Download python script to /home/pi
wget -O /home/pi/main.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/main.py
sudo chmod 777 /home/pi/main.py # Execution permissions

# Download sim7600x.py
wget -O /home/pi/sim7600x.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/sim7600x.py

# Download witty_pi_4.py
wget -O /home/pi/witty_pi_4.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/witty_pi_4.py

# Download config.yaml
wget -O /home/pi/config.yaml https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/config.yaml

# Download settings.yaml
wget -O /home/pi/settings.yaml https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/settings.yaml

echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|                     Step 3: Configure Raspberry Pi                           |'
echo '|                                                                              |'
echo '================================================================================'
echo ''

# See: https://www.raspberrypi.com/documentation/computers/configuration.html
# Enable camera and other hardware interfaces
sudo raspi-config nonint do_camera 0

# I2C should already activated by WittyPi script
sudo raspi-config nonint do_i2c 0

# Disable 1-wire interface
sudo raspi-config nonint do_onewire 1

# Disable LED and other unused hardware
echo "boot_delay=0" | sudo tee -a /boot/config.txt
echo "disable_splash=1" | sudo tee -a /boot/config.txt
echo "dtparam=act_led_trigger=none" | sudo tee -a /boot/config.txt
# echo "dtoverlay=disable-wifi" | sudo tee -a /boot/config.txt

# Add quiet flag to cmdline.txt to mute boot messages
# sudo sed -i 's/$/ quiet/' /boot/cmdline.txt

# Change the DNS server to Cloudflare and Google
echo "static domain_name_servers=1.1.1.1 8.8.8.8" | sudo tee -a /etc/dhcpcd.conf

# Enable the firewall
sudo ufw enable

# echo ''
# echo '================================================================================'
# echo '|                                                                              |'
# echo '|                    Step 5: Install WittyPi Software                          |'
# echo '|                                                                              |'
# echo '================================================================================'

# This was disabled, because it currently doesn't work because of permission
# TODO Maybe reenable in the future, once the root cause is found
# TODO: Disable UWI after installation - see https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-mini-disable-the-uwi-service/

# Install WittyPi Software
# See: https://www.uugear.com/product/witty-pi-4-mini/
# cd /home/pi
# wget https://www.uugear.com/repo/WittyPi4/install.sh
# sudo sh install.sh

# Add main.py to automatically run before wittyPi script
# echo "sudo /usr/bin/python3 /home/pi/main.py" >> /home/pi/wittypi/afterStartup.sh

# TODO Remove UWI
# See: https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-mini-disable-the-uwi-service/
# sudo update-rc.d uwi remove
# sudo rm /etc/init.d/uwi
# sudo rm -r ~/uwi


echo ''
echo '================================================================================'
echo '|                                                                              |'
echo '|              Glacier Camera Software Installation Completed!  :)             |'
echo '|                         Rebooting in 5 seconds...                            |'
echo '|                                                                              |'
echo '================================================================================'
echo ''
# TODO Maybe add some nice ASCII art

# Reboot to apply changes
sleep 5
sudo reboot