# Process settings
PROCESS_HIGHPRIORITY_NICE_VALUE = -10

# COM Port settings
import serial
HOST_COM_PORT_CONFIG = \
{
    port: '/dev/ttyAMA1',   # COM port 1
    baudrate: 9600,
    bytesize: serial.EIGHTBITS,
    parity: serial.PARITY_NONE,
    stopbits: serial.STOPBITS_ONE,
    timeout: None    # Read timeout in secs or None for never
}

# SPI Port settings
SPI_BUS = 0
MAX_SPI_SPEED_HZ = 488000
# CAUTION: Slave Select pins below should be pins other than traditional CS0/1 pins
SLAVE_SELECT_PIN_NOS = [10, 11, 12, 13] # Needs to be in order of slaves
NUM_SLAVES = len(SLAVE_SELECT_PIN_NOS)

# JSON Data settings
JSON_DATA_TERMINATOR = '\0'
JSON_DATA_TYPE_KEY = 'type'
JSON_DATA_FRAME_INTERVAL_MS_KEY = 'interval_ms'
JSON_DATA_KEY = 'data'

# LED Matrix settings
TOTAL_LEDMATRIX_ROWS = 24
TOTAL_LEDMATRIX_COLS = 6

# Log settings
LOG_FILE = 'RGBLEDMatrixDriver.log'
LOG_FORMAT = '%(asctime)s;%(levelname)s;%(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
MAX_LOG_SIZE = 2 * 1024    # 2 KB
