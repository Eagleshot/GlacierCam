'''A python module for interacting with the Witty Pi 4 board'''
from subprocess import check_output, STDOUT
from os import path

# Get WittyPi readings
# See: https://www.baeldung.com/linux/run-function-in-script

def run_witty_pi_4_command(command: str) -> str:
    '''Send a command to Witty Pi 4'''
    try:
        command = f"cd /home/pi/wittypi && . ./utilities.sh && {command}"
        output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=5)
        output = output.replace("\n", "")
        return output
    except Exception as e:
        print(f"Could not send Witty Pi 4 command: {str(e)}")
        return "ERROR"

def sync_witty_pi_time_with_network():
    '''Sync WittyPi clock with network time'''

    # See: https://www.uugear.com/forums/technial-support-discussion/witty-pi-4-how-to-synchronise-time-with-internet-on-boot/
    try:
        output = run_witty_pi_4_command("net_to_system && system_to_rtc")
        print(f"Time synchronized with network: {output}")
    except Exception as e:
        print(f"Could not synchronize time with network: {str(e)}")

# Temperature
def get_temperature_witty_pi_4():
    '''Gets the current temperature reading from the Witty Pi 4 in °C'''
    try:
        temperature = run_witty_pi_4_command("get_temperature")
        temperature = temperature.split("/", maxsplit = 1)[0] # Remove the Farenheit reading
        temperature = temperature[:-3] # Remove °C
        print(f"Temperature: {temperature} °C")
        return temperature
    except Exception as e:
        print(f"Could not get temperature: {str(e)}")
        return "-"

# Battery voltage
def get_battery_voltage_witty_pi_4() -> float:
    '''Gets the battery voltage reading from the Witty Pi 4 in V'''
    try:
        battery_voltage = run_witty_pi_4_command("get_input_voltage")
        battery_voltage = float(battery_voltage) # Remove V
        print(f"Battery voltage: {battery_voltage} V")
        return battery_voltage
    except Exception as e:
        print(f"Could not get battery voltage: {str(e)}")
        return 0.0

# Raspberry Pi voltage
def get_internal_voltage_witty_pi_4():
    '''Gets the internal (5V) voltage from the Witty Pi 4 in V'''
    try:
        internal_voltage = run_witty_pi_4_command("get_output_voltage")
        print(f"Output voltage: {internal_voltage} V")
        return internal_voltage
    except Exception as e:
        print(f"Could not get Raspberry Pi voltage: {str(e)}")
        return "-"

# Raspberry Pi current - Not needed at the moment
def get_internal_current_witty_pi_4():
    '''Gets the internal (5V) current reading from the Witty Pi 4 in A'''
    try:
        internal_current = run_witty_pi_4_command("get_output_current")
        print(f"Output current: {internal_current} A")
        return internal_current
    except Exception as e:
        print(f"Could not get Raspberry Pi current: {str(e)}")
        return "-"
    
# Get low voltage treshold
def get_low_voltage_treshold_witty_pi_4():
    '''Gets the low treshold from the Witty Pi 4'''
    try:
        low_voltage_treshold = run_witty_pi_4_command("get_low_voltage_threshold")[:-1]
        print(f"Low voltage treshold: {low_voltage_treshold} V")
        return low_voltage_treshold
    except Exception as e:
        print(f"Could not get low voltage treshold: {str(e)}")
        return "-"

# Get recovery voltage treshold
def get_recovery_voltage_treshold_witty_pi_4():
    '''Gets the recovery treshold from the Witty Pi 4'''
    try:
        recovery_voltage_treshold = run_witty_pi_4_command("get_recovery_voltage_threshold")[:-1]
        print(f"Recovery voltage treshold: {recovery_voltage_treshold} V")
        return recovery_voltage_treshold
    except Exception as e:
        print(f"Could not get recovery voltage treshold: {str(e)}")
        return "-"

