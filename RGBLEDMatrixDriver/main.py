import os
import subprocess
import time
import serial
from serial import Serial
#import spidev   # WARNING: Only available for Linux
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread
import json

import settings


def drawLEDData(logger):
    try:
        pass

    except Exception as ex:
        logger.debug("Exception occured in '{}()': {}".format(threadDrawLEDDate.__name__, ex))


def threadReadDataFromHostCOM(logger, port):
    try:
        with Serial(**settings.HOST_COM_PORT_CONFIG) as ser:
            pass

    except Exception as ex:
        logger.debug("Exception occured in '{}()': {}".format(readLEDDataFromHostForever.__name__, ex))


if __name__ == '__main__':
    try:
        # Get logger ready
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.ERROR)
        handler = RotatingFileHandler(settings.LOG_FILE, maxBytes=settings.MAX_LOG_SIZE, backupCount=0)
        formatter = logging.Formatter(fmt=settings.LOG_FORMAT, datefmt=settings.LOG_DATEFMT)
        handler.setFormatter(formatter)

        # Set high priority for this process by upping its nice value
        os.nice(settings.PROCESS_PRIORITY_NICE_VALUE)

        # IMPORTANT: Load SPI drivers in kernel
        # FIXME: Driver names may be incorrect
        modprobe_returncode = subprocess.run(['/sbin/modprobe', '-a', 'spi_bcm2835', 'spidev']).returncode
        if modprobe_returncode != 0:
            raise Exception("Couldn't load SPI drivers as 'modprobe' returned: {}".format(modprobe_returncode))

        # Read data to draw from host's COM port
        data_thread = Thread(target=threadReadDataFromHostCOM,
                             args=(logger, settings.COM_PORT_TOWARDS_HOST),
                             name=threadReadDataFromHostCOM.__name__,
                             daemon=True)
        data_thread.start()
        if not data_thread.is_alive():
            raise Exception("'{}()' daemon thread failed to start.".format(threadReadDataFromHostCOM.__name__))

        # Read data to show from host COM port
        drawLEDData(logger)

    except KeyboardInterrupt:
        pass

    except Exception as ex:
        logger.error("Unhandled exception caught in main(): {}".format(ex))