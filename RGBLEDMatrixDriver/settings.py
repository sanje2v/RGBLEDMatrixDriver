import serial

# COM Port settings
CONTROLLER_MESSAGE_END_SEQUENCE_BYTES = b'\r\n'
CONTROLLER_READY_MESSAGE = 'READY'
CONTROLLER_SYNC_MESSAGE = 'SYNC'
CONTROLLER_COM_PORT_CONFIG = \
{
    'baudrate': 115200,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': None,        # Read timeout in secs or None for never timeout
    'write_timeout': None   # In secs
}

FUNCTIONS_DIRECTORY = 'funcs'
DAEMON_WINDOW_TITLE = 'LED Matrix Controller Daemon Window'