# Set low voltage treshold
def set_low_voltage_treshold_witty_pi_4(voltage: float):
    '''Sets the low voltage treshold from the Witty Pi 4'''
    try:
        low_voltage_treshold = run_witty_pi_4_command(f"set_low_voltage_threshold {int(voltage*10)}")
        print(f"Set low voltage treshold to: {voltage} V")
        return low_voltage_treshold
    except Exception as e:
        print(f"Could not set low voltage treshold: {str(e)}")
        return "-"

# Set recovery voltage treshold
def set_recovery_voltage_treshold_witty_pi_4(voltage: float):
    '''Sets the recovery voltage treshold from the Witty Pi 4'''
    try:
        recovery_voltage_treshold = run_witty_pi_4_command(f"set_recovery_voltage_threshold {int(voltage*10)}")
        print(f"Set recovery voltage treshold to: {voltage} V")
        return recovery_voltage_treshold
    except Exception as e:
        print(f"Could not set recovery voltage treshold: {str(e)}")
        return "-"

def generate_schedule(startTimeHour: int, startTimeMinute: int, intervalMinutes: int, repetitionsPerday: int):
    '''Generate a startup schedule file for Witty Pi 4'''

    max_duration_minutes = 4

    # Basic validity check of parameters
    if not 0 < startTimeHour < 24:
        startTimeHour = 8

    if not 0 < startTimeMinute < 60:
        startTimeMinute = 0

    if not 0 < intervalMinutes < 1440:
        intervalMinutes = 30

    if not 0 < repetitionsPerday < 250:
        repetitionsPerday = 8

    if ((repetitionsPerday * intervalMinutes) + startTimeMinute + (startTimeHour * 60)) > 1440:
        repetitionsPerday = 1

    # 2037 is the maximum year for WittyPi
    formatted_start_time = f"{startTimeHour:02d}:{startTimeMinute:02d}"
    schedule = f"BEGIN\t2020-01-01 {formatted_start_time}:00\nEND\t2037-12-31 23:59:59\n"

    for i in range(repetitionsPerday):
        schedule += f"ON\tM{max_duration_minutes}\n"

        # Last off is different
        if i < repetitionsPerday - 1:
            schedule += f"OFF\tM{intervalMinutes - max_duration_minutes}\n"

    # Turn camera off for the rest of the day
    remaining_minutes = 1440 - (repetitionsPerday * intervalMinutes) + (intervalMinutes - max_duration_minutes)
    remaining_hours = remaining_minutes // 60
    remaining_minutes = remaining_minutes % 60

    schedule += f"OFF\tH{remaining_hours}"
    if remaining_minutes > 0:
        schedule += f" M{remaining_minutes}"

    SCHEDULE_FILE_PATH = "/home/pi/wittypi/schedule.wpi"

    if path.exists(SCHEDULE_FILE_PATH):
        with open(SCHEDULE_FILE_PATH, "r", encoding='utf-8') as f:
            oldSchedule = f.read()

            # Write new schedule file if it changed
            if oldSchedule != schedule:
                print("Writing and applying new schedule file.")
                with open(SCHEDULE_FILE_PATH, "w", encoding='utf-8') as f:
                    f.write(schedule)
            else:
                print("Schedule did not change.")
    else:
        print("Writing and applying new schedule file.")
        with open(SCHEDULE_FILE_PATH, "w", encoding='utf-8') as f:
            f.write(schedule)

    
def apply_schedule_witty_pi_4(max_retries: int = 5) -> str:
    '''Apply schedule to Witty Pi 4'''
    # TODO: Maybe check check_sys_and_rtc_time() in utilities.sh first
    try:
        for i in range(max_retries):
            # Apply new schedule
            command = "cd /home/pi/wittypi && sudo ./runScript.sh"
            output = check_output(command, shell=True, executable="/bin/bash", stderr=STDOUT, universal_newlines=True, timeout=10)
            output = output.split("\n")[1:3]

            if not "Schedule next startup at:" in output[1]:
                print(f"Failed to apply schedule: {output[0]}")
                sync_witty_pi_time_with_network()
            else:
                print(f"{output[0]}\n{output[1]}")
                next_startup_time = output[1][-19:]
                return next_startup_time

    except Exception as e:
        print(f"Failed to apply schedule: {str(e)}")
        return "-"