# GlacierCam 📷⛰️
GlacierCam is an open and affordable timelapse camera and sensor platform that is designed for harsh environments.
It offers modular hard- and software and can easily be adapted to different use cases or upgraded in the future.

For more information, please check out our website: [www.eagleshot.ch](https://www.eagleshot.ch)

> [!TIP]
> We are currently working on a new version of GlacierCam with custom hardware made for our requirements. Please get in touch if you are interested in a collaboration.

## Features at a glance
### Camera 📷
* High resolution camera with industry standard connector (MIPI CSI)
* Large camera selection available to suit your requirements (including specialty cameras like thermal, infrared, global shutter, etc.)
* Ability to add multiple cameras (up to 4) on one system

### Sensors 📡
* Can accomodate virtually any additional sensor (e.g. temperature, humidity, pressure, motion, radar, etc.)
* Several interfaces available (I2C, UART, SPI, USB, Bluetooth, etc.)
* Programmable schedule for measurements or via external trigger

### Compute / data processing 📊
* Hybrid system design with microcontroller and linux-based compute module allows for maximised efficiency while having large computational power on demand
* Scalable compute, memory and storage, depending on requirements (up to 16 GB RAM, 2+ TB storage)
* Supports hardware-accelerators for real time edge inference (e.g. image processing)

### Connectivity 🌐
* 4G, WiFi, Bluetooth and Ethernet connectivity
* Possibility to have multiple internet sources for redundancy
* Offline operation / fallback possible
* Offline timekeeping with built-in RTC (±2s/year) and GPS
* Easy upgradeability for future-proofing (e.g. 5G, satellite internet)

### Remote management (optional) ☁️
* Change settings remotely
* Secure over-the-air software updates
* Full data ownership with your own server
* Monitoring of system status (battery level, temperature, etc.)
* Data visualization and analysis on webserver (e.g. image processing)

### Energy 🌞
* Low power consumption with dedicated power management hardware optimized for solar / battery operation
* Programmable schedule for image capture and sensor measurements
* Intelligent schedule adaption based on battery level and sunrise/sunset
* Modular, scalable design, depending on requirements (e.g. to power exteral sensors)

### Enviroment 🌍
* Has extensively been tested in harsh enviroment conditions (snow, rain, cold temperatures etc.)
* Compact and rugged design (IP67)

## Applications 🔧
Thanks to its modular design, GlacierCam can be used as a reliable and proven platform in a wide range of applications, depending on your use case.
# Components 🛠️
| Component                                      | Price   |
| ---------------------------------------------- | ------- |
| [Raspberry Pi Zero 2 W](https://www.pi-shop.ch/raspberry-pi-zero-2-w) | CHF 19.90 |
| [Witty Pi 4](https://www.pi-shop.ch/witty-pi-4-realtime-clock-and-power-management-for-raspberry-pi) | CHF 32.90 |
| [Waveshare SIM7600G-H 4G HAT (B)](https://www.pi-shop.ch/sim7600g-h-4g-hat-b-for-raspberry-pi) | CHF 82.90 |
| [SandDisk max endurance 64GB](https://www.digitec.ch/en/s1/product/sandisk-max-endurance-microsd-64-gb-u3-uhs-i-memory-card-12705313?ip=sandisk+max+endurance) | CHF 20.10 |
| [Dörr 39mm UV Filter](https://www.digitec.ch/en/s1/product/doerr-lens-filter-digiline-hd-slim-39-mm-39-mm-uv-filter-filters-photography-13034018) | CHF 8.70 |
| [Pi Zero Kamerakabel 150mm](https://www.pi-shop.ch/raspberry-pi-zero-kamera-kabel-300mm) | CHF 9.90 |
| [Kunststoffgehäuse](https://www.distrelec.ch/de/kunststoffgehaeuse-82x80x55mm-dunkelgrau-abs-ip67-rnd-components-rnd-455-01032/p/30128636) | CHF 20.61 |
| [Druckausgleichsmembran](https://www.distrelec.ch/de/druckausgleichsstopfen-m12-12-2mm-ip67-ip69k-polyamid-grau-gore-associates-gmbh-pmf100321-grey/p/15015938?queryFromSuggest=true&itemList=suggested_search) | CHF 11.20 |
| [Dörr 2W Solarpanel](https://www.digitec.ch/en/s1/product/doerr-li-1500-12v6v-204446-solar-panel-wildlife-cameras-35520370) | CHF 68.00 |
| [Raspberry Pi Kamera V2](https://www.pi-shop.ch/raspberry-pi-kamera-module-v2) | CHF 22.90 |

## Installation
### Initial Setup
Install Pi OS Bullseye/Legacy Lite 64 bit on microSD card and boot the Raspberry Pi. Run the following command to install necessary software and configure the system:
```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script.sh | sudo sh
```
### Install Witty Pi Software
Update Witty Pi 4 firmware -> See: https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-not-starting/ and install capacitor.
```bash
wget https://www.uugear.com/repo/WittyPi4/install.sh

sudo sh install.sh
```
Uninstall UWI (UUGear Web Interface):
```bash
sudo update-rc.d uwi remove
sudo rm /etc/init.d/uwi
sudo rm -r ~/uwi
```
(Waiting for https://github.com/uugear/Witty-Pi-4/pulls to be merged.)

### Configure Software to run at startup
```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script2.sh | sudo sh
```

### Update
Set guaranteed wake mode and check RTC calibration:
```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script3.sh | sudo sh
```
## Testing
This repository uses pytest for testing. To run the tests, use the following command:
```bash
pytest
```
