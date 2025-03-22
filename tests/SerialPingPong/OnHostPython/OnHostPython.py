import serial
import time

PORT = 'COM5'
CONTROLLER_COM_PORT_CONFIG = \
{
    'baudrate': 115200,#57600,
    'bytesize': serial.EIGHTBITS,
    'parity': serial.PARITY_NONE,
    'stopbits': serial.STOPBITS_ONE,
    'timeout': None,      # Read timeout in secs or None for never timeout
    'write_timeout': None  # In secs
}

try:
    with serial.Serial(port=PORT, **CONTROLLER_COM_PORT_CONFIG) as serialToController:
        serialToController.set_buffer_size(rx_size=1024, tx_size=1024)

        serialToController.reset_input_buffer()
        serialToController.reset_output_buffer()

        time.sleep(1)
        while serialToController.in_waiting:
            serialToController.read()
            time.sleep(.1)

        DATA = []
        for j in range(3):
            for i in range(0xFF+1):
                DATA.append(i)

        DATA = bytearray(DATA)

        #bytesWritten = serialToController.write('READY\n'.encode('utf-8'))
        #assert bytesWritten == 6, "Not all READY message was written."

        i = 0
        while(True):
            #message = serialToController.read_until('\r\n'.encode('utf-8'))
            #message = message.decode('utf-8')[:-len('\r\n')]
            #while (message != 'READY'):
            #    print(message)
            #    message = serialToController.read_until('\r\n'.encode('utf-8')).decode('utf-8')[:-len('\r\n')]

            serialToController.write(DATA)

            check_index = 0
            while(check_index < len(DATA)):
                in_data = int.from_bytes(serialToController.read(), "little")

                assert (check_index % (0xFF+1)) < len(DATA), "Out of index: {}".format((check_index % (0xFF+1)))
                if (in_data != DATA[(check_index % (0xFF+1))]):
                    raise ValueError("Check failed at index: {0}, wanted {1} but was {2}.".format(check_index, DATA[(check_index % (0xFF+1))], in_data))

                check_index += 1;

            print("Looks good: {}".format(i))
            i = ((i + 1) % 1000)

except KeyboardInterrupt:
    pass