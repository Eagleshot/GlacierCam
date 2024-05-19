"""Read and validate the GlacierCam settings from a YAML file"""
from dataclasses import dataclass
import logging
from yaml import safe_load, dump

@dataclass
class Settings:
    """Class to safely load and validate the settings from a YAML file. If the settings are not valid, default values are used."""

    settings_to_check = {
        'cameraName': {'type': str, 'default': 'GlacierCam'},
        'resolution': {'type': list, 'default': [0,0]}, # , 'min': 0, 'max': 0},
        'startTimeHour': {'type': int, 'min': 0, 'max': 23, 'default': 8},
        'startTimeMinute': {'type': int, 'min': 0, 'max': 59, 'default': 0},
        'endTimeHour': {'type': int, 'min': 0, 'max': 23, 'default': 18},
        'endTimeMinute': {'type': int, 'min': 0, 'max': 59, 'default': 0},
        'enableSunriseSunset': {'type': bool, 'default': False},
        'intervalHours': {'type': int, 'min': 0, 'max': 23, 'default': 0},
        'intervalMinutes': {'type': int, 'min': 0, 'max': 59, 'default': 30},
        'timeSync': {'type': bool, 'default': False},
        'enableGPS': {'type': bool, 'default': False},
        'locationOverwrite': {'type': bool, 'default': False},
        'latitude': {'type': float, 'min': -90, 'max': 90, 'default': 0.0},
        'longitude': {'type': float, 'min': -180, 'max': 180, 'default': 0.0},
        'logLevel': {'type': str, 'valid_values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 'default': 'INFO'},
        'uploadExtendedDiagnostics': {'type': bool, 'default': False},
        'lowVoltageThreshold': {'type': float, 'min': 0.0, 'max': 30.0, 'default': 0.0},
        'recoveryVoltageThreshold': {'type': float, 'min': 0.0, 'max': 30.0, 'default': 0.0},
        'batteryVoltageHalf' : {'type': float, 'min': 0, 'max': 30, 'default': 12.0},
        'shutdown': {'type': bool, 'default': True},
    }

    settings = {}
    valid_settings = True


    def __init__(self, settings_filename: str = "settings.yaml") -> None:
        '''Load the settings from a YAML file and validate them.'''
        try:
            with open(settings_filename, encoding='utf-8') as file:
                self.settings = safe_load(file) or {}
        except Exception as e:
            logging.error('Error loading settings: %s', e)
            self.valid_settings = False

        self.__validate()

    def __validate(self) -> bool:
        '''Check if the settings are valid.'''
        for setting, validation in self.settings_to_check.items():

            value = self.settings.get(setting)

            # Check if setting is correct
            if setting not in self.settings or \
                not isinstance(value, validation['type']) or \
                ('min' in validation and value < validation['min']) or \
                ('max' in validation and value > validation['max']) or \
                ('valid_values' in validation and value not in validation['valid_values']):
                logging.warning('Setting %s is not a valid value. Using default value: %s', setting, value)
                self.settings[setting] = validation['default']
                self.valid_settings = False

        return self.valid_settings

    def get(self, key: str):
        '''Return a setting.'''
        return self.settings.get(key)

    def set(self, key: str, value) -> bool:
        '''Set the settings.'''
        if key in self.settings_to_check:
            self.settings[key] = value
            return self.__validate()

        return False

    def is_valid(self) -> bool:
        '''Return if the settings are valid.'''
        return self.valid_settings

    def save_to_file(self, settings_filename: str = "settings.yaml") -> None:
        '''Save the settings to a YAML file.'''
        with open(settings_filename, 'w', encoding='utf-8') as file:
            dump(self.settings, file)
