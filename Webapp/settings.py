# Read settings.yaml and validate the settings
from dataclasses import dataclass
from yaml import safe_load

# TODO
# - Check max. / min. values according to the documentation
# - Add unittests
# - Add to webserver
# - Add to main.py
# - Add to development readme instructions

@dataclass
class Settings:
    """Class to safely load and validate the YAML settings file"""
    def __init__(self, settings_filename: str = "settings.yaml"):

        with open(settings_filename, encoding='utf-8') as file:
            self.settings = safe_load(file)

        settings_to_check = {
            'resolution': {'type': list, 'min': 0, 'max': 0},
            'startTimeHour': {'type': int, 'min': 0, 'max': 23},
            'startTimeMinute': {'type': int, 'min': 0, 'max': 59},
            'intervalMinutes': {'type': int, 'min': 1, 'max': 59},
            'repetitionsPerday': {'type': int, 'min': 1, 'max': 96},
            'timeSync': {'type': bool},
            'enableGPS': {'type': bool},
            'location_override': {'type': bool},
            'location_override': {'type': bool},
            'latitude': {'type': float, 'min': -90, 'max': 90},
            'longitude': {'type': float, 'min': -180, 'max': 180},
            'height': {'type': float, 'min': -1000, 'max': 10000},
            'uploadWittyPiDiagnostics': {'type': bool},
            'low_voltage_threshold': {'type': float, 'min': 0, 'max': 30},
            'recovery_voltage_threshold': {'type': float, 'min': 0, 'max': 30},
            'shutdown': {'type': bool}
        }

        for setting, validation in settings_to_check.items():
            if setting not in self.settings:
                raise ValueError(f'{setting} not defined in settings.yaml')

            if not isinstance(self.settings[setting], validation['type']):
                raise ValueError(f'{setting} must be {validation["type"].__name__}')

            if 'min' in validation and self.settings[setting] < validation['min']:
                raise ValueError(f'{setting} must be greater than or equal to {validation["min"]}')

            if 'max' in validation and self.settings[setting] > validation['max']:
                raise ValueError(f'{setting} must be less than or equal to {validation["max"]}')


if __name__ == '__main__':
    print('Validating settings.yaml')
    Settings = Settings()
    print('Validation complete')
