#!/bin/bash
echo 'Configuring software to run on startup...'

# Automatically run the main.py after startup
echo "sudo /usr/bin/python3 /home/pi/main.py" >> /home/pi/wittypi/beforeScript.sh

# Software update
TARGET_FILE="/home/pi/wittypi/afterStartup.sh"

cat << 'EOF' >> $TARGET_FILE
if grep -iq "shutdown: false" /home/pi/settings.yaml; then
    echo "Updating software and scheduling shutdown in 1 minute..."
    wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/updateScript.sh | sudo sh
    sudo shutdown -h +1
else  
    echo "Shutting down now..."
    sudo shutdown -h now
fi
EOF

# Configure the wake-up watchdog
echo 'Configuring the wake-up watchdog (guaranteed wake mode)...'
i2cset -y 0x01 0x08 49 0x81

# Check the config
echo 'Checking the wake-up watchdog configuration...'
i2cget -y 0x01 0x08 49

# Check if the config is 10000001 (binary)
if [ $(i2cget -y 0x01 0x08 49) -eq 0x81 ]; then
    echo 'The wake-up watchdog is configured correctly.'
else
    echo 'The wake-up watchdog is not configured correctly.'
fi