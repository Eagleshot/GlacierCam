import os
from sys import path
import tempfile
from yaml import safe_load, dump
path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import Settings

def test_load_and_validate_valid_file():
    """Test loading a valid settings file and assert that the settings are valid"""
    settings = Settings()
    assert settings.is_valid()

def test_load_and_validate_invalid_file():
    """Test loading an invalid settings file and assert that the settings are not valid"""

    with open('settings.yaml', 'r', encoding='utf-8') as file:
        settings_dict = safe_load(file)

    settings_dict['cameraName'] = 123

    # Create mock file with invalid settings
    temp_filename = tempfile.mktemp(".yaml")

    with open(temp_filename, 'w', encoding='utf-8') as file:
        dump(settings_dict, file)

    settings = Settings(temp_filename)

    # Clean up the mock file
    os.remove(temp_filename)

    assert isinstance(settings.get('cameraName'), str)
    assert settings.get('cameraName') == 'GlacierCam'
    assert not settings.is_valid()

def test_load_and_validate_non_existing_file():
    """Test loading a non-existing settings file and assert that the settings are not valid"""
    settings = Settings('non-existing.yaml')
    assert isinstance(settings.get('cameraName'), str)
    assert settings.get('cameraName') == 'GlacierCam'
    assert not settings.is_valid()

def test_missing_required_setting():
    """Test missing a required setting and assert that the default value is used"""
    settings = Settings("invalid_settings.yaml")
    assert 'enableSunriseSunset' in settings.settings
    assert settings.get('enableSunriseSunset') is False

def test_setting_and_getting_values():
    """Test setting and getting values for both existing and new settings"""
    settings = Settings()
    settings.set('cameraName', 'This is a test')
    assert settings.get('cameraName') == 'This is a test'

    settings.set('resolution', [1920, 1080])
    assert settings.get('resolution') == [1920, 1080]

    settings.set('endTimeHour', 20)
    assert settings.get('endTimeHour') == 20

    assert not settings.set('invalidSetting', 'Invalid')
    assert settings.get('invalidSetting') is None

def test_invalid_setting_type():
    """Test setting an invalid type for a setting and assert that it is reset to the default value"""
    settings = Settings()

    assert not settings.set('cameraName', 123)
    assert settings.get('cameraName') == 'GlacierCam'

    assert not settings.set('enableGPS', 'invalid')
    assert settings.get('enableGPS') is False

def test_setting_outside_range():
    """Test setting a value outside the specified range for a setting and assert that it is reset to the default value"""
    settings = Settings()
    assert not settings.set('lowVoltageThreshold', 30.1)
    assert settings.get('lowVoltageThreshold') == 0.0

    assert not settings.set('startTimeHour', 25)
    assert settings.get('startTimeHour') == 8

def test_setting_valid_values_list():
    """Test setting a value that must be in a list of valid values and assert that it is reset to the default value"""
    settings = Settings()
    assert settings.set('logLevel', 'DEBUG')
    assert settings.get('logLevel') == 'DEBUG'
    assert not settings.set('logLevel', 'INVALID')
    assert settings.get('logLevel') == 'INFO'

def test_save_to_file():
    """Test saving the settings to a file and assert that the file is created and contains the correct settings"""
    settings = Settings()
    settings.set('cameraName', 'NewCamera')

    temp_filename = tempfile.mktemp(".yaml")
    settings.save_to_file(temp_filename)

    assert os.path.exists(temp_filename)

    with open(temp_filename, 'r', encoding='utf-8') as file:
        saved_settings = safe_load(file)

    os.remove(temp_filename)

    assert saved_settings == settings.settings
