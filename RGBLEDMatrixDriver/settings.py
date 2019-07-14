# Process settings
PROCESS_PRIORITY_NICE_VALUE = -10

# COM Port settings
import serial
HOST_COM_PORT_CONFIG = \
{
    port: '/dev/ttyAMA1',   # COM port 1
    baudrate: 9600,
    bytesize: serial.EIGHTBITS,
    parity: serial.PARITY_NONE,
    stopbits: serial.STOPBITS_ONE,
    timeout: 5.0    # Read timeout in secs
}

# Log settings
LOG_FILE = 'RGBLEDMatrixDriver.log'
LOG_FORMAT = '%(asctime)s;%(levelname)s;%(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
MAX_LOG_SIZE = 2 * 1024    # 2 KB
