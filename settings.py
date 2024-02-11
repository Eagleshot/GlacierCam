# Read settings.yaml and validate the settings
from dataclasses import dataclass
from yaml import safe_load, safe_dump

# TODO
# - Check max. / min. values according to the documentation
# - Add default values for settings.yaml
# - Add unittests
# - Add to webserver
# - Add to main.py
# - Add to development readme instructions

@dataclass
class Settings:
    """Class to safely load and validate the settings from a YAML file. If the settings are not valid, the default values are used and the file is saved."""
    def __init__(self, settings_filename: str = "settings.yaml", save: bool = True):

        valid_settings = True
        
        with open(settings_filename, encoding='utf-8') as file:
            self.settings = safe_load(file)

        settings_to_check = {
            'cameraName': {'type': str, 'default': 'GlacierCam'},
            'resolution': {'type': list}, # , 'min': 0, 'max': 0},
            'startTimeHour': {'type': int, 'min': 0, 'max': 23, 'default': 8},
            'startTimeMinute': {'type': int, 'min': 0, 'max': 59, 'default': 0},
            'intervalMinutes': {'type': int, 'min': 1, 'max': 59, 'default': 30},
            'repetitionsPerday': {'type': int, 'min': 1, 'max': 96, 'default': 1},
            'timeSync': {'type': bool, 'default': False},
            'enableGPS': {'type': bool, 'default': False},
            'location_override': {'type': bool, 'default': False},
            'latitude': {'type': float, 'min': -90, 'max': 90, 'default': 0},
            'longitude': {'type': float, 'min': -180, 'max': 180, 'default': 0},
            'height': {'type': int, 'min': -1000, 'max': 10000, 'default': 0},
            'uploadWittyPiDiagnostics': {'type': bool, 'default': False},
            'low_voltage_threshold': {'type': float, 'min': 0, 'max': 30, 'default': 0.0},
            'recovery_voltage_threshold': {'type': float, 'min': 0, 'max': 30, 'default': 0},
            'shutdown': {'type': bool, 'default': True},
        }

        for setting, validation in settings_to_check.items():
            if setting not in self.settings:
                self.settings[setting] = validation['default']
                valid_settings = False

            if not isinstance(self.settings[setting], validation['type']):
                self.settings[setting] = validation['default']
                valid_settings = False

            if 'min' in validation and self.settings[setting] < validation['min']:
                self.settings[setting] = validation['default']
                valid_settings = False

            if 'max' in validation and self.settings[setting] > validation['max']:
                self.settings[setting] = validation['default']
                valid_settings = False

        if save and valid_settings:
            print("Saving file")
            with open('settings.yaml', 'w', encoding='utf-8') as file:
                file.write(safe_dump(self.settings))

    def get_settings(self):
        '''Return the settings'''
        return self.settings
    
    def get(self, key: str):
        '''Return the settings'''
        if key in self.settings:
            return self.settings[key]

        return False

if __name__ == '__main__':
    print('Validating settings.yaml')
    Settings = Settings()
    print('Validation complete')
