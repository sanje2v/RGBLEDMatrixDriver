import serial

# COM Port settings
CONTROLLER_MESSAGE_END_SEQUENCE_BYTES = b'\r\n'
CONTROLLER_LAST_FRAME_MESSAGE = 'COMPLETED' + CONTROLLER_MESSAGE_END_SEQUENCE_BYTES.decode('utf-8')
CONTROLLER_COM_PORT_CONFIG = \
{
    'baudrate': 115200,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': 5.0,      # Read timeout in secs or None for never timeout
    'write_timeout': 5.0  # In secs
}
