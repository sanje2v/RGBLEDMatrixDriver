from serial import Serial


# NOTE: Will run in separate daemon thread
def threadReadDataFromHostCOMForever(logger, port, data_changed_event, data_lock, data):
    try:
        with Serial(**settings.HOST_COM_PORT_CONFIG) as ser:
            while(True):
                try:
                    data_bytes = ser.read_until(settings.JSON_DATA_TERMINATOR)[:-1] # CAUTION: Do remove terminating charater
                    with data_lock:
                        data[:] = json.loads(data_bytes.decode('utf-8'))    # CAUTION: Make sure to use '[:]' to modify original dictionary
                        data_changed_event.set()

                except Exception as ex:
                    logger.error("Continuing with exception occured in '{}()' COM read loop: {}".format(readLEDDataFromHostForever.__name__, ex))

    except Exception as ex:
        raise Exception("Exception occured in '{}()': {}".format(threadReadDataFromHostCOMForever.__name__, ex))
