# GlacierCam
## Features at a glance
### Camera
* Standardized CSI camera connector
* 12 MP autofocus camera
* Big selection regarding resolution, lens and filters
* Specialty cameras (e.g. thermal, infrared, global shutter, etc.) available
* Possible: Ability to add up to 4 cameras on one system

### Connectivity
* 4G, WiFi, Bluetooth, Ethernet (with adapter)
* Offline time synchronization with GPS
* Offline backup, possibility to have multiple internet sources for backup
* Possible to add long range data transmission (e.g. LoRa, Satellite, directional antenna)

### Energy
* Low power consumption (ca. 0.05 Wh / wake cycle)
* Dedicated power management hardware
* Input: 5 V DC (USB-C) or 6 - 30 DC
* Programmable schedule (e.g. every 30 minutes from 8:00 to 20:00)
* Monitoring of battery level, internal temperature and voltage
* External 12V battery and solar panel possible
* Planned: Automatic schedule dependent on battery level and sunrise/sunset
* Planned: Energy consumption optimization trough soft- and hardware
* Possible to trigger externally (e.g. with radar)

### Additional sensors and data processing
* I2C, UART, SPI, USB, Bluetooth etc. available for additional sensors
* GPS and Temperature sensor built in
* Possible: Image processing on device
* Possible: Different Raspberry Pi for more processing power and more I/O or external accelerators

### Webserver (optional)
* Data visualization
* Local or in the cloud
* Planned: Image processing on server
* Planned: Change setting on the webserver
-> Modular for expansion and/or future upgrades

