import pyaudio
from pyaudio import PyAudio
import numpy as np
from copy import deepcopy


class music_visualizer:
    FRAME_WIDTH, FRAME_HEIGHT = (8, 32)
    NUM_COLOR_CHANNELS = 3
    NUM_AUDIO_FRAMES_PER_BUFFER = 512


    def __init__(self, audio_device_index):
        self.template = np.zeros((self.FRAME_WIDTH, self.FRAME_HEIGHT, self.NUM_COLOR_CHANNELS),
                                 dtype=np.uint8)
        self.pyaudio = PyAudio()

        self.audio_device_info = self.pyaudio.get_device_info_by_index(audio_device_index)
        self.stream = self.pyaudio.open(format=pyaudio.paInt16,
                                        channels=min(2, self.audio_device_info['maxOutputChannels']),
                                        rate=int(self.audio_device_info["defaultSampleRate"]),
                                        input=True,
                                        frames_per_buffer=self.NUM_AUDIO_FRAMES_PER_BUFFER,
                                        input_device_index=audio_device_index,
                                        as_loopback=True)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio.terminate()

    def get_frame(self):
        # Create a deep copy of template to work on
        frame = deepcopy(self.template)

        audio_data = self.stream.read(self.stream.get_read_available())
        audio_data_fft = np.abs(np.fft(audio_data, n=self.FRAME_HEIGHT))

        return frame