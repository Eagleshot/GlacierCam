from datetime import time
from os import remove
from witty_pi_4 import WittyPi4

# def test_set_low_voltage_threshold()
# def test_set_recovery_voltage_threshold()
# def test_set_recovery_voltage_threshold()

def test_set_start_time():
    """Test setting a valid start time."""
    witty_pi = WittyPi4()
    witty_pi.set_start_time(time(5, 0))
    assert witty_pi.start_time == time(5, 0)
    witty_pi.set_start_time(time(0, 0))
    assert witty_pi.start_time == time(0, 0)

def test_set_start_time_invalid():
    """Test setting an invalid start time."""
    witty_pi = WittyPi4()
    witty_pi.set_interval_length(15)
    witty_pi.set_start_time(time(23, 46))
    assert witty_pi.start_time == time(8, 0)

    witty_pi.set_interval_length(30, 1)
    witty_pi.set_start_time(time(22, 32))
    assert witty_pi.start_time == time(8, 0)

def test_set_end_time():
    '''Test setting a valid end time.'''
    witty_pi = WittyPi4()
    witty_pi.set_end_time(time(5, 0))
    assert witty_pi.end_time == time(5, 0)
    witty_pi.set_end_time(time(23, 59))
    assert witty_pi.end_time == time(23, 59)

# def test_set_start_end_time_sunrise() # TODO

def test_set_interval_length_valid():
    '''Test setting a valid interval length.'''
    witty_pi = WittyPi4()
    witty_pi.set_interval_length(15)
    assert witty_pi.interval_length_minutes == 15
    witty_pi.set_interval_length(30, 1)
    assert witty_pi.interval_length_minutes == 30
    assert witty_pi.interval_length_hours == 1

def test_set_interval_length_invalid():
    '''Test setting an invalid interval length.'''
    witty_pi = WittyPi4()
    witty_pi.set_interval_length(0)
    assert witty_pi.interval_length_minutes == 30
    witty_pi.set_interval_length(60, 24)
    assert witty_pi.interval_length_minutes == 30
    assert witty_pi.interval_length_hours == 0
    witty_pi.set_interval_length(-1, -1)
    assert witty_pi.interval_length_minutes == 30
    assert witty_pi.interval_length_hours == 0

def test_double_interval_length():
    '''Test doubling the interval length.'''
    witty_pi = WittyPi4()
    witty_pi.set_interval_length(17)
    witty_pi.double_interval_length()
    assert witty_pi.interval_length_minutes == 34
    assert witty_pi.interval_length_hours == 0
    witty_pi.double_interval_length()
    assert witty_pi.interval_length_minutes == 8
    assert witty_pi.interval_length_hours == 1
    witty_pi.double_interval_length()
    assert witty_pi.interval_length_minutes == 16
    assert witty_pi.interval_length_hours == 2
    witty_pi.double_interval_length() # 4:32
    witty_pi.double_interval_length() # 9:4
    witty_pi.double_interval_length() # 18:8
    witty_pi.double_interval_length() # 37:16
    assert witty_pi.interval_length_minutes == 16
    assert witty_pi.interval_length_hours == 18

def test_single_startup_interval():
    '''Test setting a single startup interval.'''
    witty_pi = WittyPi4()
    witty_pi.set_start_time(time(0, 0))
    witty_pi.set_end_time(time(15, 28))
    witty_pi.set_interval_length(15)
    witty_pi.single_startup_interval()
    assert witty_pi.start_time == time(0, 0)
    assert witty_pi.end_time == time(0, 0)
    assert witty_pi.calculate_num_repetitions_per_day() == 1

def test_round_time_to_nearest_interval():
    """Test the rounding of a time to the nearest interval."""

    witty_pi = WittyPi4()

    # 15 minutes interval
    witty_pi.set_interval_length(15)
    rounded_time = witty_pi.round_time_to_nearest_interval(time(5, 15))
    assert rounded_time == time(5, 15)
    rounded_time = witty_pi.round_time_to_nearest_interval(time(5, 20))
    assert rounded_time == time(5, 15)
    rounded_time = witty_pi.round_time_to_nearest_interval(time(5, 30))
    assert rounded_time == time(5, 30)

    # 30 minutes interval
    witty_pi.set_interval_length(30)
    rounded_time = witty_pi.round_time_to_nearest_interval(time(5, 20))
    assert rounded_time == time(5, 0)

    # 5 minutes interval
    witty_pi.set_interval_length(5)
    rounded_time = witty_pi.round_time_to_nearest_interval(time(5, 32))
    assert rounded_time == time(5, 30)

    # 29 minutes interval
    witty_pi.set_interval_length(29)
    rounded_time = witty_pi.round_time_to_nearest_interval(time(5, 30))
    assert rounded_time == time(5, 29)

