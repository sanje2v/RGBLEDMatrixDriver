import os.path
import imageio
import psutil
import pynvml as nvml   # Python wrapper around NVIDIA NVML DLL
import numpy as np
from copy import deepcopy

from enums import IntervalEnum


class cpugpu_usage:
    MAX_LINE_LENGTH_PX = 15
    LINE_WIDTH = 3
    CPU_TEXT_COLOR_VALUE = [255]*3
    GPU_TEXT_COLOR_VALUE = [254]*3
    GREEN_COLOR = [0x00, 0xFF, 0x00]
    YELLOW_COLOR = [0xFF, 0xFF, 0x00]
    RED_COLOR = [0xFF, 0x00, 0x00]


    @staticmethod
    def name():
        return 'CPU and GPU usage meter'
    
    def __init__(self, path_prefix):
        # Need to load template image
        self.template = imageio.imread(os.path.join(path_prefix, 'template.bmp'))

        # CAUTION: Need to call usage functions at least once
        #          before calling it in 'get_frame()'
        self.cpu_usage_percent = psutil.cpu_percent()
        self.cpu_temperature = 0.0

        nvml.nvmlInit()  # CAUTION: Must be called before any other nvml functions
        assert nvml.nvmlDeviceGetCount() > 0, "No NVIDIA GPU found."
        self.selected_gpu = nvml.nvmlDeviceGetHandleByIndex(0)
        self.gpu_usage_percent = nvml.nvmlDeviceGetUtilizationRates(self.selected_gpu).gpu
        self.gpu_temperature = nvml.nvmlDeviceGetTemperature(self.selected_gpu, nvml.NVML_TEMPERATURE_GPU)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        nvml.nvmlShutdown()

    def get_interval(self):
        return IntervalEnum.MSECS_500

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
            if temp < 40.:
                return self.GREEN_COLOR
            elif temp < 70.:
                return self.YELLOW_COLOR
            else:
                return self.RED_COLOR

        self.cpu_temperature = 0.0
        self.gpu_temperature = nvml.nvmlDeviceGetTemperature(self.selected_gpu, nvml.NVML_TEMPERATURE_GPU)

        IMAGE_CHANNEL_AXIS = -1 # Last axis
        frame[(frame==self.GPU_TEXT_COLOR_VALUE).all(axis=IMAGE_CHANNEL_AXIS)] = getCPUGPUTextColor(self.gpu_temperature)

        return frame.flatten()