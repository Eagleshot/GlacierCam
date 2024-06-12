'''Class for the SIM7600X 4G module'''
from time import sleep
from datetime import datetime
import logging
import serial

class SIM7600X:
    '''Class for the SIM7600X 4G module.'''
    def __init__(self, port: str = '/dev/ttyUSB2', baudrate: int = 115200, timeout: int = 5):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout) # USB connection
            self.ser.flushInput()
        except Exception as e:
            logging.error("Could not initialize SIM7600X: %s", str(e))

    def send_at_command(self, command: str, back: str = 'OK', timeout: int = 1) -> str:
        '''Send an AT command to SIM7600X.'''
        rec_buff = ''
        self.ser.write((command+'\r\n').encode())
        sleep(timeout)
        if self.ser.inWaiting():
            sleep(0.01)
            rec_buff = self.ser.read(self.ser.inWaiting())
        if back not in rec_buff.decode():
            logging.error("Error: AT command %s returned %s", command, rec_buff.decode())
            return ""

        return rec_buff.decode()

    # Get current signal quality
    # https://www.manualslib.com/download/1593302/Simcom-Sim7000-Series.html
    # 0 -115 dBm or less
    # 1 -111 dBm
    # 2...30 -110... -54 dBm
    # 31 -52 dBm or greater
    # 99 not known or not detectable
    def get_signal_quality(self) -> float:
        '''Get the current signal quality of the 4G modem.'''
        try:
            signal_quality = self.send_at_command('AT+CSQ')
            signal_quality = signal_quality[8:10]
            signal_quality = signal_quality.replace("\n", "")
            signal_quality = ''.join(ch for ch in signal_quality if ch.isdigit()) # Remove non-numeric characters
            logging.info("Current signal quality: %s", signal_quality)
            return float(signal_quality)
        except Exception as e:
            logging.error("Could not get current signal quality: %s", str(e))
            return 99

    @staticmethod
    def __decode_position(position: str, round_to: int = 5) -> float:
        '''Decode the NMEA GPS position to a latitude or longitude value .'''
        position = position.split('.')
        degrees = position[0][:-2]
        minutes = position[0][-2:] + '.' + position[1]
        return round(float(degrees) + float(minutes)/60, round_to)

    def get_gps_position(self, max_attempts=7, delay=5):
        '''Get the current GPS position and time.'''
        current_attempt = 0

        while current_attempt < max_attempts:

            current_attempt += 1
            gps_data_raw = self.send_at_command('AT+CGPSINFO', back='+CGPSINFO:')

            if gps_data_raw == "":
                sleep(delay)
            elif ',,,,,,' in gps_data_raw:
                logging.info("GPS not yet ready.")
                sleep(delay)
            else:
                # Additions to Demo Code Written by Tim! -> Core Electronics
                # https://core-electronics.com.au/guides/raspberry-pi/raspberry-pi-4g-gps-hat/
                gps_data_cleaned = str(gps_data_raw)[13:]
                gps_data_cleaned = gps_data_cleaned.split(',')

                lat = self.__decode_position(gps_data_cleaned[0])
                lon = self.__decode_position(gps_data_cleaned[2])

                # North or South, East or West
                if gps_data_cleaned[1] == 'S':
                    lat = -lat
                if gps_data_cleaned[3] == 'W':
                    lon = -lon

                height = float(gps_data_cleaned[6])

                date_str = gps_data_cleaned[4] + gps_data_cleaned[5]
                date = datetime.strptime(date_str, '%d%m%y%H%M%S.%f')

                logging.info("GPS date: %s", date)
                logging.info("GPS position: LAT %s, LON %s, HEIGHT %s", lat, lon, height)
                return lat, lon, height, date

        return None

    def start_gps_session(self):
        '''Start the GPS session.'''
        try:
            logging.info("Starting GPS session.")
            self.send_at_command('AT+CGPS=1,1')
        except Exception as e:
            logging.error("Could not start GPS session: %s", str(e))

    def stop_gps_session(self):
        '''Stops the GPS session.'''
        try:
            logging.info("Stopping GPS session.")
            self.send_at_command('AT+CGPS=0')
        except Exception as e:
            logging.error("Could not stop GPS session: %s", str(e))

    def close(self):
        '''Close the serial connection.'''
        try:
            self.ser.close()
        except Exception as e:
            logging.error("Could not close serial connection: %s", str(e))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sim7600x = SIM7600X()
    sim7600x.get_signal_quality()
    sim7600x.start_gps_session()
    sleep(10)
    sim7600x.get_gps_position()
    sim7600x.stop_gps_session()