def test_calculate_num_repetitions_per_day():
    """Test the calculation of the number of repetitions per day."""

    witty_pi = WittyPi4()
    witty_pi.set_start_time(time(0, 0))
    witty_pi.set_end_time(time(0, 17))
    witty_pi.set_interval_length(5)
    repetitions = witty_pi.calculate_num_repetitions_per_day()
    assert repetitions == 4

    witty_pi.set_start_time(time(5, 0))
    witty_pi.set_end_time(time(6, 0))
    witty_pi.set_interval_length(15)
    repetitions = witty_pi.calculate_num_repetitions_per_day()
    assert repetitions == 5

    witty_pi = WittyPi4()
    witty_pi.set_start_time(time(6, 0))
    witty_pi.set_end_time(time(18, 0))
    witty_pi.set_interval_length(0, 1)
    repetitions = witty_pi.calculate_num_repetitions_per_day()
    assert repetitions == 13

def test_calculate_num_repetitions_per_day_long_interval():
    """Test the calculation of the number of repetitions per day with a long interval."""
    witty_pi = WittyPi4()
    witty_pi.set_start_time(time(6, 0))
    witty_pi.set_end_time(time(6, 15))
    witty_pi.set_interval_length(1350)
    repetitions = witty_pi.calculate_num_repetitions_per_day()
    assert repetitions == 1

def test_calculate_num_repetitions_per_day_identical_start_end_time():
    '''Test the calculation of the number of repetitions per day with identical start and end time.'''
    witty_pi = WittyPi4()
    witty_pi.set_start_time(time(8, 0))
    witty_pi.set_end_time(time(8, 0))
    repetitions = witty_pi.calculate_num_repetitions_per_day()
    assert repetitions == 1

    witty_pi.set_start_time(time(20, 32))
    witty_pi.set_end_time(time(20, 32))
    repetitions = witty_pi.calculate_num_repetitions_per_day()
    assert repetitions == 1

def test_calculate_num_repetitions_per_day_start_time_after_end_time():
    '''Test the calculation of the number of repetitions per day with start time after end time.'''
    witty_pi = WittyPi4()
    witty_pi.set_start_time(time(8, 0))
    witty_pi.set_end_time(time(7, 0))
    witty_pi.set_interval_length(15)
    repetitions = witty_pi.calculate_num_repetitions_per_day()
    assert repetitions == 5

def test_generate_valid_schedule_minute_interval():
    """Test the generation of a valid schedule."""
    witty_pi = WittyPi4()
    witty_pi.SCHEDULE_FILE_PATH = "test_schedule.txt"
    witty_pi.set_start_time(time(7, 30))
    witty_pi.set_end_time(time(11, 00))
    witty_pi.set_interval_length(30)
    witty_pi.generate_schedule()

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 07:30:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tM26\nON\tM4\nOFF\tH20 M26"
    assert lines == text

    # Overwrite schedule
    witty_pi = WittyPi4()
    witty_pi.SCHEDULE_FILE_PATH = "test_schedule.txt"
    witty_pi.set_start_time(time(12, 0))
    witty_pi.set_end_time(time(12, 5))
    witty_pi.set_interval_length(5)
    witty_pi.generate_schedule()

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 12:00:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tM1\nON\tM4\nOFF\tH23 M51"
    assert lines == text

    # Delete schedule file
    remove(witty_pi.SCHEDULE_FILE_PATH)


def test_generate_valid_schedule_hour_interval():
    """Test the generation of a valid schedule."""
    witty_pi = WittyPi4()
    witty_pi.SCHEDULE_FILE_PATH = "test_schedule.txt"
    witty_pi.set_start_time(time(12, 0))
    witty_pi.set_end_time(time(13, 5))
    witty_pi.set_interval_length(0, 1)
    witty_pi.generate_schedule()

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 12:00:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tM56\nON\tM4\nOFF\tH22 M56"
    assert lines == text

    # Second test
    witty_pi.set_start_time(time(9, 0))
    witty_pi.set_end_time(time(12, 25))
    witty_pi.set_interval_length(4, 1)
    witty_pi.generate_schedule()

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 09:00:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tH1\nON\tM4\nOFF\tH1\nON\tM4\nOFF\tH1\nON\tM4\nOFF\tH20 M44"
    assert lines == text

    # Third test
    witty_pi.set_start_time(time(17, 0))
    witty_pi.set_end_time(time(18, 35))
    witty_pi.set_interval_length(27, 1)
    witty_pi.generate_schedule()

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 17:00:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tH1 M23\nON\tM4\nOFF\tH22 M29"
    assert lines == text

    # Delete schedule file
    remove(witty_pi.SCHEDULE_FILE_PATH)

def test_generate_invalid_schedule():
    """Test the generation of a valid schedule."""
    witty_pi = WittyPi4()
    witty_pi.SCHEDULE_FILE_PATH = "test_schedule.txt"
    witty_pi.start_time = time(23, 59)
    witty_pi.end_time = time(23, 30)
    witty_pi.set_interval_length(31)
    witty_pi.generate_schedule()

    # Read schedule file
    with open(witty_pi.SCHEDULE_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.read()

    # Check schedule
    text = "BEGIN\t2020-01-01 23:30:00\nEND\t2037-12-31 23:59:59\nON\tM4\nOFF\tH23 M56"
    assert lines == text

    # Delete schedule file
    remove(witty_pi.SCHEDULE_FILE_PATH)
