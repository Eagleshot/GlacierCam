from sim7600x import SIM7600X

def test_decode_position():
    '''Test the decoding of a GPS position.'''
    sim7600x = SIM7600X()
    assert sim7600x._SIM7600X__decode_position('5327.0000') == 53.45
    assert sim7600x._SIM7600X__decode_position('0630.2345') == 6.50391
    assert sim7600x._SIM7600X__decode_position('5327.0000', 1) == 53.5
    assert sim7600x._SIM7600X__decode_position('0630.2345', 1) == 6.5
