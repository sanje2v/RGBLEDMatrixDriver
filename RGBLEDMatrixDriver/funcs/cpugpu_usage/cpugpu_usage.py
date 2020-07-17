import imageio
import psutil
import GPUtil
import numpy as np
from copy import deepcopy


class cpugpu_usage:
    MAX_LINE_LENGTH_PX = 25
    LINE_WIDTH = 2
    LINE_START_FROM_END = -2
    NUM_WIDTH_PX, NUM_HEIGHT_PX = (32, 8)

    def __init__(self):
        # Need to load template image
        self.template = imageio.imread('./funcs/cpugpu_usage/template.bmp')

        # CAUTION: Need to call CPU usage function at least once
        #          before calling it in 'get_frame()'
        self.cpu_usage_percent = psutil.cpu_percent()
        self.gpu_usage_percent = GPUtil.getGPUs()[0].load * 100.0

    def get_frame(self):
        # Get CPU and GPU usage percentages
        self.cpu_usage_percent = psutil.cpu_percent()
        self.gpu_usage_percent = GPUtil.getGPUs()[0].load * 100.0

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

        frame[self.LINE_START_FROM_END:(-cpu_line_length_px + self.LINE_START_FROM_END):-1,\
              1:(self.LINE_WIDTH+1),\
              :] = getUsageLineColor(self.cpu_usage_percent)
        frame[self.LINE_START_FROM_END:(-gpu_line_length_px + self.LINE_START_FROM_END):-1,\
              5:(5+self.LINE_WIDTH),\
              :] = getUsageLineColor(self.gpu_usage_percent)

        return frame.flatten()