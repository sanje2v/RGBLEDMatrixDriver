import time
from copy import copy
import RPi.GPIO as GPIO
from spidev import SpiDev   # WARNING: Only available for Linux

from utils import *


# NOTE: Will run in main thread
def drawLEDDataForever(logger, frames_data_changed_event, frames_data_lock, frames_data):
    spi = None
    try:
        spi = SpiDev()
        spi.open(settings.SPI_BUS, 0)  # NOTE: We are manually controlling SS pins so we just use 0 for device
        spi.max_speed_hz = settings.MAX_SPI_SPEED_HZ
        spi.no_cs = True    # NOTE: We manually control Slave Select (SS) pins

        # NOTE: Make sure pins are in BCM
        GPIO.setmode(GPIO.BCM)

        # Make all the manually chosen Slave Select (SS) pins to OUTPUT mode
        # and also set them to HIGH (used to deselect slave in SPI)
        # except for the first slave select pin
        for i, pin_no in enumerate(settings.SLAVE_SELECT_PIN_NOS):
            GPIO.setup(pin_no, GPIO.OUT)
            GPIO.output(pin_no, (GPIO.LOW if i == 0 else GPIO.HIGH))

        # Save index of currently selected slave above
        selected_slave_id = 0

        # Update with provided frames data
        frame_id, interval_secs, rgbp_frames_data = checkAndUpdateNewFramesData(frames_data_changed_event,
                                                                                frames_data_lock,
                                                                                frames_data,
                                                                                0,
                                                                                0.0,
                                                                                None)
        assert rgbp_frames_data is not None, "BUG: 'frames_data_changed_event' was not set in main.py for first default frame data."

        while(True):    # Do this forever
            while(frame_id < len(rgbp_frames_data)):
                # Send data to each slave
                for slave_id, rgbp_frame_data in enumerate(chunks(rgbp_frames_data[frame_id], settings.NUM_SLAVES)):
                    selected_slave_id = selectSPISlave(slave_id, selected_slave_id)

                    # Send data row by row
                    for col_rgbp_data in chunk(rgbp_frame_data, settings.NUM_ROWS_IN_ONE_SLAVE):
                        spi.writebytes2(col_rgbp_data)
                        spinWait(times=4)

                # Wait until next frame update
                frame_id += 1
                time.sleep(interval_secs)

                # After completing a frame draw, check if new frames data has arrived
                frame_id, interval_secs, rgbp_frames_data = checkAndUpdateNewFramesData(frames_data_changed_event,
                                                                                        frames_data_lock,
                                                                                        frames_data,
                                                                                        frame_id,
                                                                                        interval_secs,
                                                                                        rgbp_frames_data)

            # Start from first frame again
            frame_id = 0

    except Exception as ex:
        raise Exception("Exception occured in '{}()': {}".format(drawLEDDataForever.__name__, ex))

    finally:
        GPIO.cleanup()
        if spi is not None:
            spi.close()


def selectSPISlave(id, selected_slave_id):
    GPIO.output(settings.SLAVE_SELECT_PIN_NOS[selected_slave_id], GPIO.HIGH)    # Deselect currently selected slave
    GPIO.output(settings.SLAVE_SELECT_PIN_NOS[id], GPIO.LOW)                    # Enable new slave

    return id


def checkAndUpdateNewFramesData(frames_data_changed_event,
                                frames_data_lock,
                                frames_data,
                                prev_frame_id,
                                prev_interval_secs,
                                prev_rgbp_frames_data):
    # Check if there is new RGB frames data
    # NOTE: We use data lock so that we don't half update the screens ever
    if frames_data_changed_event.is_set():
        with frames_data_lock:
            frames_data_changed_event.clear()

            # Convert to seconds (float)
            interval_secs = max(frames_data[settings.JSON_DATA_FRAME_INTERVAL_MS_KEY] / 1000.0, settings.JSON_DATA_FRAME_INTERVAL_MAX)
            # For each frame
            for frame_data in frames_data:
                # Read data dictionary into local variables
                rgbp_frames_data = formatRGBFramesDataForEP0075Matrix(frames_data[settings.JSON_DATA_KEY])

            return (0, interval_secs, rgbp_frames_data)

    return (prev_frame_id, prev_interval_secs, prev_rgbp_frames_data)


def formatRGBFramesDataForEP0075Matrix(rgb_frames_data):
    rgbp_frames_data = []

    # For each slave matrix, format RGB data to ~R~G~BP (where P is row position index in BCD starting from 1)
    TOTAL_PRIMARY_COLORS = 3    # Red, Green and Blue
    for rgb_frame_data in rgb_frames_data:
        rgbp_frame_data = []
        for slave_rgb_frame_data in chunks(rgb_frame_data, settings.NUM_SLAVES):
            for row, (r, g, b) in enumerate(zip(slave_rgb_frame_data[0::TOTAL_PRIMARY_COLORS], \
                                                slave_rgb_frame_data[1::TOTAL_PRIMARY_COLORS], \
                                                slave_rgb_frame_data[2::TOTAL_PRIMARY_COLORS])):
                rgbp_frame_data.extend((~r, ~g, ~b, (0x1 << row))) # NOTE: EP0075 wants RGB data inverted

        rgbp_frames_data.append(rgbp_frame_data)

    return rgbp_frames_data