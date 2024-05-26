from os import path, remove
from io import BytesIO
import logging
from yaml import safe_load, safe_dump

class Data:
    '''Class to handle diagnostics and sensor data storage and retrieval.'''
    def __init__(self, diagnostics_filepath="diagnostics.yaml"):
        self.diagnostics_filepath = diagnostics_filepath
        self.diagnostics = [{}]

    def add(self, key, value):
        '''Add a data point to the current diagnostics dictionary.'''
        self.diagnostics[-1][key] = value

    def load_diagnostics(self):
        '''Load the diagnostics dictionary from a local file.'''
        try:
            if path.exists(self.diagnostics_filepath):
                with open(self.diagnostics_filepath, 'r', encoding='utf-8') as yaml_file:
                    self.diagnostics = safe_load(yaml_file) + self.diagnostics
                remove(self.diagnostics_filepath) # Delete the file after loading
        except Exception as e:
            logging.warning("Could not open diagnostics file: %s", str(e))

    def save_diagnostics(self):
        '''Save the current diagnostics dictionary to a local file.'''
        with open(self.diagnostics_filepath, 'w', encoding='utf-8') as yaml_file:
            safe_dump(self.diagnostics, yaml_file)

    def append_diagnostics_to_file(self):
        '''Append the diagnostics to a local file.'''
        with open(self.diagnostics_filepath, 'a', encoding='utf-8') as yaml_file:
            safe_dump(self.diagnostics, yaml_file, encoding='utf-8')

    def get_data_as_bytes(self):
        '''Return the current diagnostics dictionary as bytes.'''
        data_string = safe_dump(self.diagnostics, default_flow_style=False)
        return BytesIO(data_string.encode('utf-8'))
