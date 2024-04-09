"""Read and validate the GlacierCam settings from a YAML file"""
from dataclasses import dataclass
import logging
from yaml import safe_load, dump

@dataclass
class Settings:
    """Class to safely load and validate the settings from a YAML file. If the settings are not valid, default values are used."""

    settings_to_check = {
        'cameraName': {'type': str, 'default': 'GlacierCam'},
        'lensPosition': {'type': float, 'min': -1.0, 'max': 10.0, 'default': -1.0},
        'resolution': {'type': list, 'default': [0,0]}, # , 'min': 0, 'max': 0},
        'startTimeHour': {'type': int, 'min': 0, 'max': 23, 'default': 8},
        'startTimeMinute': {'type': int, 'min': 0, 'max': 59, 'default': 0},
        'intervalMinutes': {'type': int, 'min': 1, 'max': 59, 'default': 30},
        'repetitionsPerday': {'type': int, 'min': 1, 'max': 96, 'default': 1},
        'timeSync': {'type': bool, 'default': False},
        'enableGPS': {'type': bool, 'default': False},
        'location_overwrite': {'type': bool, 'default': False},
        'latitude': {'type': float, 'min': -90, 'max': 90, 'default': 0.0},
        'longitude': {'type': float, 'min': -180, 'max': 180, 'default': 0.0},
        'enableSunriseSunset': {'type': bool, 'default': False},
        'logLevel': {'type': str, 'valid_values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 'default': 'INFO'},
        'uploadWittyPiDiagnostics': {'type': bool, 'default': False},
        'low_voltage_threshold': {'type': float, 'min': 0.0, 'max': 30.0, 'default': 0.0},
        'recovery_voltage_threshold': {'type': float, 'min': 0.0, 'max': 30.0, 'default': 0.0},
        'battery_voltage_half' : {'type': float, 'min': 0, 'max': 30, 'default': 12.0},
        'shutdown': {'type': bool, 'default': True},
    }

    def __init__(self, settings_filename: str = "settings.yaml") -> None:

        self.valid_settings = True

        try:
            with open(settings_filename, encoding='utf-8') as file:
                self.settings = safe_load(file)
        except Exception as e:
            logging.error('Error loading settings: %s', e)
            self.settings = {}
            self.valid_settings = False

        self.validate()

    def validate(self) -> bool:
        '''Load the settings and validate them'''
        for setting, validation in self.settings_to_check.items():

            # Check if setting exists
            if setting not in self.settings:
                self.settings[setting] = validation['default']
                logging.warning('Setting %s not found. Using default value: %s', setting, self.settings[setting])
                self.valid_settings = False

            # Check if setting is of the correct type
            if not isinstance(self.settings[setting], validation['type']):
                self.settings[setting] = validation['default']
                logging.warning('Setting %s is not of type %s. Using default value: %s', setting, validation['type'], self.settings[setting])
                self.valid_settings = False

            # Check if setting is within valid range
            if 'min' in validation and self.settings[setting] < validation['min']:
                self.settings[setting] = validation['default']
                logging.warning('Setting %s is less than %s. Using default value: %s', setting, validation['min'], self.settings[setting])
                self.valid_settings = False

            if 'max' in validation and self.settings[setting] > validation['max']:
                self.settings[setting] = validation['default']
                logging.warning('Setting %s is greater than %s. Using default value: %s', setting, validation['max'], self.settings[setting])
                self.valid_settings = False

            if 'valid_values' in validation and self.settings[setting] not in validation['valid_values']:
                self.settings[setting] = validation['default']
                logging.warning('Setting %s is not a valid value. Using default value: %s', setting, self.settings[setting])
                self.valid_settings = False

        return self.valid_settings

    def get(self, key: str):
        '''Return the settings'''
        if key in self.settings:
            return self.settings[key]

        return None

    def set(self, key: str, value) -> bool:
        '''Set the settings'''
        if key in self.settings:
            self.settings[key] = value
            self.valid_settings = self.validate()

        return self.valid_settings

    def is_valid(self) -> bool:
        '''Return if the settings are valid'''
        return self.valid_settings

    def save_to_file(self, settings_filename: str = "settings.yaml"):
        '''Save the settings to a file'''
        with open(settings_filename, 'w', encoding='utf-8') as file:
            dump(self.settings, file)
