'''A python module for interacting with the Witty Pi 4 board.'''
from subprocess import check_output, STDOUT
from datetime import time, datetime
from time import sleep
from os import path
import logging
import suntime

class WittyPi4:
    '''A class for interacting with the Witty Pi 4 board.'''

    # Setup
    WITTYPI_DIRECTORY = "/home/pi/wittypi"
    SCHEDULE_FILE_PATH = f"{WITTYPI_DIRECTORY}/schedule.wpi"

    def __init__(self):
        # Default schedule settings
        self.start_time = time(8, 0)
        self.end_time = time(20, 0)
        self.interval_length_minutes = 30
        self.interval_length_hours = 0
        self.round_start_end_time = False

        self.START_DATE = datetime(2020, 1, 1)
        self.END_DATE = datetime(2037, 12, 31, 23, 59, 59)
        self.MAX_DURATION_MINUTES = 4 # Maximum time Raspberry Pi is allowed to run

    MAX_RETRIES = 5

    # Get WittyPi readings
    # See: https://www.baeldung.com/linux/run-function-in-script
    def run_command(self, command: str) -> str:
        '''Run a Witty Pi 4 command'''
        try:
            command = f"cd {self.WITTYPI_DIRECTORY} && . ./utilities.sh && {command}"
            output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=3)
            return output.strip()
        except Exception as e:
            logging.error("Could not run Witty Pi 4 command: %s", str(e))
        return "ERROR"

    def sync_time_with_network(self) -> None:
        '''Sync the RTC with network time.'''
        # See: https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-how-to-synchronise-time-with-internet-on-boot/
        try:
            output = self.run_command("net_to_system && system_to_rtc")
            logging.info("Time synchronized with network: %s", output)
        except Exception as e:
            logging.error("Could not synchronize time with network: %s", str(e))

    def get_temperature(self) -> float:
        '''Gets the current temperature reading in °C.'''
        try:
            temperature = self.run_command("get_temperature")
            temperature = temperature.split("/", maxsplit = 1)[0] # Remove the Farenheit reading
            temperature = temperature[:-3] # Remove °C
            temperature = float(temperature)
            logging.info("Temperature: %s °C", temperature)
            return temperature
        except Exception as e:
            logging.error("Could not get temperature: %s", str(e))
            return -273.15

    def get_battery_voltage(self) -> float:
        '''Gets the battery voltage reading in V.'''
        try:
            battery_voltage = self.run_command("get_input_voltage")
            battery_voltage = float(battery_voltage) # Remove V
            logging.info("Battery voltage: %s V", battery_voltage)
            return battery_voltage
        except Exception as e:
            logging.error("Could not get battery voltage: %s", str(e))
            return 0.0

    def get_internal_voltage(self) -> float:
        '''Gets the internal (5V) voltage in V.'''
        try:
            internal_voltage = self.run_command("get_output_voltage")
            internal_voltage = float(internal_voltage)
            logging.info("Output voltage: %s V", internal_voltage)
            return internal_voltage
        except Exception as e:
            logging.error("Could not get Raspberry Pi voltage: %s", str(e))
            return 0.0

    def get_internal_current(self) -> float:
        '''Gets the internal (5V) current reading in A.'''
        try:
            internal_current = self.run_command("get_output_current")
            internal_current = float(internal_current)
            logging.info("Output current: %s A", internal_current)
            return internal_current
        except Exception as e:
            logging.error("Could not get Raspberry Pi current: %s", str(e))
            return 0.0

    def get_voltage_threshold(self, command: str) -> float:
        '''General method to get a voltage threshold'''
        try:
            threshold = self.run_command(command)

            if threshold == "disabled":
                logging.info("%s: disabled", command)
                return 0.0

            threshold = float(threshold[:-1])
            logging.info("%s: %s V", command, threshold)
            return threshold

        except Exception as e:
            logging.error("Could not get %s: %s", command, str(e))
            return 0.0 

    def get_low_voltage_threshold(self) -> float:
        '''Gets the low threshold in V.'''
        return self.get_voltage_threshold("get_low_voltage_threshold")

    def get_recovery_voltage_threshold(self) -> float:
        '''Gets the recovery threshold in V.'''
        return self.get_voltage_threshold("get_recovery_voltage_threshold")

    def set_low_voltage_threshold(self, voltage: float) -> float:
        '''Set the low voltage threshold in V.'''
        # TODO: Compare with recovery voltage threshold
        try:
            if 2.0 <= voltage <= 25.0 or voltage == 0:
                if voltage != self.get_low_voltage_threshold():
                    low_voltage_threshold = self.run_command(f"set_low_voltage_threshold {int(voltage*10)}")
                    logging.info("Set low voltage threshold to: %s V", low_voltage_threshold)
                else:
                    logging.info("Low voltage threshold already set to: %s V", voltage)
            else:
                logging.error("Voltage must be between 2.0 and 25.0 V (or 0 to disable).")

        except Exception as e:
            logging.error("Could not set low voltage threshold: %s", str(e))

    def set_recovery_voltage_threshold(self, voltage: float) -> None:
        '''Set the recovery voltage threshold in V.'''
        # TODO Compare to low voltage threshold
        try:
            if 2.0 <= voltage <= 25.0 or voltage == 0:
                if voltage != self.get_recovery_voltage_threshold():
                    recovery_voltage_threshold = self.run_command(f"set_recovery_voltage_threshold {int(voltage*10)}")
                    logging.info("Set recovery voltage threshold to: %s V", recovery_voltage_threshold)
                else:
                    logging.info("Recovery voltage threshold already set to: %s V", voltage)
            else:
                logging.error("Voltage must be between 2.0 and 25.0 V (or 0 to disable).")

        except Exception as e:
            logging.error("Could not set recovery voltage threshold: %s", str(e))

    def set_start_time(self, start_time: time) -> None:
        '''Set the start time for the schedule.'''
        if start_time < time(23 - self.interval_length_hours, 59 - self.interval_length_minutes):
            self.start_time = start_time
        else:
            logging.error("Invalid start time: %s", start_time)

    def set_end_time(self, end_time: time) -> None:
        '''Set the end time for the schedule.'''
        self.end_time = end_time

    def set_start_end_time_sunrise(self, latitude: float, longitude: float) -> None:
        '''Start the schedule at sunrise and end it at sunset. The time gets rounded to nearest interval.'''
        sun = suntime.Sun(latitude, longitude)

        # Sunrise
        sunrise = sun.get_sunrise_time().time()
        logging.info("Next sunrise: %s:%s", sunrise.hour, sunrise.minute)
        self.set_start_time(sunrise)

        # Sunset
        sunset = sun.get_sunset_time().time()
        logging.info("Next sunset: %s:%s", sunset.hour, sunset.minute)
        self.set_end_time(sunset)

        self.round_start_end_time = True # Round to nearest interval

    def set_interval_length(self, minutes: int, hours: int = 0) -> None:
        '''Set the interval length for the schedule with basic validity checks.'''
        if 0 <= hours < 24:
            self.interval_length_hours = hours
        else:
            logging.error("Invalid interval length (hours): %s", hours)

        if self.MAX_DURATION_MINUTES < minutes <= 59:
            self.interval_length_minutes = minutes
        elif self.interval_length_hours > 0 and 0 <= minutes <= 59:
            self.interval_length_minutes = minutes
        else:
            logging.error("Invalid interval length (minutes): %s", minutes)

    def round_time_to_nearest_interval(self, time: time) -> time:
        '''Round datetime up to the nearest interval (e.g. 15 minutes)'''
        return time.replace(minute=(time.minute // self.interval_length_minutes) * self.interval_length_minutes)

    def calculate_num_repetitions_per_day(self) -> int:
        '''Calculate the number of repetitions between (and including) the start and end time'''
        start_time_date = datetime(2020, 1, 1, self.start_time.hour, self.start_time.minute)
        end_time_date = datetime(2020, 1, 1, self.end_time.hour, self.end_time.minute)

        # Swap start and end time if start time is later than end time
        if self.start_time > self.end_time:
            start_time_date, end_time_date = end_time_date, start_time_date

        return (((end_time_date - start_time_date).seconds // 60) // (self.interval_length_minutes + self.interval_length_hours * 60)) + 1

    def generate_schedule(self) -> None:
        '''Generate a daily recurring schedule and overwrite schedule.wpi'''

        # Round start and end time
        if self.round_start_end_time:
            self.start_time = self.round_time_to_nearest_interval(self.start_time)
            self.end_time = self.round_time_to_nearest_interval(self.end_time)

        # Check if end is before start time
        if self.start_time > self.end_time:
            self.start_time, self.end_time = self.end_time, self.start_time

        # 2037 is the maximum year for WittyPi
        formatted_start_date = self.START_DATE.strftime("%Y-%m-%d")
        formatted_start_time = f"{self.start_time.hour:02d}:{self.start_time.minute:02d}:00"
        formatted_end_date = self.END_DATE.strftime("%Y-%m-%d")
        formatted_end_time = f"{self.END_DATE.hour:02d}:{self.END_DATE.minute:02d}:{self.END_DATE.second:02d}"

        schedule = f"BEGIN\t{formatted_start_date} {formatted_start_time}\nEND\t{formatted_end_date} {formatted_end_time}\n"

        num_repetitions_per_day = self.calculate_num_repetitions_per_day()

        total_off_minutes = self.interval_length_hours * 60 + self.interval_length_minutes - self.MAX_DURATION_MINUTES
        off_hours = total_off_minutes // 60
        off_minutes = total_off_minutes % 60

        for _ in range(num_repetitions_per_day - 1):
            schedule += f"ON\tM{self.MAX_DURATION_MINUTES}\nOFF\t"

            if off_hours > 0 and off_minutes > 0:
                schedule += f"H{off_hours} M{(off_minutes)}\n"
            elif off_hours > 0 and off_minutes == 0:
                schedule += f"H{off_hours}\n"
            else:
                schedule += f"M{(off_minutes)}\n"

        # Last repetition is different
        schedule += f"ON\tM{self.MAX_DURATION_MINUTES}\n"

        # Turn camera off for the rest of the day (schedule length is 24 hours)
        remaining_minutes = 1440 - (num_repetitions_per_day * (self.interval_length_minutes + self.interval_length_hours * 60))
        remaining_minutes += self.interval_length_minutes + self.interval_length_hours * 60 - self.MAX_DURATION_MINUTES
        remaining_hours = remaining_minutes // 60
        remaining_minutes = remaining_minutes % 60

        if remaining_hours > 0 and remaining_minutes > 0:
            schedule += f"OFF\tH{remaining_hours} M{remaining_minutes}"
        elif remaining_minutes > 0:
            schedule += f"OFF\tM{remaining_minutes}"

        if path.exists(self.SCHEDULE_FILE_PATH):
            with open(self.SCHEDULE_FILE_PATH, "r", encoding='utf-8') as f:
                old_schedule = f.read()

                # Overwrite schedule if it has changed
                if old_schedule != schedule:
                    logging.info("Schedule changed - writing new schedule file.")
                    with open(self.SCHEDULE_FILE_PATH, "w", encoding='utf-8') as f:
                        f.write(schedule)
                else:
                    logging.info("Schedule did not change.")
        else:
            logging.warning("Schedule file not found. Writing new schedule file.")
            with open(self.SCHEDULE_FILE_PATH, "w", encoding='utf-8') as f:
                f.write(schedule)

    def apply_schedule(self) -> str:
        '''Apply schedule to Witty Pi 4'''
        for retry in range(self.MAX_RETRIES):
            try:
                # Apply new schedule
                command = f"cd {self.WITTYPI_DIRECTORY} && sudo ./runScript.sh"
                output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=30)
                output = output.split("\n")[1:3]

                if "Schedule next startup at:" in output[1]:
                    logging.info("%s", output[0])
                    logging.info("%s", output[1])
                    return output[1][-19:] # Next startup time

                logging.warning("Failed to apply schedule: %s", output[0])
                self.sync_time_with_network()

            except Exception as e:
                logging.error("Failed to apply schedule: %s (%s)", str(e), retry)

            sleep(2**retry) # Exponential backoff

        # Return error if max retries reached
        return "-"

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    witty_pi_4 = WittyPi4()
    witty_pi_4.sync_time_with_network()
    witty_pi_4.get_temperature()
    witty_pi_4.get_battery_voltage()
    witty_pi_4.get_internal_voltage()
    witty_pi_4.get_internal_current()
    witty_pi_4.get_low_voltage_threshold()
    witty_pi_4.get_recovery_voltage_threshold()
    witty_pi_4.set_start_time(time(8, 0))
    witty_pi_4.set_end_time(time(20, 0))
    witty_pi_4.set_interval_length(30)
    witty_pi_4.generate_schedule()
    witty_pi_4.apply_schedule()
