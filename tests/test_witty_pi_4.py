from datetime import datetime
from os import remove
from witty_pi_4 import WittyPi4

def test_round_time_to_nearest_interval():
    """Test the rounding of a time to the nearest interval."""

    witty_pi = WittyPi4()

    sunrise = datetime(2021, 1, 1, 5, 15)
    rounded_sunrise = witty_pi.round_time_to_nearest_interval(sunrise, 15)
    assert rounded_sunrise == sunrise

    sunrise = datetime(2021, 1, 1, 5, 20)
    rounded_sunrise = witty_pi.round_time_to_nearest_interval(sunrise, 15)
    assert rounded_sunrise == datetime(2021, 1, 1, 5, 15)

    sunrise = datetime(2021, 1, 1, 5, 30)
    rounded_sunrise = witty_pi.round_time_to_nearest_interval(sunrise, 15)
    assert rounded_sunrise == datetime(2021, 1, 1, 5, 30)

    sunrise = datetime(2021, 1, 1, 5, 20)
    rounded_sunrise = witty_pi.round_time_to_nearest_interval(sunrise, 30)
    assert rounded_sunrise == datetime(2021, 1, 1, 5, 0)

    sunrise = datetime(2021, 1, 1, 5, 32)
    rounded_sunrise = witty_pi.round_time_to_nearest_interval(sunrise, 5)
    assert rounded_sunrise == datetime(2021, 1, 1, 5, 30)

    sunrise = datetime(2021, 1, 1, 5, 30)
    rounded_sunrise = witty_pi.round_time_to_nearest_interval(sunrise, 29)
    assert rounded_sunrise == datetime(2021, 1, 1, 5, 29)

def test_calculate_num_repetitions_per_day():
    """Test the calculation of the number of repetitions per day."""

    witty_pi = WittyPi4()

    start_time = datetime(2021, 1, 1, 0, 0)
    end_time = datetime(2021, 1, 1, 0, 17)
    interval = 3
    repetitions = witty_pi.calculate_num_repetitions_per_day(start_time, end_time, interval)
    assert repetitions == 6

    start_time = datetime(2021, 1, 1, 5, 0)
    end_time = datetime(2021, 1, 1, 6, 0)
    interval = 15
    repetitions = witty_pi.calculate_num_repetitions_per_day(start_time, end_time, interval)
    assert repetitions == 5

    start_time = datetime(2021, 1, 1, 6, 0)
    end_time = datetime(2021, 1, 1, 18, 0)
    interval = 60
    repetitions = witty_pi.calculate_num_repetitions_per_day(start_time, end_time, interval)
    assert repetitions == 13

def test_generate_valid_schedule():
    """Test the generation of a valid schedule."""

    witty_pi = WittyPi4()

    witty_pi.SCHEDULE_FILE_PATH = "test_schedule.txt"

    # Generate schedule
    start_hour = 7
    start_minute = 30
    interval_length_minutes = 30
    num_repetitions_per_day = 8
    witty_pi.generate_schedule(start_hour, start_minute, interval_length_minutes, num_repetitions_per_day)

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 07:30:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tH20 M26"
    assert lines == text

    # Overwrite schedule
    start_hour = 12
    start_minute = 00
    interval_length_minutes = 5
    num_repetitions_per_day = 2
    witty_pi.generate_schedule(start_hour, start_minute, interval_length_minutes, num_repetitions_per_day)

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 12:00:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tM1\nON\tM4\nOFF\tH23 M51"
    assert lines == text

    # Delete schedule file
    remove(witty_pi.SCHEDULE_FILE_PATH)


def test_generate_invalid_schedule():
    """Test the generation of a valid schedule."""

    witty_pi = WittyPi4()

    witty_pi.SCHEDULE_FILE_PATH = "test_schedule.txt"

    # Generate schedule
    start_hour = 23
    start_minute = 62
    interval_length_minutes = 2000
    num_repetitions_per_day = 99999
    witty_pi.generate_schedule(start_hour, start_minute, interval_length_minutes, num_repetitions_per_day)

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 23:00:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tH23 M56"
    assert lines == text

    # Delete schedule file
    remove(witty_pi.SCHEDULE_FILE_PATH)
