'''Class for the SIM7600X 4G module'''
from time import sleep
import serial

class SIM7600X:
    '''Class for the SIM7600X 4G module'''
    def __init__(self, port: str = '/dev/ttyUSB2', baudrate: int = 115200, timeout: int = 5):
        self.ser = serial.Serial(port, baudrate, timeout=timeout) # USB connection
        self.ser.flushInput()

    # Send AT command to SIM7600X
    def send_at_command(self, command: str, back: str = 'OK', timeout: int = 1) -> str:
        '''Send an AT command to SIM7600X'''
        rec_buff = ''
        self.ser.write((command+'\r\n').encode())
        sleep(timeout)
        if self.ser.inWaiting():
            sleep(0.01)
            rec_buff = self.ser.read(self.ser.inWaiting())
        if back not in rec_buff.decode():
            print(f"Error: AT command {command} returned {rec_buff.decode()}")
            return ""

        return rec_buff.decode()

    # Get current signal quality
    # https://www.manualslib.com/download/1593302/Simcom-Sim7000-Series.html
    # 0 -115 dBm or less
    # 1 -111 dBm
    # 2...30 -110... -54 dBm
    # 31 -52 dBm or greater
    # 99 not known or not detectable
    def get_signal_quality(self):
        '''Gets the current signal quality from the SIM7600G-H 4G module'''
        try:
            signal_quality = self.send_at_command('AT+CSQ')
            signal_quality = signal_quality[8:10]
            signal_quality = signal_quality.replace("\n", "")
            signal_quality = ''.join(ch for ch in signal_quality if ch.isdigit()) # Remove non-numeric characters
            print(f"Current signal quality: {signal_quality}")
            return signal_quality
        except Exception as e:
            print(f"Could not get current signal quality: {str(e)}")
            return ""

    # Get GPS Position
    def get_gps_position(self, max_attempts=7, delay=5):
        '''Gets the current GPS position from the SIM7600G-H 4G module'''

        current_attempt = 0

        while current_attempt < max_attempts:

            current_attempt += 1
            gps_data_raw = self.send_at_command('AT+CGPSINFO', back='+CGPSINFO:')

            if gps_data_raw == "":
                sleep(delay)
            elif ',,,,,,' in gps_data_raw:
                print('GPS not yet ready.')
                sleep(delay)
            else:
                # Additions to Demo Code Written by Tim! -> Core Electronics
                # https://core-electronics.com.au/guides/raspberry-pi/raspberry-pi-4g-gps-hat/
                gps_data_cleaned = str(gps_data_raw)[13:]

                lat = float(gps_data_cleaned[:2]) + (float(gps_data_cleaned[2:11])/60)
                lon = float(gps_data_cleaned[14:17]) + (float(gps_data_cleaned[17:26])/60)

                north_or_south = gps_data_cleaned[12]
                east_or_west = gps_data_cleaned[27]

                if north_or_south == 'S':
                    lat = -lat
                if east_or_west == 'W':
                    lon = -lon

                # TODO Sometimes heigth is not correctly extracted
                Height = gps_data_cleaned[45:49]

                str_lat = str(round(lat, 5))
                str_lon = str(round(lon, 5))
                str_height = str(Height)

                # TODO Time

                print(f"GPS position: LAT {str_lat}, LON {str_lon}, HEIGHT {str_height}")
                return str_lat, str_lon, str_height
        return "-", "-", "-"

    def start_gps_session(self):
        '''Starts a GPS session on the SIM7600G-H 4G module'''
        try:
            print('Starting GPS session.')
            self.send_at_command('AT+CGPS=1,1')
        except Exception as e:
            print(f"Could not start GPS session: {str(e)}")

    def stop_gps_session(self):
        '''Stops a GPS session on the SIM7600G-H 4G module'''
        try:
            print('Stopping GPS session.')
            self.send_at_command('AT+CGPS=0')
            print("GPS session stopped.")
        except Exception as e:
            print(f"Could not stop GPS session: {str(e)}")


if __name__ == "__main__":
    sim7600x = SIM7600X()
    sim7600x.get_signal_quality()
    sim7600x.start_gps_session()
    sleep(10)
    sim7600x.get_gps_position()
    sim7600x.stop_gps_session()