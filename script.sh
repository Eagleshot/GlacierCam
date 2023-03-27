#!/bin/sh

echo "Beginning install script:"

# Install packages
PACKAGES="python3-picamera2"
sudo apt-get update
sudo agt-get upgrade -y
sudo apt-get install -y $PACKAGES 

# TODO Enable camera and other hardware interfaces
# TODO Enable read-only filesystem


