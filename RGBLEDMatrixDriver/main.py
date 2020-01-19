import os
import serial
import serial.tools.list_ports
import pygubu
import tkinter as tk
import tkinter.messagebox as messagebox


class Application:
    def __init__(self, master):

        #1: Create a builder
        self.builder = builder = pygubu.Builder()

        #2: Load an ui file
        builder.add_from_file('mainwindow.ui')

        #3: Create the widget using a master as parent
        self.mainwindow = builder.get_object('mainwindow', master)


if __name__ == '__main__':
    com_ports = serial.tools.list_ports.comports()
    #if not com_ports:
    #    messagebox.showerror("No COM ports were found in your system!")
    #    exit(-1)

    root = tk.Tk()
    app = Application(root)
    root.mainloop()
