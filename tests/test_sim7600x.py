import pytest
from unittest.mock import MagicMock
from sim7600x import SIM7600X

@pytest.fixture
def mock_serial(mocker):
    mock_serial = mocker.patch('serial.Serial')
    return mock_serial

@pytest.fixture
def sim7600x(mock_serial):
    '''Return a SIM7600X instance.'''
    return SIM7600X()

def test_init(mock_serial):
    '''Test the initialization of the SIM7600X class.'''
    sim7600x = SIM7600X()
    mock_serial.assert_called_with('/dev/ttyUSB2', 115200, timeout=5)
    sim7600x = SIM7600X('/dev/ttyUSB1', 9600, 10)
    mock_serial.assert_called_with('/dev/ttyUSB1', 9600, timeout=10)

def test_send_at_command(mock_serial, sim7600x):
    '''Test sending AT command and getting response.'''
    instance = mock_serial.return_value
    instance.inWaiting.return_value = True
    instance.read.return_value = b'OK\r\n'
    response = sim7600x.send_at_command('AT')
    assert response == 'OK\r\n'

def test_send_at_command_timeout(mock_serial, sim7600x):
    mock_serial.inWaiting.return_value = False
    response = sim7600x.send_at_command('AT', timeout=0.1)
    assert response == ''

# def test_get_signal_quality(mock_serial, sim7600x):
#     instance = mock_serial.return_value
#     instance.inWaiting.return_value = True
#     instance.read.return_value = b'+CSQ: 25,99\r\n'
#     signal_quality = sim7600x.get_signal_quality()
#     assert signal_quality == 20

def test_decode_position():
    '''Test the decoding of a GPS position.'''
    sim7600x = SIM7600X()
    assert sim7600x._SIM7600X__decode_position('5327.0000') == 53.45
    assert sim7600x._SIM7600X__decode_position('0630.2345') == 6.50391
    assert sim7600x._SIM7600X__decode_position('5327.0000', 1) == 53.5
    assert sim7600x._SIM7600X__decode_position('0630.2345', 1) == 6.5
