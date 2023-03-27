#!/bin/sh

echo "Beginning install script:"

# Install packages
PACKAGES="python3-picamera2"
apt-get update
agt-get upgrade -y
apt-get install -y $PACKAGES 

# TODO Enable camera and other hardware interfaces
# TODO Enable read-only filesystem


