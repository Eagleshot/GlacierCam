# Read settings.yaml and validate the settings
from yaml import safe_load

# TODO
# - Check max. / min. values according to the documentation
# - Add to webserver
# - Add to main.py
# - Add to development readme instructions

class SettingsValidator:
    """Class to validate the settings.yaml file"""
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.settings = self.load_settings()

    def load_settings(self):
        """Load settings from file"""
        with open(self.settings_file, 'r', encoding='utf-8') as f:
            settings = safe_load(f)
        return settings

    def validate_settings(self):
        """Validate the settings file"""

        # cameraName
        if 'cameraName' not in self.settings:
            raise ValueError('Camera name not defined in settings.yaml')

        if not isinstance(self.settings['cameraName'], str):
            raise ValueError('Camera name must be a string')

        # lensPosition
        if 'lensPosition' not in self.settings:
            raise ValueError('Lens position not defined in settings.yaml')

        if not isinstance(self.settings['lensPosition'], float):
            raise ValueError('Lens position must be a float')

        # resolution
        if 'resolution' not in self.settings:
            raise ValueError('Resolution not defined in settings.yaml')

        if not isinstance(self.settings['resolution'], list):
            raise ValueError('Resolution must be a list')

        if len(self.settings['resolution']) != 2:
            raise ValueError('Resolution must have two elements')

        if not isinstance(self.settings['resolution'][0], int):
            raise ValueError('Resolution must be a list of integers')

        if not isinstance(self.settings['resolution'][1], int):
            raise ValueError('Resolution must be a list of integers')

        # startTimeHour
        if 'startTimeHour' not in self.settings:
            raise ValueError('Start time hour not defined in settings.yaml')

        if not isinstance(self.settings['startTimeHour'], int):
            raise ValueError('Start time hour must be an integer')

        if self.settings['startTimeHour'] < 0 or self.settings['startTimeHour'] > 23:
            raise ValueError('Start time hour must be between 0 and 23')

        # startTimeMinute
        if 'startTimeMinute' not in self.settings:
            raise ValueError('Start time minute not defined in settings.yaml')

        if not isinstance(self.settings['startTimeMinute'], int):
            raise ValueError('Start time minute must be an integer')

        if self.settings['startTimeMinute'] < 0 or self.settings['startTimeMinute'] > 59:
            raise ValueError('Start time minute must be between 0 and 59')

        # intervalMinutes
        if 'intervalMinutes' not in self.settings:
            raise ValueError('Interval minutes not defined in settings.yaml')

        if not isinstance(self.settings['intervalMinutes'], int):
            raise ValueError('Interval minutes must be an integer')

        if self.settings['intervalMinutes'] < 1 or self.settings['intervalMinutes'] > 59:
            raise ValueError('Interval minutes must be between 1 and 59')

        # repetitionsPerday
        if 'repetitionsPerday' not in self.settings:
            raise ValueError('Repetitions per day not defined in settings.yaml')

        if not isinstance(self.settings['repetitionsPerday'], int):
            raise ValueError('Repetitions per day must be an integer')

        if self.settings['repetitionsPerday'] < 1 or self.settings['repetitionsPerday'] > 96:
            raise ValueError('Repetitions per day must be between 1 and 24')

        # timeSync
        if 'timeSync' not in self.settings:
            raise ValueError('Time sync not defined in settings.yaml')

        if not isinstance(self.settings['timeSync'], bool):
            raise ValueError('Time sync must be a boolean')

        # enableGPS
        if 'enableGPS' not in self.settings:
            raise ValueError('Enable GPS not defined in settings.yaml')

        if not isinstance(self.settings['enableGPS'], bool):
            raise ValueError('Enable GPS must be a boolean')

        # location_override
        if 'location_override' not in self.settings:
            raise ValueError('Location override not defined in settings.yaml')

        if not isinstance(self.settings['location_override'], bool):
            raise ValueError('Location override must be a boolean')

        # latitude
        if 'latitude' not in self.settings:
            raise ValueError('Latitude not defined in settings.yaml')

        if not isinstance(self.settings['latitude'], float):
            raise ValueError('Latitude must be a float')

        if self.settings['latitude'] < -90 or self.settings['latitude'] > 90:
            raise ValueError('Latitude must be between -90 and 90')

        # longitude
        if 'longitude' not in self.settings:
            raise ValueError('Longitude not defined in settings.yaml')

        if not isinstance(self.settings['longitude'], float):
            raise ValueError('Longitude must be a float')

        if self.settings['longitude'] < -180 or self.settings['longitude'] > 180:
            raise ValueError('Longitude must be between -180 and 180')

        # height
        if 'height' not in self.settings:
            raise ValueError('Height not defined in settings.yaml')

        if not isinstance(self.settings['height'], int):
            raise ValueError('Height must be an integer')

        if self.settings['height'] < 0 or self.settings['height'] > 10000:
            raise ValueError('Height must be between 0 and 10000')

        # enableSunriseSunset
        if 'enableSunriseSunset' not in self.settings:
            raise ValueError('Enable sunrise/sunset not defined in settings.yaml')

        if not isinstance(self.settings['enableSunriseSunset'], bool):
            raise ValueError('Enable sunrise/sunset must be a boolean')

        # shutdown
        if 'shutdown' not in self.settings:
            raise ValueError('Shutdown not defined in settings.yaml')

        if not isinstance(self.settings['shutdown'], bool):
            raise ValueError('Shutdown must be a boolean')

if __name__ == '__main__':
    print('Validating settings.yaml')
    validator = SettingsValidator("settings.yaml")
    validator.validate_settings()
    print('Validation complete')

# cameraName: "Camera1"
# lensPosition: -1.0
# resolution: [0, 0]
# startTimeHour: 8
# startTimeMinute: 0
# intervalMinutes: 30
# repetitionsPerday: 16
# timeSync: false
# enableGPS: false
# location_override: false
# latitude: 0.0
# longitude: 0.0
# height: 0
# enableSunriseSunset: false
# shutdown: false
# uploadWittyPiDiagnostics: false
# low_voltage_threshold: 0.0
# recovery_voltage_threshold: 0.0