# Components
* [Raspberry Pi Zero 2 W](https://www.pi-shop.ch/raspberry-pi-zero-2-w) - CHF 19.90
* [Witty Pi 4](https://www.pi-shop.ch/witty-pi-4-realtime-clock-and-power-management-for-raspberry-pi) - CHF 32.90
* [Waveshare SIM7600G-H 4G HAT (B)](https://www.pi-shop.ch/sim7600g-h-4g-hat-b-for-raspberry-pi) - CHF 82.90
* [SandDisk max endurance 64GB](https://www.digitec.ch/en/s1/product/sandisk-max-endurance-microsd-64-gb-u3-uhs-i-memory-card-12705313?ip=sandisk+max+endurance) - CHF 20.10
* [Dörr 39mm UV Filter](https://www.digitec.ch/en/s1/product/doerr-lens-filter-digiline-hd-slim-39-mm-39-mm-uv-filter-filters-photography-13034018) - 8.70 CHF
* [Pi Zero Kamerakabel 150mm](https://www.pi-shop.ch/raspberry-pi-zero-kamera-kabel-300mm) - CHF 9.90

* [Kunststoffgehäuse](https://www.distrelec.ch/de/kunststoffgehaeuse-82x80x55mm-dunkelgrau-abs-ip67-rnd-components-rnd-455-01032/p/30128636) - CHF 20.61
* [Druckausgleichsmembran](https://www.distrelec.ch/de/druckausgleichsstopfen-m12-12-2mm-ip67-ip69k-polyamid-grau-gore-associates-gmbh-pmf100321-grey/p/15015938?queryFromSuggest=true&itemList=suggested_search) - CHF 11.20
* [Dörr 2W Solarpanel](https://www.digitec.ch/en/s1/product/doerr-li-1500-12v6v-204446-solar-panel-wildlife-cameras-35520370) - CHF 68.-

= Zwischentotal: CHF 274.21

* [Raspberry Pi Kamera V2](https://www.pi-shop.ch/raspberry-pi-kamera-module-v2) - CHF 22.90
oder
* [Raspberry Pi HQ Kamera](https://www.pi-shop.ch/hq-camera) - CHF 60.90
* [Raspberry Pi 6mm Lens](https://www.pi-shop.ch/official-raspberry-pi-6mm-wide-angle-lens) - CHF 29.90

= CHF 297.11 bzw. 365.01

+ Kleinteile (Kabel, Schrauben, Kondensator, Filament für 3D-Druck, etc.) - ca. CHF 50.-

## Installation
### Initial Setup
```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script.sh | sudo sh
```
### Update
```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/updateScript.sh | sudo sh
```

# Next TODOs
- [ ] Modularization -> graphics
- [ ] Advanced scheduling (start and end date)
- [ ] Finish 3D-printed case
- [ ] Publish Witty Pi software

# Fusion 360 TODOs
- [x] add cable releve for antenna cabels
- [x] See pictures on signal [16.0424]


-> get sample images for image processing

## Hardware
- [X] Upgrade to Witty Pi 4 (non mini)
- [X] Upgrade to Raspberry Pi Zero 2 W
- [X] Test camera focus with plexiglass
- [ ] Create 3D printed internal case
- [ ] Create additional cameras for testing

## Software
- [ ] Automatically set camera to reboot when power is on again
- [ ] Add log level settings
- [X] Improved settings validation
- [x] Code review by Philip
- [x] Improve the format of saved data -> e.g. use .yaml instead of a csv file so additional data can easily be added or different data versions can be used in future software
- [ ] Enable watchdog
- [ ] Add hooks for data processing (e.g. `image_processing()`) that are called by the program at a specific time in the program and can be modified by the user
- [X] Move SIM7600G-H 4G code to separate file/library for easier readability and add tests
- [X] Move WittyPi code to separate file/library for easier readability and add tests
- [ ] Move file handling code to separate file/library for easier readability and add tests
- [ ] Software update possibility
- [ ] Work with read only filesystem and USB drive
- [ ] Manage max. number of images on USB drive and add an upload limit
- [X] Update to Raspberry Pi OS bookworm (maybe) -> Not feasible
- [X] General code and boot speed improvements 
- [X] Change camera name to be configurable in settings
- [X] Fix bug with wrong timezone for start time
- [X] Set location manually for sunrise and sunset
- [ ] Get startup reason from witty pi
- [X] Move to dedicated logging facility
- [X] Log file handling with witty pi log files
- [ ] Limit log filesize
- https://www.youtube.com/watch?v=pxuXaaT1u3k
- https://stackoverflow.com/questions/24505145/how-to-limit-log-file-size-in-python

## Energy and Scheduling
- [X] Take sunrise and sunset into account for scheduling
- [X] Take battery level into account for scheduling
- [ ] Advanced scheduling (start and end date)
- [ ] Time drift detection (maybe with GPS)
- [X] New energy measurement -> optimize Solar panel and battery size

## Connectivity and Sensors
- [ ] Simpler WiFi setup
- [ ] Long range data transmission (LoRa/Satellite/directional antenna)
- [ ] Modify firmware to be able to easily add new sensors (including CSV/webserver adaption)

## Webserver
- [ ] Add settings page (after login)
- [ ] Add settings validation
- [ ] Error notifications
- [ ] Implement logging on webserver
- [X] Webserver without streamlit -> FTP app
- [ ] Implement image processing
- [ ] Add image comparison of different timestamps
- [ ] Generate timelapse from images
- [ ] Customization (e.g. logo, colors, etc.)
- [ ] Package webserver as a executable (electron?) - or PWA?
- [ ] Active camera monitoring -> E-Mail message (camera didnt start, battery low, other error message, etc.)

## General
- [ ] Extend documentation + improve installation script
    * Add instruction: camera needs to be set to UTC time -> Should be done by installation script
    * Add instruction: default camera state needs to be set to "on"
    * Add instruction: Only works with raspberry pi os bullseye
- [ ] Open source the project

# In the media
* [FHGR News](https://www.fhgr.ch/news/newsdetail/photonics-absolvent-gewinnt-ruag-innovation-award/)
* [Nau](https://www.nau.ch/ort/chur/fh-graubunden-photonics-absolvent-gewinnt-ruag-innovation-award-66625517)
* [LinkedIn](https://www.linkedin.com/posts/ruag-ag_news-fh-graub%C3%BCnden-activity-7117803653880569858-ut_M)
* [myScience](https://www.myscience.ch/de/news/wire/photonics_bachelorarbeit_wird_praemiert-2023-fhgr)
## TODO

