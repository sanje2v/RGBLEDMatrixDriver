import matplotlib.pyplot as plt
import colorsys
import numpy as np
import random
from copy import deepcopy
import imageio


IMAGE_SIZE = (500, 500)
#color_gradient_image = np.zeros((*IMAGE_SIZE, 3), dtype=np.uint8)

#for s in range(IMAGE_SIZE[0]):
#    for h in range(IMAGE_SIZE[1]):
#        color = np.array(list(map(lambda x: int(x * 255.), colorsys.hsv_to_rgb(h/IMAGE_SIZE[0], 1. - s/IMAGE_SIZE[1], 1.0))), dtype=np.uint8)
#        color_gradient_image[s, h, :] = color

color_gradient_image = imageio.imread('test.bmp')

fig=plt.figure(1)
fig.suptitle('Original 24-bit color image')
plt.imshow(color_gradient_image)

fig=plt.figure(2)
fig.suptitle('Recovered from 15-bit color image')
recovered_color_gradient_image = np.array(list(map(lambda x: ((x >> 3) << 3), color_gradient_image)), dtype=np.uint8)
plt.imshow(recovered_color_gradient_image)

fig=plt.figure(3)
fig.suptitle('Recovered (with brightness dithering) 24-bit color image')
random.seed()
recovered_brightnessdither_color_gradient_image = deepcopy(recovered_color_gradient_image)
for i in range(IMAGE_SIZE[0]):
    for j in range(IMAGE_SIZE[1]):
        dithering_brightness = random.randint(-7, 7)
        new_color_data = np.array(list(map(lambda x: x if x == 0 else min(max(x+dithering_brightness, 0), 255), recovered_brightnessdither_color_gradient_image[i, j, :])), dtype=np.uint8)
        recovered_brightnessdither_color_gradient_image[i, j, :] = new_color_data
plt.imshow(recovered_brightnessdither_color_gradient_image)

fig=plt.figure(4)
fig.suptitle('Recovered (with color dithering) 24-bit color image')
random.seed()
recovered_colordither_color_gradient_image = deepcopy(recovered_color_gradient_image)
for i in range(IMAGE_SIZE[0]):
    for j in range(IMAGE_SIZE[1]):
        def dither_color(x):
            dithering_color = random.randint(-7, 7)
            return (x if x == 0 else min(max(x+dithering_color, 0), 255))
        new_color_data = np.array(list(map(dither_color, recovered_colordither_color_gradient_image[i, j, :])), dtype=np.uint8)
        recovered_colordither_color_gradient_image[i, j, :] = new_color_data
plt.imshow(recovered_colordither_color_gradient_image)

plt.show()