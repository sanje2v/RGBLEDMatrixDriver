import matplotlib.pyplot as plt
import imageio
from copy import deepcopy

template = imageio.imread('./funcs/cpugpu_usage/template.bmp')
im = deepcopy(template)

print(im.shape)
cpu_length = 5
im[(-2):-1:5,1:3,:] = [0xFF, 0x00, 0x00]

plt.imshow(im)
plt.show()