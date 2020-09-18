import os.path
import json
import pygubu
import tkinter as tk
import pyaudio as pya


class settings:
    @staticmethod
    def _get_compatible_audio_devices_with_indices():
        pyaudio = pya.PyAudio()

        audio_devices_with_indices = {}
        for i in range(pyaudio.get_device_count()):
            device_info = pyaudio.get_device_info_by_index(i)
            if str(pyaudio.get_host_api_info_by_index(device_info["hostApi"])["name"]).find("WASAPI") != -1:
                audio_devices_with_indices[device_info["name"]] = device_info["index"]

        pyaudio.terminate()

        return audio_devices_with_indices

    @staticmethod
    def _load_settings_from_file(filename):
        if not os.path.isfile(filename):
            return None

        with open(filename, 'r') as settings_json_file:
            return json.load(settings_json_file)

    @staticmethod
    def _save_settings_to_file(filename, settings_dict):
        with open(filename, 'w') as settings_json_file:
            settings_json_file.write(json.dumps(settings_dict))

    @staticmethod
    def _center_dialog(parent, dialog):
        parent.update()
        x = parent.winfo_rootx()
        y = parent.winfo_rooty()
        x = x + (parent.winfo_width() // 2) - (dialog.toplevel.winfo_reqwidth() // 2)
        y = y + (parent.winfo_height() // 2) - (dialog.toplevel.winfo_reqheight() // 2)
        geometry = '+{0}+{1}'.format(x, y)
        dialog.toplevel.geometry(geometry)

    def __init__(self, path_prefix):
        # Load settings from settings.json file, if available.
        # Else create default file.
        self.settings_file = os.path.join(path_prefix, 'settings.json')
        self.settings_json = settings._load_settings_from_file(self.settings_file)
        self.ui_file = os.path.join(path_prefix, 'dialog.ui')
        
    def show_settings_dialog(self, parent):
        # Load UI
        self.builder = pygubu.Builder()
        self.builder.add_from_file(self.ui_file)
        self.maindialog = self.builder.get_object('dialog', parent)
        self.builder.connect_callbacks(self)
        self.cmb_outputaudiodevices = self.builder.get_object('cmb_outputaudiodevices')
        self.btn_ok = self.builder.get_object('btn_ok')

        # Get all compatible audio devices
        self.cmb_outputaudiodevices['values'] = list(settings._get_compatible_audio_devices_with_indices().keys())
        self.builder.get_variable('cmb_outputaudiodevices_selected').set(self.cmb_outputaudiodevices['values'][0] \
                                                                            if self.settings_json is None else self.settings_json['device_name'])

        # First, center this dialog relative to parent and then show it as modal dialog
        settings._center_dialog(parent, self.maindialog)
        self.maindialog.run()

    def get_selected_audio_device_index(self):
        compatible_audio_devices_with_indices = settings._get_compatible_audio_devices_with_indices()

        if self.settings_json is not None:
            return compatible_audio_devices_with_indices[self.settings_json['device_name']]
        else:
            return compatible_audio_devices_with_indices[list(compatible_audio_devices_with_indices.keys())[0]]
    
    def btn_ok_click(self):
        settings._save_settings_to_file(self.settings_file, 
                                        {'device_name': self.builder.get_variable('cmb_outputaudiodevices_selected').get()})
        self.maindialog.destroy()