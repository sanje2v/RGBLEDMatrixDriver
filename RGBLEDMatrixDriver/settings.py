import serial

# COM Port settings
CONTROLLER_MESSAGE_END_SEQUENCE_BYTES = b'\r\n'
CONTROLLER_READY_MESSAGE = 'READY'
CONTROLLER_SYNC_MESSAGE = 'SYNC'
CONTROLLER_RESET_COMMAND = b'\x00'*6
CONTROLLER_COM_PORT_CONFIG = \
{
    'baudrate': 57600,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': None,      # Read timeout in secs or None for never timeout
    'write_timeout': None  # In secs
}
