import serial

# COM Port settings
CONTROLLER_MESSAGE_END_SEQUENCE = '\r\n'
CONTROLLER_LAST_FRAME_MESSAGE = 'COMPLETED' + CONTROLLER_MESSAGE_END_SEQUENCE
CONTROLLER_COM_PORT_CONFIG = \
{
    'baudrate': 112500,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': None,      # Read timeout in secs or None for never timeout
    'write_timeout': 5.0  # In secs
}
