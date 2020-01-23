import os
import serial
import serial.tools.list_ports
import threading
import pygubu
import tkinter as tk
import tkinter.messagebox as messagebox

import settings


class Application:
    def __init__(self, ports):
        # Create a builder
        self.builder = builder = pygubu.Builder()

        # Load mainwindow ui file and set its icon
        builder.add_from_file(os.path.join('ui', 'mainwindow.ui'))
        self.mainwindow = builder.get_object('mainwindow')
        self.mainwindow.iconbitmap(os.path.join('ui', 'app.ico'))

        # Store references to controls
        self.cmb_ports = builder.get_object('cmb_ports')
        self.btn_connect = builder.get_object('btn_connect')
        self.txt_serialoutput = builder.get_object('txt_serialoutput')

        # Configure variables
        self.thread_worker = None
        self.thread_worker_signal = threading.Event()

        # Configure callbacks
        builder.connect_callbacks(self)

        # Add COM ports to combo box
        self.cmb_ports['values'] = ports

        # Select first COM port
        self.builder.get_variable('cmb_ports_selected').set(ports[0])


    def thread_worker_func(self, com_port):
        # This thread:
        # 1. Reads and shows incoming data from slave Arduino.
        # 2. If 'COMPLETED\r\n' message is received from slave, next set of frames are written out.
        try:
            while (not self.thread_worker_signal.isSet()):
                if (com_port.in_waiting):
                    message = com_port.read_until(settings.CONTROLLER_MESSAGE_END_SEQUENCE).decode('utf-8')
                    self.txt_serialoutput.insert(tk.END, message)

                    # See if it is 'COMPLETED' message which means we need to send next set 
                    # of frames if all the frames don't in controller's memory.
                    if message == CONTROLLER_LAST_FRAME_MESSAGE:
                        #

        finally:
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


    def quit(self, event=None):
        self.mainwindow.quit()

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

    app = Application(list(map(lambda x: x.device, com_ports)))
    app.run()

    exit(0)
