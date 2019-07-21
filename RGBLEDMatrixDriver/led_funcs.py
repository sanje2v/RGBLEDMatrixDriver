import sys
import time
import traceback
from copy import copy
import RPi.GPIO as GPIO
from spidev import SpiDev   # WARNING: Only available for Linux

import settings
from utils import *


# NOTE: Will run in main thread
def drawLEDDataForever(logger, frames_data_changed_event, frames_data_lock, frames_data):
    spi = None
    try:
        # NOTE: Pin numbers are dependent on the mode set below
        GPIO.setmode(settings.SPI_SLAVE_SELECT_PIN_MODE)

        # Make all the manually chosen Slave Select (SS) pins to OUTPUT mode
        # and also set them to HIGH (used to deselect slave in SPI)
        # NOTE: In the following functions, we pass a whole list of pins.
        GPIO.setup(settings.SLAVE_SELECT_PIN_NOS, GPIO.OUT)
        GPIO.output(settings.SLAVE_SELECT_PIN_NOS, GPIO.HIGH)  # NOTE: SPI HIGH to deselect

        spi = SpiDev()
        spi.open(settings.SPI_BUS, 0)  # NOTE: We are manually controlling SS pins so we just use 0 for device
        spi.max_speed_hz = settings.SPI_MAX_SPEED_HZ
        spi.no_cs = True    # NOTE: We manually control Slave Select (SS) pins

        frame_id = -1       # CAUTION: Needs to be '-1' and not 'None'
        max_frames = None
        interval_secs = None
        data_type = None
        rgbp_frames_data = None
        while(True):    # Do this forever
            # Update with provided frames data
            frame_id, max_frames, interval_secs, data_type, rgbp_frames_data =\
                checkAndUpdateNewFramesData(logger,
                                            frames_data_changed_event,
                                            frames_data_lock,
                                            frames_data,
                                            frame_id,
                                            max_frames,
                                            interval_secs,
                                            data_type,
                                            rgbp_frames_data)

            if frame_id == max_frames:
                frame_id = 0

            # Send data to each slave
            rgbp_frames_data_index = (frame_id if data_type == settings.JSON_DATA_TYPE_FRAMES else 0)
            for slave_id, rgbp_frame_data in enumerate(chunks(rgbp_frames_data[rgbp_frames_data_index],\
                                                                TOTAL_PRIMARY_COLORS * settings.NUM_ROWS_IN_ONE_SLAVE)):
                selectSPISlave(slave_id)    # Select specific slave to make it listen
                spinWait(times=(settings.SPI_ONE_CLOCK_WAIT_SPIN_TIMES * 2))    # Wait two SPI clock cycles

                # Send data row by row
                for col_rgbp_data in chunks(rgbp_frame_data, TOTAL_RGBP_BYTES):
                    spi.writebytes2(col_rgbp_data)
                    spinWait(times=(settings.SPI_ONE_CLOCK_WAIT_SPIN_TIMES * 2))    # Wait two SPI clock cycles

                deselectSPISlave(slave_id)  # Deselect the slave to begin displaying data
                spinWait(times=(settings.SPI_ONE_CLOCK_WAIT_SPIN_TIMES * 2))    # Wait two SPI clock cycles

            # Wait until next frame update
            time.sleep(interval_secs)

    except Exception as ex:
        raise Exception("Exception occurred in '{}()': {}".format(drawLEDDataForever.__name__, traceback.format_exc()))

    finally:
        GPIO.cleanup()
        if spi is not None:
            spi.close()


def selectSPISlave(id):
    GPIO.output(settings.SLAVE_SELECT_PIN_NOS[id], GPIO.LOW)


def deselectSPISlave(id):
    GPIO.output(settings.SLAVE_SELECT_PIN_NOS[id], GPIO.HIGH)


def checkAndUpdateNewFramesData(logger,
                                frames_data_changed_event,
                                frames_data_lock,
                                frames_data,
                                prev_frame_id,
                                prev_max_frames,
                                prev_interval_secs,
                                prev_data_type,
                                prev_rgbp_frames_data):
    global program_state    # May be used to store state by LED program between executions

    # Check if there is new RGB frames data
    # NOTE: We use a mutex so that we don't half updated screens ever
    if frames_data_changed_event.is_set():
        with frames_data_lock:
            frames_data_changed_event.clear()

            # NOTE: Make sure interval given is within range and do convert to seconds (float)
            interval_secs = toSecs(max(frames_data[settings.JSON_DATA_FRAME_INTERVAL_MS_KEY],
                                       settings.JSON_DATA_FRAME_INTERVAL_MS_MAX))

            if frames_data[settings.JSON_DATA_TYPE_KEY] == settings.JSON_DATA_TYPE_FRAMES:
                # Convert RGB to proper format for hardware
                rgb_frames_data = frames_data[settings.JSON_DATA_KEY]
                rgbp_frames_data = formatRGBFramesDataForEP0075Matrix(rgb_frames_data)

                # NOTE: '0' to start from beginning frame index 0
                return (0,
                        len(rgbp_frames_data),
                        interval_secs,
                        settings.JSON_DATA_TYPE_FRAMES,
                        rgbp_frames_data)
            else:
                # New frames data generating program was provided
                # so clear state data from previous program
                prev_frame_id = -1
                program_state = {}

    if frames_data[settings.JSON_DATA_TYPE_KEY] == settings.JSON_DATA_TYPE_PROGRAM:
        # NOTE: The following program has access to 'rgb_frame_data' variable
        # and is expected to populate it
        program = frames_data[settings.JSON_DATA_KEY]
        rgb_frame_data = []
        frame_id = prev_frame_id + 1

        try:
            # Execute the given LED program to calculate next frame
            # NOTE: We restrict access to variables in this program for simple sandboxing.
            local_vars =\
            {
                'state': program_state,
                'frame_id': frame_id,
                'rgb_frame_data': rgb_frame_data
            }
            exec(program,       # Python program as string
                 None,          # Globals
                 local_vars)    # Locals

        except Exception as ex:
            logger.error("An exception occurred while executing host provided program in '{}()': {}"\
                .format(checkAndUpdateNewFramesData.__name__, ex))

            # Turn off all LEDs
            rgb_frame_data = [[ROW_COLOR_OFF_BYTE]*(TOTAL_PRIMARY_COLORS * settings.TOTAL_LEDMATRIX_ROWS)]

        finally:
            rgbp_frames_data = formatRGBFramesDataForEP0075Matrix([rgb_frame_data])

            return (frame_id,
                    sys.maxsize,
                    interval_secs,
                    settings.JSON_DATA_TYPE_PROGRAM,
                    rgbp_frames_data)

    return ((prev_frame_id + 1),
            prev_max_frames,
            prev_interval_secs,
            prev_data_type,
            prev_rgbp_frames_data)


def formatRGBFramesDataForEP0075Matrix(rgb_frames_data):
    rgbp_frames_data = []

    # For each slave matrix, format RGB data to ~R~G~BP (where P is row position index in BCD starting from 1)
    for rgb_frame_data in rgb_frames_data:
        rgbp_frame_data = []
        for slave_rgb_frame_data in chunks(rgb_frame_data, (TOTAL_PRIMARY_COLORS * settings.NUM_ROWS_IN_ONE_SLAVE)):
            for row, (r, g, b) in enumerate(chunks(slave_rgb_frame_data(TOTAL_PRIMARY_COLORS))):
                rgbp_frame_data.extend((~r, ~g, ~b, (0x1 << row))) # NOTE: EP0075 wants RGB data inverted

        rgbp_frames_data.append(rgbp_frame_data)

    return rgbp_frames_data