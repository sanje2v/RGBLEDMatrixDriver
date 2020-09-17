import pyaudio
from pyaudio import PyAudio
import numpy as np
import math
from copy import copy, deepcopy

from enums import IntervalEnum


class music_visualizer:
    FRAME_WIDTH, FRAME_HEIGHT = (8, 32)
    NUM_COLOR_CHANNELS = 3
    NUM_AUDIO_CHANNELS = 2
    NUM_AUDIO_FRAMES_PER_BUFFER = 128 # This value is a power of 2 (optimal for FFT) and good for 44.1-96 kHz sampling rates
    # NOTE: Thanks to 'http://www.perbang.dk/rgbgradient/' for HSV gradient wheel color generation
    #       Start color: FF293B, End Color: 01156A
    COLOR_GRADIENT_WHEEL = \
        ['800000', '810F00', '832000', '843100', '864200', '885300', '896500', '8B7800',
         '8D8A00', '7F8E00', '6F9000', '5E9200', '4D9300', '3C9500', '2A9700', '179800',
         '059A00', '009B0D', '009D21', '009F35', '00A049', '00A25E', '00A473', '00A589',
         '00A79F', '009CA9', '0089AA', '0075AC', '0061AE', '004CAF', '0037B1', '0021B2']
        #['FF283B', 'FA2F27', 'F54725', 'F05F23', 'EB7521', 'E68B1F', 'E2A11D', 'DDB51C',
        # 'D8C91A', 'CBD318', 'AFCE17', '94CA15', '7AC514', '61C012', '48BB11', '31B610',
        # '1AB20E', '0DAD15', '0CA827', '0BA339', '0A9E49', '089A59', '079567', '079075',
        # '068B82', '057F86', '046B82', '03577D', '024578', '023473', '01246E', '00146A']


    @staticmethod
    def name():
        return 'Music visualizer'
    
    def _readRawAudioDataIntoAudioChannelFrames(self, audio_frames, frames_per_buffer, sample_size, signed):
        # Convert it to proper sample size
        left_audio_frames = [0] * frames_per_buffer
        right_audio_frames = [0] * frames_per_buffer

        for i in range(0, len(audio_frames), sample_size):
            frame_channel_data = int.from_bytes(audio_frames[i:(i+sample_size)],
                                                byteorder='little',
                                                signed=signed)

            j = (i // sample_size)
            if j % 2 == 0:
                left_audio_frames[j // self.NUM_AUDIO_CHANNELS] = frame_channel_data
            else:
                right_audio_frames[j // self.NUM_AUDIO_CHANNELS] = frame_channel_data
    
        return left_audio_frames, right_audio_frames

    def _getFFTAmplitudes(self, audio_frames):
        audio_frames = (np.abs(np.fft.fft(audio_frames)[:self.FRAME_HEIGHT])) / len(audio_frames)
        assert len(audio_frames) == self.FRAME_HEIGHT, "BUG: 'getFFT()' must return DC and positive frequencies."
    
        return audio_frames

    def _scaleFFTAmplitudes(self, fft_amplitudes, max_limit):
        # NOTE: Here we log rescale the FFTs amplitudes such that it looks good. Nothing fancy about this algorithm.
        MIN_LOG_BOUND = 1.2
        MAGIC_NUMBER = 10.0
        scaler_func = lambda x: min(max(math.log(x + 0.00001) - MIN_LOG_BOUND, 0.0) / MAGIC_NUMBER * max_limit, max_limit)
        fft_amplitudes = list(map(lambda x: int(scaler_func(x)), fft_amplitudes))

        assert all((x >= 0 and x <= max_limit) for x in fft_amplitudes), "FFT Amplitude scaling is buggy."

        return fft_amplitudes


    def __init__(self, audio_device_index):
        assert len(self.COLOR_GRADIENT_WHEEL) == self.FRAME_HEIGHT, \
            "Need exactly {} colors in 'COLOR_GRADIENT_WHEEL'".format(self.FRAME_HEIGHT)
        # Convert hex string (for easy programmer modification) to bytearrays in 'COLOR_GRADIENT_WHEEL'
        for i, color_str in enumerate(self.COLOR_GRADIENT_WHEEL):
            self.COLOR_GRADIENT_WHEEL[i] = np.frombuffer(bytes.fromhex(color_str), dtype=np.uint8)

        self.template = np.zeros((self.FRAME_HEIGHT, self.FRAME_WIDTH, self.NUM_COLOR_CHANNELS),
                                 dtype=np.uint8)
        self.pyaudio = PyAudio()
        self.audio_device_info = self.pyaudio.get_device_info_by_index(audio_device_index)
        if self.audio_device_info['maxOutputChannels'] < self.NUM_AUDIO_CHANNELS:
            raise Exception("Audio output device should be at least stereo.")

        self.format = pyaudio.paInt16
        self.sample_size = pyaudio.get_sample_size(self.format)
        self.stream = None
        self.raw_audio_frames = b'\x00' * (self.NUM_AUDIO_CHANNELS * self.NUM_AUDIO_FRAMES_PER_BUFFER * self.sample_size)

    def __enter__(self):
        def audiodata_arrived(data, frame_count, time_info, status):
            self.raw_audio_frames = data
            return (data, pyaudio.paContinue)

        self.stream = self.pyaudio.open(format=self.format,
                                        channels=self.NUM_AUDIO_CHANNELS,
                                        rate=int(self.audio_device_info['defaultSampleRate']),
                                        input=True,
                                        frames_per_buffer=self.NUM_AUDIO_FRAMES_PER_BUFFER,
                                        input_device_index=self.audio_device_info['index'],
                                        stream_callback=audiodata_arrived,
                                        as_loopback=True)
        return self

    def __exit__(self, type, value, traceback):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio.terminate()

    def get_interval(self):
        return IntervalEnum.MSECS_100

    def get_frame(self):
        left_audio_frames, right_audio_frames = self._readRawAudioDataIntoAudioChannelFrames(copy(self.raw_audio_frames),
                                                                                             self.NUM_AUDIO_FRAMES_PER_BUFFER,
                                                                                             self.sample_size,
                                                                                             True)

        # Get FFT Amplitudes of each channel and rescale them from 0 to 'FRAME_WIDTH'
        left_channel_FFTAmp = self._getFFTAmplitudes(left_audio_frames)
        left_channel_FFTAmp = self._scaleFFTAmplitudes(left_channel_FFTAmp, self.FRAME_WIDTH)
        right_channel_FFTAmp = self._getFFTAmplitudes(right_audio_frames)
        right_channel_FFTAmp = self._scaleFFTAmplitudes(right_channel_FFTAmp, self.FRAME_WIDTH)

        # Create a deep copy of template to work on
        frame = deepcopy(self.template)

        # Draw rescaled amplitude bars on to 'frame'
        for i in range(self.FRAME_HEIGHT):
            # For left channel
            FFTAmp = left_channel_FFTAmp[i]
            if FFTAmp > 0:
                frame[i, 0:FFTAmp, :] = self.COLOR_GRADIENT_WHEEL[i]

            # For right channel
            FFTAmp = right_channel_FFTAmp[i]
            if FFTAmp > 0:
                frame[-(i+1), -1:-(FFTAmp+1):-1, :] = self.COLOR_GRADIENT_WHEEL[i]

        return frame.flatten()