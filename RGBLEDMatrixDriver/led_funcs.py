import time
from copy import copy
import RPi.GPIO as GPIO
from spidev import SpiDev   # WARNING: Only available for Linux


# NOTE: Will run in main thread
def drawLEDDataForever(logger, data_lock, data):
    spi = None
    try:
        spi = SpiDev()
        spi.open(settings.SPI_BUS, 0)  # NOTE: We are manually controlling SS pins so we just use 0 for device
        spi.max_speed_hz = settings.MAX_SPI_SPEED_HZ
        spi.no_cs = True    # NOTE: We manually control Chip Select pins

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

        while(True):
            


            for slave_id in range(settings.NUM_SLAVES):
                selected_slave_id = selectSPISlave(slave_id, selected_slave_id)

                data_start_offset = slave_id * len(data) / settings.NUM_SLAVES
                data_end_offset = data_start_offset + len(data) / settings.NUM_SLAVES

                spi.writebytes2(data[data_start_offset:data_end_offset])

            # Wait until next frame update
            time.sleep(wait_period_ms)

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
