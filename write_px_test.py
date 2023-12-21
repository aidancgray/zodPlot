from frame_buffer import Framebuffer
import time
import numpy as np


start_time = time.time()
NUM_PIXELS = 100000
px_list = np.random.randint(0,479,(NUM_PIXELS,2))

fb0 = Framebuffer()

lap_time_1 = time.time()

fb0.clear_screen()

lap_time_2 = time.time()

fb0.fb.seek(0)

lap_time_3 = time.time()

for i in range(len(px_list)):
    fb0.write_pixel(x=px_list[i][0], y=px_list[i][1])

lap_time_4 = time.time()

cls_time = (lap_time_2-lap_time_1) * 1000  # ms
sk_time = (lap_time_3-lap_time_2) * 1000  # ms
wp_time = 1000* (lap_time_4-lap_time_3) / NUM_PIXELS  # ms/px
wp_rate = 1 / (wp_time / 1000)  # px/s

print(f'clear_screen: {cls_time} ms')
print(f'seek:         {sk_time} ms')
print(f'write_pixel:  {wp_time} ms/px')
print(f'write_pixel:  {wp_rate} px/s')

wait_ = input("clear screen...")
fb0.clear_screen()