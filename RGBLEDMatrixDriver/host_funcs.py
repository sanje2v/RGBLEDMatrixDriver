from serial import Serial
import json


# NOTE: Will run in separate daemon thread
def threadReadDataFromHostCOMForever(logger, frames_data_changed_event, frames_data_lock, frames_data):
    try:
        with Serial(**settings.HOST_COM_PORT_CONFIG) as ser:
            while(True):
                try:
                    data_bytes = ser.read_until(settings.JSON_DATA_TERMINATOR)[:-1] # CAUTION: Do remove terminating character
                    data_dict = json.loads(data_bytes.decode('utf-8'))
                    assertJSONDataIsValid(data_dict)
                    respondToHost(ser, 'OK')    # Data from host was in correct format, so notify host

                    with frames_data_lock:
                        # CAUTION: Make sure to use '[:]' to modify original dictionary and not reference
                        frames_data[:] = data_dict
                        frames_data_changed_event.set()

                except Exception as ex:
                    error_message = "Continuing with exception occured in '{}()' COM read loop: {}"\
                        .format(threadReadDataFromHostCOMForever.__name__, ex)
                    logger.error(error_message)
                    respondToHost(ser, error_message)   # Also tell the host about the error in their data

    except Exception as ex:
        raise Exception("Exception occured in '{}()': {}".format(threadReadDataFromHostCOMForever.__name__, ex))


def assertJSONDataIsValid(data_dict):
       if not settings.JSON_DATA_TYPE_KEY in data_dict:
          raise Exception("Key '{}' not found in data_dict.".format(settings.JSON_DATA_TYPE_KEY))

       if not settings.JSON_DATA_FRAME_INTERVAL_MS_KEY in data_dict:
          raise Exception("Key '{}' not found in data_dict.".format(settings.JSON_DATA_FRAME_INTERVAL_MS_KEY))

       if not settings.JSON_DATA_KEY in data_dict:
          raise Exception("Key '{}' not found in data_dict.".format(settings.JSON_DATA_KEY))

       if not type(data_dict[settings.JSON_DATA_FRAME_INTERVAL_MS_KEY]) is int:
          raise Exception("Key '{}' is not of 'int' type in data_dict.".format(settings.JSON_DATA_FRAME_INTERVAL_MS_KEY))

       if not data_dict[settings.JSON_DATA_TYPE_KEY] in [settings.JSON_DATA_TYPE_FRAMES, settings.JSON_DATA_TYPE_PROGRAM]:
          raise Exception("The value of '{}' key is not of suppported type.".format(settings.JSON_DATA_TYPE_KEY))

       if not data_dict[settings.JSON_DATA_KEY]:
           raise Exception("Value of key '{}' is empty in data_dict.".format(settings.JSON_DATA_KEY))

       if data_dict[settings.JSON_DATA_TYPE_KEY] == settings.JSON_DATA_TYPE_FRAMES:
           REQUIRED_NUM_OF_RGB_DATA_BYTES = settings.TOTAL_LEDMATRIX_ROWS * TOTAL_PRIMARY_COLORS * settings.NUM_SLAVES
           for i, l in enumerate(data_dict[settings.JSON_DATA_KEY]):
               if not type(l) is list:
                   raise Exception("Items in value of key '{}' is not list of lists in data_dict.".format(settings.JSON_DATA_KEY))

               if len(l) != REQUIRED_NUM_OF_RGB_DATA_BYTES:
                   raise Exception("The RGB data list of index {} of key '{}' does not contain exactly {} number of RGB data in data_dict."\
                       .format(i, settings.JSON_DATA_KEY, REQUIRED_NUM_OF_RGB_DATA_BYTES))

       elif data_dict[settings.JSON_DATA_TYPE_KEY] == settings.JSON_DATA_TYPE_PROGRAM:
           if not type(data_dict[settings.JSON_DATA_KEY]) is str:
                raise Exception("Program in '{}' key is not a string.".format(settings.JSON_DATA_TYPE_PROGRAM))


def respondToHost(ser, message):
    json_data = json.dumps({settings.JSON_DATA_TYPE_KEY: settings.JSON_DATA_TYPE_RESPONSE, settings.JSON_DATA_KEY: message}) + \
                settings.JSON_DATA_TERMINATOR
    ser.write(json_data.encode('utf-8'))