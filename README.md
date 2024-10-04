# GlacierCam
GlacierCam is an open source timelapse camera system, powered by Raspberry Pi.

> [!IMPORTANT]
> This repository is currently under active development and the documentation is currently not up to date.

## Features at a glance
### Camera
* Standardized CSI camera connector
* 12 MP autofocus camera
* Big selection regarding resolution, lens and filters
* Specialty cameras (e.g. thermal, infrared, global shutter, etc.) available
* Possible: Ability to add up to 4 cameras on one system

### Connectivity
* 4G, WiFi, Bluetooth and Ethernet (with adapter)
* Offline time synchronization with built-in GPS
* Offline operation/fallback possible
* Possibility to have multiple internet sources for redundancy
* Full data ownership with your own server (e.g. FTP)
* Can easily be modified/upgraded in the future (e.g. 5G, Satellite internet, directional antennas)

### Energy
* Low power consumption (ca. 0.05 Wh / wake cycle)
* Dedicated power management hardware
* Input: 5 V DC (USB-C) or 6 - 30 DC
* Programmable schedule (e.g. every 30 minutes from 8:00 to 20:00)
* Monitoring of battery level, internal temperature and voltage
* External 12V battery and solar panel possible (e.g. 2 W solar panel)
* Automatic schedule dependent on battery level and sunrise/sunset
* Possible to trigger recording externally (e.g. with radar)

# Enviroment
* Has extensively been tested in harsh enviroment conditions (snow, rain, cold temperatures etc.)
* Fits in small IP67 case
* 3D-printed case insert available

### Additional sensors and data processing
* Can accomodate a wide variety of additional sensors
* I2C, UART, SPI, USB, Bluetooth etc. available for additional sensors
* GPS and Temperature sensor built in
* Image processing on device possible, supports edge TPUs for ML inference
* Supports different Raspberry Pi models, depending on compute and I/O requirements
* Timestamp with internal RTC (±2s/year), time synchronization via GPS or internet

### Webserver (optional)
* Data visualization
* Local or in the cloud
* Planned: Image processing on server
* Planned: Change setting on the webserver
-> Modular for expansion and/or future upgrades

# Components
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
Install Pi OS Bullseye/Legacy Lite 64 bit on microSD card and boot the Raspberry Pi.
```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script.sh | sudo sh
```
### Install Witty Pi Software
Update Witty Pi 4 firmware -> See: https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-not-starting/ and install capacitor.
```bash
wget https://www.uugear.com/repo/WittyPi4/install.sh
```
```bash
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

# TODOs
## Custom electronics
### Power management board
* Input voltage: 5 - 20/30 V DC (solar or USB-C)
* Output voltage: 3.3 V (MCU), 5 V (Pi)
* Battery charger (LiFePO4, Li-Ion, ...?)
* Maybe: Battery holder (18650?)
* Voltage monitoring for input and battery, current monitoring probably not necessary
* Microcontroller: ESP32 (S3 for camera?)
* Mircocontroller programmable via USB-C(?)
* Exposed external Pins for interacting with MCU (e.g. trigger wake up, additional sensors, etc.)
* RTC -> Use external or internal one? -> Test accuracy
* Protection circuitry (reverse polarity, overvoltage, overcurrent, etc.)
* Button for manual wake up / activity LED
* Max. power draw for Pi + camera + 4G module: maybe 5 W / 1 A (potentially more for compute module), typical ~2 W / 0.4 A
* Max input power ?
* Connection to Pi (I2C over 40-pin header?)

* Software: watchdog, brownout detection, ...

Examples:
* https://lifepo4wered.com/lifepo4wered-pi+.html
* https://www.waveshare.com/power-management-hat.htm
* https://www.waveshare.com/power-management-hat-b.htm
* https://www.uugear.com/product/witty-pi-4/
* https://www.uugear.com/product/witty-pi-4-l3v7/

### Connectivyit / camera
* Add 4G-module, potentially with GPS
-> Preferably with m.2 connector for replacability/upgradeability (see e.g. https://www.lilygo.cc/products/t-simcam, https://www.lilygo.cc/products/a-t-pcie?variant=42335922094261)

* Add camera interface for esp32
* Maybe use compute module and add ethernet



## V2.0
- [ ] Add one time actions/change detection in settings
- [ ] Automatic time drift detection (maybe with GPS, dependent on startup reason)
- [ ] Advanced scheduling (start and end date)
- [ ] Enable watchdog
- [ ] Add hooks for data processing (e.g. `image_processing()`) that are called by the program at a specific time in the program and can be modified by the user
- [ ] Modify firmware to be able to easily add new sensors (including CSV/webserver adaption)
- [ ] Work with read only filesystem and USB drive
- [ ] Manage max. number of images on USB drive and add an upload limit (management if disk is full)
- [ ] Get startup reason from witty pi
- https://www.youtube.com/watch?v=pxuXaaT1u3k
- https://stackoverflow.com/questions/24505145/how-to-limit-log-file-size-in-python
- [ ] Limit log filesize
- [ ] Verify image/file upload

## Connectivity
- [ ] Simpler WiFi setup
- [ ] Check long range data transmission options (LoRa/Satellite/directional antenna)

## Webserver
- [ ] Add settings page (after login)
- [ ] Add settings validation
- [ ] Error notifications
- [ ] Implement logging on webserver
- [ ] Implement image processing
- [ ] Add image comparison of different timestamps
- [ ] Generate timelapse from images
- [ ] Customization (e.g. logo, colors, etc.)
- [ ] Package webserver as a executable (electron?) - or PWA?
- [ ] Active camera monitoring -> E-Mail message (camera didnt start, battery low, other error message, etc.)

## General
- [ ] Finish documentation + improve installation script
    * Add instruction: camera needs to be set to UTC time -> Should be done by installation script
    * Add instruction: Only works with raspberry pi os bullseye
- [ ] Update project website
- [ ] Media articles
- [ ] Open source the project

# In the media
* [FHGR News](https://www.fhgr.ch/news/newsdetail/photonics-absolvent-gewinnt-ruag-innovation-award/)
* [Nau](https://www.nau.ch/ort/chur/fh-graubunden-photonics-absolvent-gewinnt-ruag-innovation-award-66625517)
* [LinkedIn](https://www.linkedin.com/posts/ruag-ag_news-fh-graub%C3%BCnden-activity-7117803653880569858-ut_M)
* [myScience](https://www.myscience.ch/de/news/wire/photonics_bachelorarbeit_wird_praemiert-2023-fhgr)
