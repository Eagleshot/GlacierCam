echo 'Configuring software to run on startup...'

# Automatically run the main.py after startup
echo "sudo /usr/bin/python3 /home/pi/main.py" >> /home/pi/wittypi/afterStartup.sh

# Software update possibility
echo "sleep 5" >> /home/pi/wittypi/afterStartup.sh
echo "sudo wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/updateScript.sh | sudo sh" >> /home/pi/wittypi/afterStartup.sh

# Schedule shutdown after update
echo "sudo shutdown -h +1" >> /home/pi/wittypi/afterStartup.sh
