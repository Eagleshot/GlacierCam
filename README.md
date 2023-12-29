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
* https://www.distrelec.ch/de/kunststoffgehaeuse-82x80x55mm-dunkelgrau-abs-ip67-rnd-components-rnd-455-01032/p/30128636


# Code review 
## Python hooks
Problem: Some functionality on the camera and webapp should be able to be modified/added in the future (e.g. image processing on the camera/webserver or readout of additional sensors). Its not ideal to hardcode this functionality.

-> Idea: The program calls a hook function (e.g. `image_processing()`) and the user can add his own code to this function. This function is called at a specific point in the program (e.g. after the image is taken). The user can add his own code to this function and the program will execute it. All sensor data can be stored in the CSV as an additional row.


## Settings download
Settings are downloaded every run from the FTP server and overwrite the local settings. There is some basic settings validation (e.g. to ensure that the camera always restarts even with invalid timer settings). If the server is offline, the local settings are used. If the settings get deleted on the server, the local settings are uploaded.

-> Is this an "ok enough" way of doing it? An option would be to add a settings validator/comparison but that would bring additional overhead.

Idea: Settings will mainly be changed in the webapp in the future. The webapp also could validate the settings and alert the user (if changed manually). Otherwise the settings validation on the camera prevents major errors so they only cause minor inconveniences.

General question: Don't fix it if it works? Testing is relatively time consuming together with hardware (problems). Sometimes it was not clear where the errors came from so it resulted in reversed code changes.


* Gültigkeit der einstellungen, wo kommt dies her -> ddos
-> konfiguration signieren (sehr aufwändig)

rollback -> 
neue config herunterladen -> überprüfen -> nur überschreiben wenn alles gültig

# -> numerische daten als yaml anstatt csv -> does battery voltage exist -> ev. versionierung


## One time actions
-> crontab
-> ntp for rtc
-> Set setting to certain value and then revert it!!!!!!!

Problem: When activated, certain settings run every time the camera runs. This is not needed for everything (e.g. time sync, GPS location). In addition, some new settings should be added (e.g. changing low voltage treshold, clear log files, chang wifi access credentials) that would only need to be done once and very rarely.

There are many possible options:
* Create a "TODO" list for the camera with jobs to be done
* Modify the settings file (e.g. set low voltage treshold 0 V after changing it)
* Only trigger this in a certain timeslot (e.g. at the first run of the day)
* Only trigger during certain conditions (e.g. when power was lost/restored)
* Leave it as is, as the overhead is possibly not worth it. Certain settings could be improve (e.g. check if time is correct first and only then sync it)

-> How to minimize overhead
-> How to properly implement
-> How to to it "time aware" with a possibly changing schedule

## Updates and version control
How to handle different versions of the software software (especially during active development/in the future)? Camera in the field, camera running development software etc.? Mostly compatible but sometimes breaking changes in data format etc. together with the webapp.

* Flag with version of data format
* Different webserver versions (e.g. for different cameras) or for different image locations

* Gehäuse -> 3D Modell
* Kamerafilter -> Test/Gewinde
* Antennen
* Generelle Fehlerbehebungen -> Stürzt nicht ab wenn z.B. Temperatursensor defekt
* Webserver -> Einstellungsmenü


'''bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script.sh | sudo sh 
'''

 Gewinde (Filter + Schrauben)
* Toleranzen
* Standoff zu Deckel oder in Deckel hinein
* Löcher für Antenne(n)
* GPS-Halter?
* Gehäuse oben kl. als unten
* USB?

-> Nur halter fräsen?

* Deckel dicker -> löcher unten
* Kamera zentrieren
* Filter
* Abstand deckel/gehäuserand
* Abstandshalter Witty Pi hinten


# TODOs
## Hardware
- [X] Upgrade to Witty Pi 4 (non mini)
- [X] Upgrade to Raspberry Pi Zero 2 W
- [X] Test camera focus with plexiglass
- [ ] Create 3D printed internal case
- [ ] Create additional cameras for testing

## Software
- [x] Code review by Philip
- [ ] Improved settings validation
- [ ] Enable watchdog
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
- [X] Move to dedicated logging facility - https://docs.python.org/3/library/logging.html
- [X] Log file handling with witty pi log files
# https://www.youtube.com/watch?v=pxuXaaT1u3k
# https://stackoverflow.com/questions/24505145/how-to-limit-log-file-size-in-python

## Energy and Scheduling
- [X] Take sunrise and sunset into account for scheduling
- [X] Take battery level into account for scheduling
- [ ] Advanced scheduling (start and end date)xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
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
    * Add instruction: camera needs to be set to UTC time
    * Add instruction: default camera state needs to be set to "on"
    * Add instruction: Only works with raspberry pi os bullseye
- [ ] Open source the project

# In the media
* [FHGR News](https://www.fhgr.ch/news/newsdetail/photonics-bachelorarbeit-wird-praemiert/)
* [Nau](https://www.nau.ch/ort/chur/fh-graubunden-photonics-absolvent-gewinnt-ruag-innovation-award-66625517)
* [LinkedIn](https://www.linkedin.com/posts/ruag-ag_news-fh-graub%C3%BCnden-activity-7117803653880569858-ut_M)
* [myScience](https://www.myscience.ch/de/news/wire/photonics_bachelorarbeit_wird_praemiert-2023-fhgr)
## TODO

