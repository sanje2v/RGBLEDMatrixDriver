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


    @staticmethod
    def name():
        return 'CPU and GPU usage meter'
    
    def __init__(self, path_prefix):
        # Need to load template image
        self.template = imageio.imread(os.path.join(path_prefix, 'template.bmp'))

        # CAUTION: Need to call usage functions at least once
        #          before calling it in 'get_frame()'
        self.cpu_usage_percent = psutil.cpu_percent()

        nvml.nvmlInit()  # CAUTION: Must be called before any other nvml functions
        self.selected_gpu = nvml.nvmlDeviceGetHandleByIndex(0)
        self.gpu_usage_percent = nvml.nvmlDeviceGetUtilizationRates(self.selected_gpu).gpu

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

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
                return [0x00, 0xFF, 0x00]
            elif usage < 70.:
                return [0xFF, 0xFF, 0x00]
            else:
                return [0xFF, 0x00, 0x00]

        cpu_line_length_px = int(self.cpu_usage_percent / 100. * self.MAX_LINE_LENGTH_PX)
        gpu_line_length_px = int(self.gpu_usage_percent / 100. * self.MAX_LINE_LENGTH_PX)

        frame[1:(cpu_line_length_px + 1), 0:self.LINE_WIDTH, :] = getUsageLineColor(self.cpu_usage_percent)
        frame[18:(gpu_line_length_px + 18), 0:self.LINE_WIDTH, :] = getUsageLineColor(self.gpu_usage_percent)

        return frame.flatten()