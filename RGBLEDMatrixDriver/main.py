import os
import time
import serial
import serial.tools.list_ports
import threading
from copy import deepcopy
import pygubu
import tkinter as tk
import tkinter.messagebox as messagebox

import settings


class Application:
    DISPATCHER_QUEUE_CHECK_PERIOD_MS = 200
    CONTROLLER_RESET_COMMAND = 'RESET\r\n'


    def __init__(self, ports):
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
        self.isControllerInitialized = False
        self.thread_worker = None
        self.thread_worker_signal = threading.Event()

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

    def writeToController(self, serialToController, data):
        serialToController.write(data)

    def thread_worker_func(self, port):
        # Utility function
        def getNextMessageAndWriteOut(serialToController, gui_dispatcher_queue, txt_serialoutput):
            # NOTE: We 'deepcopy()' here 'cause another thread will be accessing this data later
            message = deepcopy(serialToController.read_until(settings.CONTROLLER_MESSAGE_END_SEQUENCE_BYTES)\
                                  .decode('utf-8')[:-len(settings.CONTROLLER_MESSAGE_END_SEQUENCE_BYTES)])
            # We push serial data from controller to a queue which will be accessed by GUI thread later to
            # write text safely to GUI text control.
            # NOTE: Tkinter textbox uses '\n' for newline regardless of OS
            gui_dispatcher_queue.append(lambda: txt_serialoutput.insert(tk.END, message + '\n'))

            return message

        def sendCommandToControllerIfAny(worker_dispatcher_queue, serialToController):
            while (worker_dispatcher_queue):
                worker_dispatcher_queue.pop(0)(serialToController)

        # TEST ONLY
        FRAME_WRITE_OUT_INDEX = 0
        NUM_FRAMES = 12
        ONE_FRAME_SIZE = 96
        NUM_COLORS_PER_DOT = 3
        FRAMES = [b'\xFF']*(NUM_FRAMES * ONE_FRAME_SIZE)

        for i in range(0, NUM_FRAMES):
            for j in range(0, ONE_FRAME_SIZE, NUM_COLORS_PER_DOT):
                if i < 3:
                    FRAMES[i * ONE_FRAME_SIZE + j + 0] = b'\x00'    # Red
                    FRAMES[i * ONE_FRAME_SIZE + j + 2] = b'\xFF'    # Green
                    FRAMES[i * ONE_FRAME_SIZE + j + 1] = b'\xFF'    # Blue
                elif i < 6:
                    FRAMES[i * ONE_FRAME_SIZE + j + 0] = b'\xFF'
                    FRAMES[i * ONE_FRAME_SIZE + j + 2] = b'\x00'
                    FRAMES[i * ONE_FRAME_SIZE + j + 1] = b'\xFF'
                elif i < 9:
                    FRAMES[i * ONE_FRAME_SIZE + j + 0] = b'\xFF'
                    FRAMES[i * ONE_FRAME_SIZE + j + 2] = b'\xFF'
                    FRAMES[i * ONE_FRAME_SIZE + j + 1] = b'\x00'
                else:
                    FRAMES[i * ONE_FRAME_SIZE + j + 0] = b'\xFF'
                    FRAMES[i * ONE_FRAME_SIZE + j + 2] = b'\x00'
                    FRAMES[i * ONE_FRAME_SIZE + j + 1] = b'\x00'

        assert len(FRAMES) % ONE_FRAME_SIZE == 0, "Total bytes in 'FRAMES' must be multiple of one frame size."

        # This thread:
        # 1. Reads and shows incoming data from slave Arduino.
        # 2. If 'COMPLETED' message is received from LED controller, next set of frames are written out.
        try:
            with serial.Serial(port=port, **settings.CONTROLLER_COM_PORT_CONFIG) as serialToController:
                serialToController.reset_input_buffer()
                serialToController.reset_output_buffer()

                # Ask controller to reset
                self.writeToController(serialToController, bytearray(self.CONTROLLER_RESET_COMMAND, 'utf-8'))

                # Set the index in FRAME of next frame
                next_frame_start_position = 0

                while (not self.thread_worker_signal.isSet()):
                    sendCommandToControllerIfAny(self.worker_dispatcher_queue, serialToController);

                    if (serialToController.in_waiting):
                        message = getNextMessageAndWriteOut(serialToController, self.gui_dispatcher_queue, self.txt_serialoutput)

                        if not self.isControllerInitialized and message == settings.CONTROLLER_INITIALIZED_MESSAGE:
                            # LED controller is not initialized
                            self.isControllerInitialized = True

                            self.gui_dispatcher_queue.append(lambda: self.lbl_status.configure(text="Controller initialized. Ready."))
                        
                        elif self.isControllerInitialized and message.startswith('SYNC'):
                            to_send = FRAMES[next_frame_start_position:(next_frame_start_position + ONE_FRAME_SIZE)]
                            assert len(to_send) == ONE_FRAME_SIZE
                            next_frame_start_position = (next_frame_start_position + ONE_FRAME_SIZE) % len(FRAMES)
                            to_send = b''.join(to_send)
                            self.writeToController(serialToController, to_send)
                                
                            hasErrorOccurred = False
                            while (True):
                                message = getNextMessageAndWriteOut(serialToController, self.gui_dispatcher_queue, self.txt_serialoutput)
                                if message.startswith('OK'):
                                    break
                                elif message.startswith('ERROR'):
                                    self.gui_dispatcher_queue.append(lambda: self.lbl_status.configure(text="Error occurred!"))
                                    self.isControllerInitialized = False
                                    hasErrorOccurred = True
                                    break

                                sendCommandToControllerIfAny(self.worker_dispatcher_queue, serialToController);

                            if hasErrorOccurred:
                                break

        except Exception as ex:
            ex_str = "Exception occurred: {}".format(str(ex))
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
        self.isControllerInitialized = False
        self.lbl_status.configure(text="Reset sent. Waiting for initializing message from controller.")
        self.worker_dispatcher_queue.append(lambda serialToController: self.writeToController(serialToController, bytearray(self.CONTROLLER_RESET_COMMAND, 'utf-8')))


    def gui_dispatcher(self):
        while(self.gui_dispatcher_queue):
            # Call the earliest function in the queue with GUI thread
            self.gui_dispatcher_queue.pop(0)()

        self.dispatcher_queue_checker_id = self.mainwindow.after(self.DISPATCHER_QUEUE_CHECK_PERIOD_MS, self.gui_dispatcher)


    def quit(self, event=None):
        self.mainwindow.after_cancel(self.dispatcher_queue_checker_id)
        self.mainwindow.destroy()

        if self.thread_worker:
            self.thread_worker_signal.set()
            self.thread_worker.join(2.0)


    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    com_ports = serial.tools.list_ports.comports()
    if not com_ports:
        print("ERROR: No COM ports were found in your system! Aborted.")
        exit(-1)

    app = Application([x.device for x in com_ports])
    app.run()

    exit(0)
