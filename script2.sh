#!/bin/bash
echo 'Configuring software to run on startup...'

# Automatically run the main.py after startup
echo "sudo /usr/bin/python3 /home/pi/main.py" >> /home/pi/wittypi/beforeScript.sh

# Software update
TARGET_FILE="/home/pi/wittypi/afterStartup.sh"

cat << 'EOF' >> $TARGET_FILE
if grep -iq "shutdown: false" /home/pi/wittypi/settings.yaml; then
    echo "Updating software and scheduling shutdown in 1 minute..."
    wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/updateScript.sh | sudo sh
    sudo shutdown -h +1
else  
    echo "Shutting down now..."
    sudo shutdown -h now
fi
EOF
