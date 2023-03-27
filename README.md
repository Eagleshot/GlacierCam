# GlacierCam

## Installation
### 1. Install Raspberry Pi OS
Required hardware: microSD card, computer with microSD card reader and internet connection

Download and install the Raspberry Pi Imager to flash the OS to the microSD card. The software can be downloaded [here](https://www.raspberrypi.com/software/).

Open the raspberry Pi Imager and click on the "Choose OS" button. Select "Raspberry Pi OS (other)" and click on "CHOOSE OS". Select "Raspberry Pi OS Lite (32-bit)" (the Pi Zero is a 32-bit computer). Then insert the microSD card and select it in the "SD Card" menu. Next click on the gear icon and select "Set Username and Password" and set a unique username and password. You can also add a WiFi connection if you don't have an ethernet adapter. In addition you can change the keyboard layout.

Then click on "SAVE" and "WRITE" to flash the OS to the microSD card. This process will take roughly 15 minutes. When the process is finished, remove the microSD card from the computer and insert it into the Raspberry Pi.

### Setup the software on the Raspberry Pi
Required hardware: Raspberry Pi Zero WH (or other), monitor, HDMI to microHDMI adapter (optional), keyboard, mouse, power supply, ethernet adapter or WiFi for Pi Zero W

Insert the microSD card and connect the Raspberry Pi to the monitor, keyboard, mouse and power supply. Boot up the Raspberry Pi and write the following command in the terminal:

```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script.sh | bash
```
