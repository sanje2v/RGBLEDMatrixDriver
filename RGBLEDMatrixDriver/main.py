import os
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread, Lock, Event
import json

import settings
from utils import *
from host_funcs import threadReadDataFromHostCOMForever
from led_funcs import drawLEDDataForever


if __name__ == '__main__':
    try:
        # Get logger ready
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.ERROR)
        handler = RotatingFileHandler(settings.LOG_FILE, maxBytes=settings.MAX_LOG_SIZE, backupCount=0)
        formatter = logging.Formatter(fmt=settings.LOG_FORMAT, datefmt=settings.LOG_DATEFMT)
        handler.setFormatter(formatter)

        # Set high priority for this process by upping its nice value
        os.nice(settings.PROCESS_HIGHPRIORITY_NICE_VALUE)

        # IMPORTANT: Load SPI drivers in kernel
        modload_returncode = subprocess.run(['/sbin/modprobe', '-a', 'spi-bcm2835', 'spidev']).returncode
        if modload_returncode != 0:
            raise Exception("Couldn't load SPI drivers as 'modprobe' returned: {}".format(modload_returncode))

        # Create a mutex to lock access to data and an event object to notify it has changed
        frames_data_lock = Lock()
        frames_data_changed_event = Event()

        # Load a default data of all white
        ROW_ALL_LED_ON_BYTE = 0xFF  # Turn all LEDs white
        frames_data = \
        {
            'interval_ms': 500,
            'data': [[ROW_ALL_LED_ON_BYTE]*(TOTAL_PRIMARY_COLORS * settings.TOTAL_LEDMATRIX_ROWS)]
        }
        frames_data_changed_event.set()    # CAUTION: Don't forget to set this as we have just changed 'frames_data'

        # Read data to draw from host's COM port
        data_thread = Thread(target=threadReadDataFromHostCOMForever,
                             args=(logger, \
                                   settings.COM_PORT_TOWARDS_HOST, \
                                   frames_data_changed_event, \
                                   frames_data_lock, \
                                   frames_data),
                             name=threadReadDataFromHostCOMForever.__name__,
                             daemon=True)
        data_thread.start()
        if not data_thread.is_alive():
            raise Exception("'{}()' daemon thread failed to start.".format(threadReadDataFromHostCOMForever.__name__))

        # Read data to show from host COM port, forever
        drawLEDDataForever(logger, frames_data_changed_event, frames_data_lock, frames_data)

    except KeyboardInterrupt:
        exit(0)

    except Exception as ex:
        logger.error("Unhandled exception caught in main(): {}".format(ex))
        exit(-1)