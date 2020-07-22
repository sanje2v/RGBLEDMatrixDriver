import pyaudio as pa
import numpy as np
import matplotlib.pyplot as plt
import imageio
import math
from copy import deepcopy


def readAudioStreamIntoBuffer(stream, frames_per_buffer, sample_size, signed):
    # Read raw bytes from stream
    #print(stream.get_read_available())
    audio_frames = stream.read(frames_per_buffer)
    assert len(audio_frames) > 0, "No audio frame returned"
    
    # Convert it to proper sample size
    NUM_AUDIO_CHANNELS = 2
    output_audio_frames = [0] * (NUM_AUDIO_CHANNELS * frames_per_buffer)
    for i in range(0, len(audio_frames), sample_size):
        output_audio_frames[i//sample_size] = int.from_bytes(audio_frames[i:i+sample_size],
                                                             byteorder='little',
                                                             signed=signed)
    
    return output_audio_frames

def getChannelData(audio_frames, channel):
    assert channel < 2, "'channel' parameter can be either 0 for left or 1 for right channel."
    
    channel_data = [0] * (len(audio_frames) // 2)
    
    for i in range(channel, len(audio_frames), 2):
        channel_data[i//2] = audio_frames[i]
    
    return channel_data

def getFFTAmplitudes(audio_frames, n):
    audio_frames = (np.abs(np.fft.fft(audio_frames, n=n))[0:(n // 2)]) / n
    assert len(audio_frames) == (n // 2), "BUG: 'getFFT()' must return DC and positive frequencies."
    
    return audio_frames

def scaleFFTAmplitudes(fft_amplitudes, max_limit):
    print(np.min(fft_amplitudes))
    print(np.max(fft_amplitudes))
    print()
    #fft_amplitudes = [int(np.fmin(max_limit * math.log(x), 1000.0) * 1) for x in fft_amplitudes]
    #fft_amplitudes = [int(x) for x in fft_amplitudes]
    scaler_func = lambda x: min(max(math.log(x + 0.00001), 0.0) / 10.0 * max_limit, max_limit)
    fft_amplitudes = list(map(lambda x: int(scaler_func(x)), fft_amplitudes))

    return fft_amplitudes
    

FRAME_WIDTH, FRAME_HEIGHT = (8, 32)

pyaudio = pa.PyAudio()
audio_device_index = 8
audio_device_info = pyaudio.get_device_info_by_index(audio_device_index)
format = pa.paInt16
sample_size = pyaudio.get_sample_size(format)
frames_per_buffer = 2**math.ceil(math.log2(FRAME_HEIGHT * 2))
stream = None
try:
    stream = pyaudio.open(format=format,
                            channels=2,
                            rate=int(audio_device_info["defaultSampleRate"]),
                            input=True,
                            frames_per_buffer=frames_per_buffer,
                            input_device_index=audio_device_index,
                            as_loopback=True)
    print(dir(stream))

    audio_frames = readAudioStreamIntoBuffer(stream, frames_per_buffer, sample_size, signed=True)
    #print(audio_frames)

    left_channel_FFTAmp = getFFTAmplitudes(getChannelData(audio_frames, channel=0), n=frames_per_buffer)[:FRAME_HEIGHT]
    left_channel_FFTAmp = scaleFFTAmplitudes(left_channel_FFTAmp, FRAME_WIDTH // 2)
    right_channel_FFTAmp = getFFTAmplitudes(getChannelData(audio_frames, channel=1), n=frames_per_buffer)[:FRAME_HEIGHT]
    right_channel_FFTAmp = scaleFFTAmplitudes(right_channel_FFTAmp, FRAME_WIDTH // 2)
    print()
    print(left_channel_FFTAmp)
    print()
    print(right_channel_FFTAmp)

finally:
    if stream:
        stream.stop_stream()
        stream.close()
    pyaudio.terminate()