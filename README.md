# GlacierCam
## Installationsanleitung
# TODO: Materialliste
### 1. Vorgefertigte Software installieren
In order to save time you can also use a preconfigured image and flash it to the sd card using win32 disk imager.
https://sourceforge.net/projects/win32diskimager/

Falls Sie diesen Schritt ausgeführt haben, können Sie direkt mit Schritt 4 weiterfahren.

### 2. Raspberry Pi OS installieren
Benötigte Hardware: microSD-Karte, Computer mit microSD-Kartenleser und Internetverbindung

Laden Sie den Raspberry Pi Imager herunter und installieren Sie ihn, um das Betriebssystem auf die microSD-Karte zu flashen. Die Software kann [hier](https://www.raspberrypi.com/software/) für alle gängigen Betriebssysteme heruntergeladen werden.

Öffnen Sie den Raspberry Pi Imager und klicken Sie auf den Knopf "OS WÄHLEN". Klicken Sie auf "Raspberry Pi OS (other)" und wählen "Raspberry Pi OS Lite (32-bit)" aus. Die Raspberry Pi OS Lite Version ist eine schlankere Version des Betriebssystems, die keine grafische Benutzeroberfläche enthält. Dies ist für diese Anwendungen ausreichend und spart Speicherplatz und Ressourcen. Der Pi Zero W, welcher verwendet wird, bietet zudem keinen 64-bit Support, weshalb die 32-bit Version verwendet wird.

Schliessen Sie anschliessend die microSD-Karte an und wählen Sie sie im Menü "SD-KARTE WÄHLEN" aus. Klicken Sie dann auf das Zahnradsymbol unten rechts und wählen Sie "Benutzername und Passwort setzen:" aus. Legen Sie einen eindeutigen Benutzernamen und ein Passwort fest. Zusätzlich können Sie noch die Spracheinstellungen festlegen und die Zeitzone auf "Europe/Zurich" sowie das Tastaturlayout auf "CH" setzen. Sie können hier auch eine WiFi-Verbindung für den nächsten Installationsschritt hinzufügen, wenn Sie keinen Ethernet-Adapter haben. Alle restlichen Einstellungen wie die Aktivierung von SSH können Sie deaktivieren.

Klicken Sie dann auf "SPEICHERN" und "SCHREIBEN", um das Betriebssystem auf die microSD-Karte zu übertragen. Achtung: Dadurch werden alle Daten auf der microSD-Karte gelöscht. Dieser Vorgang dauert etwa 15 Minuten, abhängig von der Geschwindigkeit der microSD-Karte, des Computers und der Internetverbindung. Wenn der Vorgang abgeschlossen ist, nehmen Sie die microSD-Karte aus dem Computer. 

## 3. Installation der Software auf dem Raspberry Pi
Benötigte Hardware: Raspberry Pi Zero WH (oder andere), Monitor, HDMI Kabel mit microHDMI-Adapter, Tastatur (mit micro usb-zu-usb-Adapter), Netzteil, Ethernet-Adapter (oder WiFi Verbindung für Pi Zero W)

Legen Sie die microSD Karte ein und verbinden Sie den Raspberry Pi mit dem Monitor und der Tastatur. Schliessen Sie das Netzteil an, dann sollte er automatisch starten. Es wird ein Signal auf dem Bildschirm ausgegeben und die grüne Aktivitäts-LED auf dem Raspberry leuchtet auf. Während dem Installationsprozess wird der Raspberry Pi mehrmals neu starten. Melden Sie sich mit dem Benutzernamen und Passwort an, welches Sie im vorherigen Schritt festgelegt haben. Der Standardbenutzername ist "pi" und das Standardpasswort ist "raspberry". Bei der Eingabe des Passworts wird dieses nichts angezeigt, dies ist normal und ist ein Sicherheitsfeature.

Wenn Sie dies Ausgeführt haben, schreiben Sie folgenden Befehl in die Konsole und drücken Sie Enter:
```bash
wget -O - https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/script.sh | sudo sh
```
Nach dem Abschluss des Installationsskripts startet der Raspberry Pi automatisch neu, um die Änderungen zu übernehmen. Danach müssen Sie sich noch einmal einloggen, um die Software für den WittyPi4 herunterzuladen. Dazu schreiben Sie folgenden Befehl in die Konsole und drücken Sie Enter:

```bash
wget https://www.uugear.com/repo/WittyPi4/install.sh
```
Danach können sie das Installationsprogramm mit folgendem Befehl ausführen:
```bash¨
sudo sh install.sh
```

```bash
sudo reboot
```

Add main.py to automatically run before wittyPi script
```bash
echo "sudo /usr/bin/python3 /home/pi/main.py" >> /home/pi/wittypi/beforeScript.sh
```

Herunterfahren des Raspberry Pi:
```bash
sudo shutdown -h 0
```
warten bis heruntergefahren und led nicht mehr leuchtet, dann strom und kabel abziehen.




### 4. Kamera installieren
# TODO

### 5. Waveshare SIM7600G-H 4G HAT (B) installieren
# TODO
aufpassen usb pins -> löten?

### 6. RNDIS installieren
https://www.waveshare.com/wiki/Raspberry_Pi_networked_via_RNDIS

### 7. Edit config.yaml file
```bash
sudo nano config.yaml
```
You can validate yaml files herre: https://www.yamllint.com/

-> Edit username and password

# TODO PAsswort ändern

### Install the wittypi hardware
# TODO
-> only connect the power to the witty pi, not the raspberry pi!

### Set up the witty pi


### Activate read-only mode
https://www.youtube.com/watch?v=Nuww3UicTsI

### Finished?!?

## Update the software
# TODO disable read only
To update the main.py file only, run the following command in the terminal:

```bash
sudo wget -O /home/pi/main.py https://raw.githubusercontent.com/Eagleshot/GlacierCam/main/main.py
```

## Modifying Raspberry Pi OS
### Modify config.txt
Speed up boot time by disabling unneeded services
See: https://himeshp.blogspot.com/2018/08/fast-boot-with-raspberry-pi.html


Edit the config.txt file:
```bash
sudo nano /boot/config.txt
```
Add/modify the following lines:
```bash
boot_delay=0 # Set the boot delay to 0 seconds
disable_splash=1 # Disable the splash screen
dtparam=act_led_trigger=none # Disable the LED
dtoverlay=disable-wifi # Disable wifi # TODO

```

### Modify cmdline.txt
Edit the cmdline.txt file:
```bash
sudo nano /boot/cmdline.txt
```
Add/modify the following lines:
```bash
quiet
```
This will disable the boot messages.

# Check services and their impact on boot time
```bash
systemd-analyze blame
systemd-analyze critical-chain
```
Returns a list of services and their boot time impact.

# Disable services
# TODO Remove
Disable dhcpcd.service. Caution, this will break the internet connection if upload is done over bluetooth or ethernet.
```bash

Turn off white LED of witty pi

# TODOs
- [ ] USB Backup
- [ ] Web interface of ftp server (streamlit)

## Sicherheit
Sicherheit ist heute ein 
*Best practices
up to date system (keine updates im feld - schwierig)
nutzername/passwort
firewall blockiert anfragen von aussen, kein ssh zugriff von aussen
input validierung von einstellungen See https://pyyaml.org/wiki/PyYAMLDocumentation -> safe load / security

verschlüsselte übertragung möglich
read only modus (kann umgangen werden)


physikalische sicherheit -> keine verschlüsselung festplatte mögl.
sd karte/gerät/logindaten können geklaut werden, nur beschränkt sicher mit physikalischem zugriff

programm wird als root ausgeführt

todo erklärung/qr code auf gehäuse

Datenübertragung:
Datenübertragung über verschiedene Kanäle möglich:
Rasperry Pi W hat einen eingebauten WiFi- und Bluetooth Chip. Zudem kann der Rasperry über einen USB Adapter via Ethernet Kabel angeschlossen werden. Für unsere anwendungszwecke wird ein 4g modul mit eingebautem gps verwendet. Durch den aufbau des python skripts spielt es keine Rolle, welche "Internetquelle" verwendet wird. Es ist auch möglich, mehrere anschlüsse gleichzeitig zu verwenden (test erwähnen). Im Falle eines Ausfalls einer Verbindung wird so automatisch die verbindung gewechselt um so eine höhere verfügbarkeit zu erreichen. Ist das internet gar nicht erreichbar werden bilder zwischengespeichert und wenn internet nächstes mal wieder online alle zusammen hochgeladen.

DNS Server. - verwendet mehrere Anbieter für höchste Verfügbarkeit.

Test mit versch. sim, simabedckung link swisscom
geschätztes datenvolumen
speed test/ping
mögl. direkt über at commands files auf ftp/ftps server hochzuladen, allerdings weniger flexibel für zukunft
möglichkeit jegliche standart zur datenübertragung zu benutzen (sftp, webdav etc.)
auch getestet mit wlan (wieder aktivieren), über ethernet adapter, gibt auch viele thirdparty mögl auch für zukunft.

# Kamera

# Datenlogging
versch. sensoren möglich, auch über i2c bus, auch theoretisch analoge sensoren möglich. So wäre möglich .

# Additional log information can be found in the wittypi log files




