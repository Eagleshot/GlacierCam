# Read settings.yaml and validate the settings
from dataclasses import dataclass
import logging
from yaml import safe_load

# TODO
# - Check max. / min. values according to the documentation
# - Add default values for settings.yaml
# - Also check settings with set
# - Add unittests
# - Add to webserver
# - Add to main.py
# - Add to development readme instructions

@dataclass
class Settings:
    """Class to safely load and validate the settings from a YAML file. If the settings are not valid, the default values are used."""
    def __init__(self, settings_filename: str = "settings.yaml") -> None:
        self.valid_settings = True
        self.valid_settings = self.load_and_validate(settings_filename)

    def load_and_validate(self, settings_filename: str = "settings.yaml") -> bool:
        '''Load the settings and validate them'''
        try:
            with open(settings_filename, encoding='utf-8') as file:
                self.settings = safe_load(file)
        except Exception as e:
            logging.error('Error loading settings: %s', e)
            self.settings = {}
            self.valid_settings = False

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
            'location_override': {'type': bool, 'default': False},
            'latitude': {'type': float, 'min': -90, 'max': 90, 'default': 0},
            'longitude': {'type': float, 'min': -180, 'max': 180, 'default': 0},
            'enableSunriseSunset': {'type': bool, 'default': False},
            'uploadWittyPiDiagnostics': {'type': bool, 'default': False},
            'low_voltage_threshold': {'type': float, 'min': 0, 'max': 30, 'default': 0.0},
            'recovery_voltage_threshold': {'type': float, 'min': 0, 'max': 30, 'default': 0},
            'battery_voltage_half' : {'type': float, 'min': 0, 'max': 30, 'default': 12.0},
            'shutdown': {'type': bool, 'default': True},
        }

        for setting, validation in settings_to_check.items():
            if setting not in self.settings:
                self.settings[setting] = validation['default']
                logging.warning('Setting %s not found. Using default value: %s', setting, self.settings[setting])
                self.valid_settings = False

            if not isinstance(self.settings[setting], validation['type']):
                self.settings[setting] = validation['default']
                logging.warning('Setting %s is not of type %s. Using default value: %s', setting, validation['type'], self.settings[setting])
                self.valid_settings = False

            if 'min' in validation and self.settings[setting] < validation['min']:
                self.settings[setting] = validation['default']
                logging.warning('Setting %s is less than %s. Using default value: %s', setting, validation['min'], self.settings[setting])
                self.valid_settings = False

            if 'max' in validation and self.settings[setting] > validation['max']:
                self.settings[setting] = validation['default']
                logging.warning('Setting %s is greater than %s. Using default value: %s', setting, validation['max'], self.settings[setting])
                self.valid_settings = False

        return self.valid_settings

    def get(self, key: str):
        '''Return the settings'''
        if key in self.settings:
            return self.settings[key]

        return None

    def set(self, key: str, value):
        '''Set the settings'''
        
        self.settings[key] = value

    def is_valid(self) -> bool:
        '''Return if the settings are valid'''
        return self.valid_settings
