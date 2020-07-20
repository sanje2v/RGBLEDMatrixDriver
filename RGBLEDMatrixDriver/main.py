import os
import sys
import time
import serial
import serial.tools.list_ports
import asyncio
import serial_asyncio
import threading
import pygubu
import numpy as np
import tkinter as tk
import tkinter.messagebox as messagebox

from libs.Compressor import Compressor
from funcs.cpugpu_usage import cpugpu_usage
import settings


class Application:
    DISPATCHER_QUEUE_CHECK_PERIOD_MS = 200


    def __init__(self, ports, is_service, params):
        # Create a builder
        self.builder = builder = pygubu.Builder()

        # Load mainwindow ui file and set its icon
        builder.add_from_file(os.path.join('ui', 'mainwindow.ui'))
        self.mainwindow = builder.get_object('mainwindow')
        self.mainwindow.iconbitmap(os.path.join('ui', 'app.ico'))
        self.mainwindow.protocol('WM_DELETE_WINDOW', self.quit)

        # Store references to controls
        self.cmb_ports = builder.get_object('cmb_ports')
        self.btn_connect = builder.get_object('btn_connect')
        self.txt_serialoutput = builder.get_object('txt_serialoutput')
        self.sbr_serialoutput = builder.get_object('sbr_serialoutput')
        self.lbl_status = builder.get_object('lbl_status')
        self.btn_reset = builder.get_object('btn_reset')

        # Set up controls
        # 1. Wireup scrollbar
        self.sbr_serialoutput.configure(command=self.txt_serialoutput.yview)
        self.txt_serialoutput.configure(yscrollcommand=self.sbr_serialoutput.set)

        # 2. Make 'txt_serialoutput' text control readonly
        self.txt_serialoutput.bind("<Key>", lambda e: "break")

        # Configure variables
        self.thread_worker = None
        self.loop = None

        # Configure callbacks
        builder.connect_callbacks(self)

        # Add COM ports to combo box
        self.cmb_ports['values'] = ports

        # Select first COM port
        self.builder.get_variable('cmb_ports_selected').set(ports[0])

        # Prepare dispatcher which is used to dispatch work from worker thread to GUI thread
        self.gui_dispatcher_queue = []
        self.worker_dispatcher_queue = []
        self.dispatcher_queue_checker_id = self.mainwindow.after(self.DISPATCHER_QUEUE_CHECK_PERIOD_MS,
                                                                 self.gui_dispatcher)

    def thread_worker_func(self, port):
        # Utility functions
        def writeToController(self, serialToController, data, flush=False):
            serialToController.write(data)
            if (flush):
                serialToController.flush()

        def writeOutToUI(message, gui_dispatcher_queue=self.gui_dispatcher_queue, txt_serialoutput=self.txt_serialoutput):
            # NOTE: The following should do a deep copy which is needed 'cause
            #       another thread will be accessing this data later
            # NOTE: Tkinter textbox uses '\n' for newline regardless of OS
            message = message + '\n'

            # We push serial data from controller to a queue which will be
            # accessed by GUI thread later to write text safely to GUI text control
            gui_dispatcher_queue.append(lambda: txt_serialoutput.insert(tk.END, message))

            return message

        def sendCommandToControllerIfAny(worker_dispatcher_queue, serialToController):
            while (worker_dispatcher_queue):
                worker_dispatcher_queue.pop(0)(serialToController)

        # TEST ONLY
        #NUM_FRAMES = 20
        #ONE_FRAME_SIZE = 768
        #NUM_COLOR_CHANNELS = 3
        #FRAMES = []
        #COLOR_WHEEL = [[b'\xF9', b'\x01', b'\x01'],
        #               [b'\xF9', b'\xF9', b'\x01'],
        #               [b'\x01', b'\xF9', b'\x01'],
        #               [b'\x01', b'\xF9', b'\xF9'],
        #               [b'\x01', b'\x01', b'\xF9'],
        #               [b'\x01', b'\xF9', b'\xF9'],
        #               [b'\xF9', b'\xF9', b'\xF9']]

        #for i in range(NUM_FRAMES):
        #    COLOR = COLOR_WHEEL[i % len(COLOR_WHEEL)]
        #    FRAMES.append([])

        #    for j in range(0, ONE_FRAME_SIZE, NUM_COLOR_CHANNELS):
        #        for k in range(NUM_COLOR_CHANNELS):
        #            FRAMES[i].append(COLOR[k])

        #for i in range(0, NUM_FRAMES):
        #    FRAMES[i] = b''.join(FRAMES[i])

        #assert len(FRAMES) == NUM_FRAMES and len(FRAMES[0]) == ONE_FRAME_SIZE, "Total bytes in 'FRAMES' must be multiple of one frame size."

        # This thread:
        # 1. Reads and shows incoming data from slave Arduino.
        # 2. If 'COMPLETED' message is received from LED controller, next set of frames are written out.
        try:
            # Start async serial read write
            class ControllerSerialHandler(asyncio.Protocol):
                END_OF_MESSAGE_BYTE = ord('\n')     # In CRLF line ending of a message, LF signifies end-of-message


                def _handle_message(self, message):
                    writeOutToUI(message)

                    if not self.controller_ready and message == settings.CONTROLLER_READY_MESSAGE:
                        # LED controller is now ready after soft reset
                        self.controller_ready = True

                        #self.gui_dispatcher_queue.append(lambda: self.lbl_status.configure(text="Controller ready. Sending frames..."))

                        self.next_frame = compressor.feed(function.get_frame())
                        
                    elif self.controller_ready:
                        if message.startswith('SYNC'):
                            self.transport.write(self.next_frame)
                            self.next_frame = compressor.feed(function.get_frame())

                        elif message.startswith('ERROR'):
                            raise Exception(message)

                def __init__(self, loop, compressor):
                    self.controller_ready = False
                    self.read_buffer = bytearray()
                    self.transport = None

                    self.loop = loop
                    self.compressor = compressor
                    self.next_frame = None

                def get_transport(self):
                    return self.transport

                def connection_made(self, transport):
                    self.transport = transport
                    transport.serial.rts = False

                    transport.serial.set_buffer_size(rx_size=256, tx_size=2048)

                    transport.serial.reset_input_buffer()
                    transport.serial.reset_output_buffer()

                    time.sleep(.1)
                    while transport.serial.in_waiting:
                        transport.serial.read(transport.serial.in_waiting)

                    # Ask controller to reset
                    transport.write(settings.CONTROLLER_RESET_COMMAND)

                def data_received(self, data):
                    for data_byte in data:
                        self.read_buffer.append(data_byte)

                        if data_byte == self.END_OF_MESSAGE_BYTE:
                            message = self.read_buffer.decode('utf-8')[:-len(settings.CONTROLLER_MESSAGE_END_SEQUENCE_BYTES)]
                            self.read_buffer.clear()

                            # Determine the kind of message received and perform actions accordingly
                            self._handle_message(message)

                def connection_lost(self, exc):
                    self.loop.stop()

            
            function = cpugpu_usage()
            frame = None
            compressor = Compressor()

            frame = compressor.feed(function.get_frame())
            for i in range(0, len(frame), 3):
                r = frame[i] & 0x7
                g = frame[i+1] & 0x7
                b = frame[i+2] & 0x7

                assert r != 0 or g != 0 or b != 0, "Bad byte found"

            self.loop = asyncio.new_event_loop()
            controller_serialhandler = ControllerSerialHandler(self.loop, compressor)
            conn = serial_asyncio.create_serial_connection(self.loop,
                                                           lambda: controller_serialhandler,
                                                           port,
                                                           **settings.CONTROLLER_COM_PORT_CONFIG)
            self.loop.run_until_complete(conn)
            self.loop.run_forever()
            if controller_serialhandler.get_transport() is not None:
                  # Ask controller to reset before exit
                controller_serialhandler.get_transport().serial.write(settings.CONTROLLER_RESET_COMMAND)
                controller_serialhandler.get_transport().serial.flush()
            self.loop.close()
            self.loop = None

        except Exception as ex:
            ex_str = str(ex)
            self.gui_dispatcher_queue.append(lambda: self.lbl_status.configure(text=ex_str))


    def btn_connect_click(self):
        self.btn_connect.configure(state='disabled')
        self.btn_reset.configure(state='normal')

        try:
            # Dispatch COM port name for worker thread to communicate
            selected_com_port = self.builder.get_variable('cmb_ports_selected').get()

            self.thread_worker = threading.Thread(target=self.thread_worker_func,
                                                  args=(selected_com_port,))
            self.thread_worker.start()

        except Exception as ex:
            messagebox.showerror("Error opening port", str(ex))
            self.btn_connect.configure(state='normal')


    def btn_reset_click(self):
        self.isControllerReady = False
        self.lbl_status.configure(text="Reset sent. Waiting for ready message from controller.")
        self.worker_dispatcher_queue.append(lambda serialToController: self.writeToController(serialToController, settings.CONTROLLER_RESET_COMMAND))


    def gui_dispatcher(self):
        while(self.gui_dispatcher_queue):
            # Call the earliest function in the queue with GUI thread
            self.gui_dispatcher_queue.pop(0)()

        self.dispatcher_queue_checker_id = self.mainwindow.after(self.DISPATCHER_QUEUE_CHECK_PERIOD_MS, self.gui_dispatcher)


    def quit(self, event=None):
        self.mainwindow.after_cancel(self.dispatcher_queue_checker_id)
        self.mainwindow.destroy()

        if self.loop is not None:
            self.loop.stop()
            self.thread_worker.join(2.0)

    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    com_ports = serial.tools.list_ports.comports()
    if not com_ports:
        print("ERROR: No COM ports were found in your system! Aborted.")
        exit(-1)

    is_service = ('--as-service' in sys.argv) and ('--params' in sys.argv)
    params = None

    app = Application([x.device for x in com_ports], is_service, params)
    app.run()

    exit(0)
