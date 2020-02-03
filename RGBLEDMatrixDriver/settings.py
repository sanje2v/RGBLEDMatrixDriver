import serial

# COM Port settings
CONTROLLER_MESSAGE_END_SEQUENCE_BYTES = b'\r\n'
CONTROLLER_INITIALIZED_MESSAGE = 'INITIALIZED'
CONTROLLER_LAST_FRAME_MESSAGE = 'COMPLETED'
CONTROLLER_COM_PORT_CONFIG = \
{
    'baudrate': 57600,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': None,      # Read timeout in secs or None for never timeout
    'write_timeout': None  # In secs
}
