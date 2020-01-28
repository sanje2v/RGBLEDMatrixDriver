import os
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

        # Set up controls
        # 1. Wireup scrollbar
        self.sbr_serialoutput.configure(command=self.txt_serialoutput.yview)
        self.txt_serialoutput.configure(yscrollcommand=self.sbr_serialoutput.set)

        # 2. Make 'txt_serialoutput' text control readonly
        self.txt_serialoutput.bind("<Key>", lambda e: "break")

        # Configure variables
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
        self.dispatcher_queue_checker_id = self.mainwindow.after(self.DISPATCHER_QUEUE_CHECK_PERIOD_MS,
                                                                 self.gui_dispatcher)


    def thread_worker_func(self, com_port):
        # TEST ONLY
        FRAME_WRITE_OUT_INDEX = 0
        NUM_DEFAULT_FRAMES = 18
        FRAMES = [0xFF]*(4 * 9 * 96)

        # Add RED
        for i in range(0, (9 * 96), 3):
            FRAMES[i+0] = 0x00  # Red
            FRAMES[i+1] = 0xFF  # Green
            FRAMES[i+2] = 0xFF  # Blue

        # Add GREEN
        for i in range(0, (9 * 96), 3):
            FRAMES[i+0] = 0xFF  # Red
            FRAMES[i+1] = 0x00  # Green
            FRAMES[i+2] = 0xFF  # Blue

        # Add BLUE
        for i in range(0, (9 * 96), 3):
            FRAMES[i+0] = 0xFF  # Red
            FRAMES[i+1] = 0xFF  # Green
            FRAMES[i+2] = 0x00  # Blue

        # This thread:
        # 1. Reads and shows incoming data from slave Arduino.
        # 2. If 'COMPLETED\r\n' message is received from slave, next set of frames are written out.
        try:
            com_port.flushOutput()
            com_port.flushInput()

            while (not self.thread_worker_signal.isSet()):
                if (com_port.in_waiting):
                    message = deepcopy(com_port.read_until(settings.CONTROLLER_MESSAGE_END_SEQUENCE_BYTES)) # NOTE: We 'deepcopy()' 'cause another thread will be accessing this data
                    # NOTE: Tkinter textbox uses '\n' for newline regardless of OS
                    message = message.decode('utf-8')[:-len(settings.CONTROLLER_MESSAGE_END_SEQUENCE_BYTES)] + '\n'
                    self.gui_dispatcher_queue.append(lambda: self.txt_serialoutput.insert(tk.END, message))

                    # See if it is 'COMPLETED' message which means we need to send next set
                    # of frames if all the frames don't in controller's memory.
                    if message == settings.CONTROLLER_LAST_FRAME_MESSAGE:
                        com_port.write(bytearray(FRAMES[FRAME_WRITE_OUT_INDEX:(FRAME_WRITE_OUT_INDEX + (9 * 96 + 1)):])) # CAUTION: Don't forget '+ 1' here
                        FRAME_WRITE_OUT_INDEX = (FRAME_WRITE_OUT_INDEX + (2 * 9 * 96)) % len(FRAMES)

        finally:
            if com_port.is_open:
                com_port.close()


    def btn_connect_click(self):
        self.btn_connect.configure(state='disabled')

        try:
            # Dispatch COM port name for worker thread to communicate
            selected_com_port = self.builder.get_variable('cmb_ports_selected').get()

            self.thread_worker = threading.Thread(target=self.thread_worker_func,
                                                  args=(serial.Serial(port=selected_com_port, **settings.CONTROLLER_COM_PORT_CONFIG),))
            self.thread_worker.start()


        except Exception as ex:
            messagebox.showerror("Error opening port", str(ex))
            self.btn_connect.configure(state='normal')


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
            self.thread_worker.join()


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
