import os
import os.path
import sys
import time
import serial
import serial.tools.list_ports
import asyncio
import serial_asyncio
import threading
import importlib
import pkgutil
import pygubu
import win32gui
import win32api
import win32con
import numpy as np
import tkinter as tk
import tkinter.messagebox as messagebox

from libs.Compressor import Compressor
from enums import IntervalEnum
from utils import *
import settings


class Application:
    DISPATCHER_QUEUE_CHECK_PERIOD_MS = 200


    def __init__(self, ports, functions, is_daemon, selected_com_port=None, selected_function=None):
        self.functions = functions
        self.is_daemon = is_daemon

        # Create a builder
        if not is_daemon:
            self.builder = pygubu.Builder()

        # Load mainwindow ui file, if GUI else make a dummy window and set its icon
        if is_daemon:
            self.mainwindow = tk.Tk()
            self.mainwindow.overrideredirect(1)
            self.mainwindow.title(settings.DAEMON_WINDOW_TITLE)
        else:
            self.builder.add_from_file(os.path.join('uis', 'mainwindow.ui'))
            self.mainwindow = self.builder.get_object('mainwindow')
        self.mainwindow.iconbitmap(os.path.join('uis', 'app.ico'))
        self.mainwindow.protocol('WM_DELETE_WINDOW', self.quit)

        if is_daemon:
            self.mainwindow.withdraw()

            self.thread_worker = threading.Thread(target=self.thread_worker_func,
                                                  args=(selected_com_port, getattr(importlib.import_module(selected_function[0]), selected_function[1])))
            self.thread_worker.start()
        else:
            # Store references to controls
            self.cmb_ports = self.builder.get_object('cmb_ports')
            self.btn_connect = self.builder.get_object('btn_connect')
            self.cmb_functions = self.builder.get_object('cmb_functions')
            self.btn_settings = self.builder.get_object('btn_settings')
            self.txt_serialoutput = self.builder.get_object('txt_serialoutput')
            self.sbr_serialoutput = self.builder.get_object('sbr_serialoutput')
            self.lbl_status = self.builder.get_object('lbl_status')

            # Set up controls
            # 1. Wireup scrollbar
            self.sbr_serialoutput.configure(command=self.txt_serialoutput.yview)
            self.txt_serialoutput.configure(yscrollcommand=self.sbr_serialoutput.set)

            # 2. Make 'txt_serialoutput' text control readonly
            self.txt_serialoutput.bind("<Key>", lambda e: "break")

            # Configure variables
            self.thread_worker = None
            self.event_loop = None

            # Configure callbacks
            self.builder.connect_callbacks(self)

            # Add COM ports to combo box
            self.cmb_ports['values'] = ports

            # Select first COM port
            self.builder.get_variable('cmb_ports_selected').set(self.cmb_ports['values'][0])

            # Add function modules to combo box
            self.cmb_functions['values'] = list(functions.keys())

            # Select first function
            self.builder.get_variable('cmb_functions_selected').set(self.cmb_functions['values'][0])

            # Prepare dispatcher which is used to dispatch work from worker thread to GUI thread
            self.gui_dispatcher_queue = []
            self.worker_dispatcher_queue = []
            self.dispatcher_queue_checker_id = self.mainwindow.after(self.DISPATCHER_QUEUE_CHECK_PERIOD_MS,
                                                                     self.gui_dispatcher)

    def thread_worker_func(self, port, function_class):
        # Utility functions
        def writeOutToUI(message):
            # NOTE: The following should do a deep copy which is needed 'cause
            #       another thread will be accessing this data later
            # NOTE: Tkinter textbox uses '\n' for newline regardless of OS
            message = message + '\n'

            # We push serial data from controller to a queue which will be
            # accessed by GUI thread later to write text safely to GUI text control
            self.gui_dispatcher_queue.append(lambda: self.txt_serialoutput.insert(tk.END, message))

            return message

        # This thread:
        # 1. Reads and shows incoming data from slave Arduino.
        # 2. If 'COMPLETED' message is received from LED controller, next set of frames are written out.
        try:
            # Start async serial read write
            class ControllerSerialHandler(asyncio.Protocol):
                END_OF_MESSAGE_BYTE = ord('\n')     # In CRLF line ending of a message, LF signifies end-of-message


                def _handle_message(self, message):
                    if not self.is_daemon:
                        writeOutToUI(message)

                    if not self.controller_ready and message == settings.CONTROLLER_READY_MESSAGE:
                        # LED controller is now ready after soft reset
                        self.controller_ready = True

                        self.next_frame = self.compressor.feed(self.function.get_frame())
                        
                    elif self.controller_ready:
                        if message.startswith('SYNC'):
                            self.transport.write(self.next_frame)
                            self.next_frame = self.compressor.feed(self.function.get_frame())

                        elif message.startswith('ERROR'):
                            raise Exception(message)

                def __init__(self, is_daemon, function, event_loop, compressor):
                    self.controller_ready = False
                    self.read_buffer = bytearray()
                    self.transport = None

                    self.is_daemon = is_daemon
                    self.function = function
                    self.event_loop = event_loop
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
                    transport.write(makeResetCommand(self.function.get_interval()))

                def data_received(self, data):
                    for data_byte in data:
                        self.read_buffer.append(data_byte)

                        if data_byte == self.END_OF_MESSAGE_BYTE:
                            message = self.read_buffer.decode('utf-8')[:-len(settings.CONTROLLER_MESSAGE_END_SEQUENCE_BYTES)]
                            self.read_buffer.clear()

                            # Determine the kind of message received and perform actions accordingly
                            self._handle_message(message)

                def connection_lost(self, exc):
                    self.event_loop.stop()

            with function_class(os.path.join(settings.FUNCTIONS_DIRECTORY, function_class.__name__)) as function:
                self.event_loop = asyncio.new_event_loop()
                controller_serialhandler = ControllerSerialHandler(self.is_daemon, function, self.event_loop, Compressor())
                conn = serial_asyncio.create_serial_connection(self.event_loop,
                                                               lambda: controller_serialhandler,
                                                               port,
                                                               **settings.CONTROLLER_COM_PORT_CONFIG)
                self.event_loop.run_until_complete(conn)
                self.event_loop.run_forever()
                if controller_serialhandler.get_transport() is not None:
                    # Ask controller to reset before exit
                    controller_serialhandler.get_transport().serial.write(makeResetCommand(IntervalEnum.MSECS_1000))
                    controller_serialhandler.get_transport().serial.flush()
                self.event_loop.close()
                self.event_loop = None

        except Exception as ex:
            if not self.is_daemon:
                self.gui_dispatcher_queue.append(lambda: self.lbl_status.configure(text=str(ex)))


    def btn_connect_click(self):
        try:
            # Dispatch COM port name for worker thread to communicate
            selected_com_port = self.builder.get_variable('cmb_ports_selected').get()
            selected_function = self.functions[self.builder.get_variable('cmb_functions_selected').get()]

            self.thread_worker = threading.Thread(target=self.thread_worker_func,
                                                  args=(selected_com_port, getattr(importlib.import_module(selected_function[0]), selected_function[1])))
            self.thread_worker.start()

            self.cmb_ports.configure(state='disabled')
            self.btn_connect.configure(state='disabled')
            self.cmb_functions.configure(state='disabled')
            self.btn_settings.configure(state='disabled')

        except Exception as ex:
            messagebox.showerror("Error opening port '{}'!".format(selected_com_port), str(ex), parent=self.mainwindow)


    def btn_settings_click(self):
        try:
            selected_function = self.functions[self.builder.get_variable('cmb_functions_selected').get()]
            selected_function_settings = getattr(importlib.import_module(selected_function[0] + '.settings'),
                                                 'settings')(os.path.join(settings.FUNCTIONS_DIRECTORY, selected_function[1]))
            selected_function_settings.show_settings_dialog(self.mainwindow.winfo_toplevel())

        except ModuleNotFoundError:
            messagebox.showerror("No settings", "There are no settings available for this function.", parent=self.mainwindow)

        except Exception as ex:
            messagebox.showerror("Error opening settings", str(ex), parent=self.mainwindow)


    def gui_dispatcher(self):
        while(self.gui_dispatcher_queue):
            # Call the earliest function in the queue with GUI thread
            self.gui_dispatcher_queue.pop(0)()

        self.dispatcher_queue_checker_id = self.mainwindow.after(self.DISPATCHER_QUEUE_CHECK_PERIOD_MS, self.gui_dispatcher)


    def quit(self, event=None):
        if not self.is_daemon:
            self.mainwindow.after_cancel(self.dispatcher_queue_checker_id)
        self.mainwindow.destroy()

        if self.event_loop is not None:
            self.event_loop.stop()
            self.thread_worker.join(2.0)

    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    # Determine if we are being asked to kill hidden daemon window
    if '--kill-daemon' in sys.argv:
        hwndDaemonWindow = win32gui.FindWindow(None, settings.DAEMON_WINDOW_TITLE)
        assert hwndDaemonWindow != 0, "Failed to find window"
        win32api.PostMessage(hwndDaemonWindow, win32con.WM_CLOSE, 0x0, 0x0)
        exit(0)

    com_ports = serial.tools.list_ports.comports()
    if not com_ports:
        print("ERROR: No COM ports were found in your system! Aborted.")
        exit(-1)

    # Get a list of functions python packages that are available inside 'FUNCTIONS_DIRECTORY' folder
    functions = list(filter(lambda m: m.ispkg, pkgutil.iter_modules([settings.FUNCTIONS_DIRECTORY])))
    if not functions:
        print("ERROR: No function modules were found in '{}' directory! Aborted.".format(settings.FUNCTIONS_DIRECTORY))
        exit(-1)
    # Store as a list of function full name and tuples of module path with module name
    functions = dict(map(lambda m: (getattr(getattr(importlib.import_module(m.module_finder.path + '.' + m.name), m.name), 'name')(), \
                                    [m.module_finder.path + '.' + m.name, m.name]), functions))

    # Determine if we are to run as daemon or GUI program
    is_daemon = '--as-daemon' in sys.argv and len(sys.argv) == 4
    selected_com_port = sys.argv[2] if is_daemon else None
    selected_function = functions[sys.argv[3]] if is_daemon else None

    app = Application([x.device for x in com_ports], functions, is_daemon, selected_com_port, selected_function)
    app.run()

    exit(0)
