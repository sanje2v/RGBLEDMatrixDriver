import os.path
import struct
import imageio
import psutil
import time
import subprocess
import pynvml as nvml   # Python wrapper around NVIDIA NVML DLL
import numpy as np
from copy import deepcopy

from enums import IntervalEnum


class cpugpu_usage:
    SERVICE_NAME = 'Elevated Information Provider Service'
    CPU_TEMPERATURE_SERVICE_PIPE = r'\\.\pipe\ElevatedInformationProviderService'
    SIZE_OF_FLOAT = 4
    MAX_LINE_LENGTH_PX = 15
    LINE_WIDTH = 3
    CPU_TEXT_COLOR_VALUE = [0xFF]*3
    GPU_TEXT_COLOR_VALUE = [0xFE]*3
    GREEN_COLOR = [0x00, 0xFF, 0x00]
    YELLOW_COLOR = [0xFF, 0xFF, 0x00]
    RED_COLOR = [0xFF, 0x00, 0x00]


    @staticmethod
    def name():
        return 'CPU and GPU usage meter'
    
    def __init__(self, path_prefix):
        # Need to load template image
        self.template = imageio.imread(os.path.join(path_prefix, 'template.bmp'))

        # Start 'Elevated Information Provider Service' and open pipe to it to read CPU core temperature
        # CAUTION: We use 'net.exe' instead of 'sc.exe' because we want to start the service synchronously
        if subprocess.run(['net.exe', 'start', self.SERVICE_NAME]).returncode not in [0, 2]:    # Service must correct start or have already started
            raise RuntimeException(f"Couldn't start '{self.SERVICE_NAME}'!")

        # CAUTION: Need to call usage functions at least once
        #          before calling it in 'get_frame()'
        self.cpu_usage_percent = 0.0
        self.cpu_temperature = 0.0

        self.selected_gpu = None
        self.gpu_usage_percent = 0.0
        self.gpu_temperature = 0.0

    def __enter__(self):
        # CAUTION: Need to call usage functions at least once
        #          before calling it in 'get_frame()'
        self.cpu_usage_percent = psutil.cpu_percent()
        self.cpu_temperature_service_pipe = self._get_service_pipe()
        if not self.cpu_temperature_service_pipe:
            raise Exception("This function needs 'Elevated Information Provider Service' service to be installed!")

        nvml.nvmlInit()  # CAUTION: Must be called before any other nvml functions
        assert nvml.nvmlDeviceGetCount() > 0, "No NVIDIA GPU found."
        self.selected_gpu = nvml.nvmlDeviceGetHandleByIndex(0)
        return self

    def __exit__(self, type, value, traceback):
        if self.cpu_temperature_service_pipe:
            self.cpu_temperature_service_pipe.close()
            subprocess.run(['sc.exe', 'stop', self.SERVICE_NAME])   # NOTE: We use 'sc.exe' here because we want to stop the service asynchronously
        nvml.nvmlShutdown()

    def get_interval(self):
        return IntervalEnum.MSECS_500

    def _get_service_pipe(self):
        try:
            pipe_handle = open(self.CPU_TEMPERATURE_SERVICE_PIPE, mode='rb+', buffering=0) # CAUTION: 'buffering' must be 0 to NOT to have to call 'flush()'

        except:
            pipe_handle = None
        return pipe_handle

    def _get_cpu_temperature(self):
        self.cpu_temperature_service_pipe.write(b'GetCPUPackageTemp')
        return struct.unpack('f', self.cpu_temperature_service_pipe.read(self.SIZE_OF_FLOAT))[0]

    def get_frame(self):
        # Get CPU and GPU usage percentages
        self.cpu_usage_percent = psutil.cpu_percent()
        self.gpu_usage_percent = nvml.nvmlDeviceGetUtilizationRates(self.selected_gpu).gpu

        # Create a deep copy of template to work on
        frame = deepcopy(self.template)

        # Draw progress bar for each usage
        def getUsageLineColor(usage):
            if usage < 30.:
                return self.GREEN_COLOR
            elif usage < 70.:
                return self.YELLOW_COLOR
            else:
                return self.RED_COLOR

        cpu_line_length_px = int(self.cpu_usage_percent / 100. * self.MAX_LINE_LENGTH_PX)
        gpu_line_length_px = int(self.gpu_usage_percent / 100. * self.MAX_LINE_LENGTH_PX)

        frame[1:(cpu_line_length_px + 1), 0:self.LINE_WIDTH, :] = getUsageLineColor(self.cpu_usage_percent)
        frame[18:(gpu_line_length_px + 18), 0:self.LINE_WIDTH, :] = getUsageLineColor(self.gpu_usage_percent)

        # Color CPU and GPU text according to temperature
        def getCPUGPUTextColor(temp):
            if temp < 45.:
                return self.GREEN_COLOR
            elif temp < 74.:
                return self.YELLOW_COLOR
            else:
                return self.RED_COLOR

        self.cpu_temperature = self._get_cpu_temperature()
        self.gpu_temperature = nvml.nvmlDeviceGetTemperature(self.selected_gpu, nvml.NVML_TEMPERATURE_GPU)

        IMAGE_CHANNELS_AXIS = -1 # Last axis
        frame[(frame==self.CPU_TEXT_COLOR_VALUE).all(axis=IMAGE_CHANNELS_AXIS)] = getCPUGPUTextColor(self.cpu_temperature)
        frame[(frame==self.GPU_TEXT_COLOR_VALUE).all(axis=IMAGE_CHANNELS_AXIS)] = getCPUGPUTextColor(self.gpu_temperature)

        return frame.flatten()