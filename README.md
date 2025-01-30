# GlacierCam 📷⛰️
GlacierCam is an open and affordable timelapse camera and sensor platform that is designed for harsh environments.
It offers modular hard- and software and can easily be adapted to different use cases or upgraded in the future.

> [!IMPORTANT]
> This repository is currently under active development and the documentation is currently not up to date.

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
Thanks to its modular design, GlacierCam can be used in a wide range of applications, depending on your use case. Reliable and proven platform

Here are some examples:

### Scientific Research
GlacierCam supports remote field research by providing real-time data collection crucial for scientific analysis. Its modular, customizable design allows researchers to add and configure sensors, including cameras, radar, and motion detectors, tailored to specific data needs. GlacierCam’s open architecture makes it future-proof, enabling easy expansion with new sensors. Additionally, its affordability allows for extensive sensor networks without high costs, making it ideal for researchers working in challenging environments to advance their studies.

### Environmental Hazard Monitoring
Climate change is increasing the frequency of hazards like landslides, rockfalls, and floods. GlacierCam enables low-cost, real-time monitoring of communities and remote infrastructure in high-risk areas. Its modular system integrates a range of sensors—such as cameras, radar, and motion detectors—to deliver comprehensive hazard monitoring. Built with high reliability for rugged environments, GlacierCam minimizes false alarms, reducing the need for human intervention and lowering both costs and risk. By providing timely early warnings, GlacierCam helps protect vulnerable communities and infrastructure with rapid response capabilities.

### Tourism and Outdoor Recreation
GlacierCam enhances visitor experience by offering live images, real-time weather, and environmental conditions that support safer and better-informed outdoor activities. The system is customizable, allowing businesses to add their own branding for a unique visitor experience. Real-time weather and safety updates enable visitors to plan their activities based on current conditions. This technology serves as an effective marketing tool, attracting and engaging tourists and outdoor enthusiasts by providing valuable, timely information for enjoyable and safe outdoor adventures.

### Agriculture and Forestry
GlacierCam supports precision agriculture and forestry by providing real-time data on environmental conditions, crop growth, and forest health. Its modular design allows for the integration of various sensors, such as cameras, temperature, and humidity sensors, to monitor crop growth and detect pests and diseases. GlacierCam’s real-time data collection enables farmers and foresters to make informed decisions on irrigation, fertilization, and pest control, optimizing crop yield and forest health. By providing timely data, GlacierCam supports sustainable agriculture and forestry practices, reducing costs and environmental impact.

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
> [!WARNING]
> The license for the project has not yet been decided on and needs to be checked before using the project.

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
