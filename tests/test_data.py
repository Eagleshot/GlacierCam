import os
from sys import path
from io import BytesIO
path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import Data
import fileserver as fs
import streamlit as st

def test_init():
    """Test the initialization of the Data class."""
    data = Data()
    assert data.diagnostics == [{}]

def test_add():
    """Test adding a data point to the diagnostics dictionary."""
    data = Data()
    data.add("temperature", 25)
    data.add("humidity", 50)
    assert data.diagnostics == [{"temperature": 25, "humidity": 50}]

def test_load_diagnostics():
    """Test loading a diagnostics file."""
    temp_filename = "test_diagnostics.yaml"
    data = Data(temp_filename)
    data.add("temperature", 25)
    data.add("humidity", 50)
    data.save_diagnostics()
    data.add("temperature", 3)
    data.append_diagnostics_to_file()
    
    new_data = Data(temp_filename)
    new_data.load_diagnostics()
    assert not os.path.exists(temp_filename)
    assert new_data.diagnostics == [{'humidity': 50, 'temperature': 25}, {'humidity': 50, 'temperature': 3}, {}]

def test_load_diagnostics_file_not_found():
    """Test loading a diagnostics file that does not exist."""
    data = Data("non_existent.yaml")
    data.load_diagnostics()
    assert data.diagnostics == [{}]

def test_load_empty_diagnostics():
    """Test loading an empty diagnostics from a file."""
    temp_filename = "test_diagnostics.yaml"
    with open(temp_filename, 'w', encoding='utf-8') as file:
        file.write("")

    data = Data(temp_filename)
    data.load_diagnostics()
    assert data.diagnostics == [{}]

def test_save_diagnostics():
    """Test saving the diagnostics dictionary to a file."""
    data = Data("test_diagnostics.yaml")
    data.add("temperature", 25)
    data.add("humidity", 50)
    data.save_diagnostics()
    assert os.path.exists("test_diagnostics.yaml")

    data2 = Data("test_diagnostics.yaml")
    data2.load_diagnostics() # Also removes the file
    data2.add("temperature", 3)
    assert data2.diagnostics == [{'humidity': 50, 'temperature': 25}, {'temperature': 3}]

def test_append_diagnostics_to_file():
    """Test appending the diagnostics to a file."""
    temp_filename = "test_diagnostics.yaml"
    data = Data(temp_filename)
    data.add("string", "test")
    data.save_diagnostics()

    data2 = Data(temp_filename)
    data2.add("temperature", 25)
    data2.append_diagnostics_to_file()

    new_data = Data(temp_filename)
    new_data.load_diagnostics()
    assert new_data.diagnostics == [{'string': 'test'}, {'temperature': 25}, {}]

def test_get_data_as_bytes():
    """Test getting the diagnostics dictionary as bytes."""
    temp_filename = "test_diagnostics.yaml"
    data = Data(temp_filename)
    data.add("temperature", 25)
    data.add("humidity", 50)
    data.save_diagnostics()
    data.append_diagnostics_to_file()
    data.load_diagnostics()
    bytes_data = data.get_data_as_bytes()
    assert isinstance(bytes_data, BytesIO)

    # TODO
    # FTP_HOST = st.secrets["FTP_HOST"]
    # FTP_USERNAME = st.secrets["FTP_USERNAME"]
    # FTP_PASSWORD = st.secrets["FTP_PASSWORD"]
    # FTP_FOLDER = st.secrets["FTP_FOLDER"]

    # file_server = fs.FileServer(FTP_HOST, FTP_USERNAME, FTP_PASSWORD)
    # file_server.change_directory(FTP_FOLDER[0])
    # file_server.append_file_from_bytes(temp_filename, bytes_data)
