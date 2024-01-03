from frame_buffer_old import Framebuffer
import time
import numpy as np


print('######## Framebuffer Write Speed using Python Std Lib mmap() ########')

start_time = time.time()
NUM_PIXELS = 10000
px_list = np.random.randint(0,479,(NUM_PIXELS,2))

fb0 = Framebuffer()

lap_time_1 = time.time()

fb0.clear_screen()

lap_time_2 = time.time()

fb0.fb.seek(0)

lap_time_3 = time.time()

for i in range(len(px_list)):
    fb0.write_px_to_buf(x=px_list[i][0], y=px_list[i][1])

lap_time_4 = time.time()

fb0.update_fb()

lap_time_5 = time.time()

cls_time = (lap_time_2-lap_time_1) * 1000  # ms
sk_time = (lap_time_3-lap_time_2) * 1000  # ms
wp_time = 1000* (lap_time_4-lap_time_3) / NUM_PIXELS  # ms/px
wp_rate = 1 / (wp_time / 1000)  # px/s
update_fb_time = (lap_time_5-lap_time_4) * 1000  # ms
buf_total_time = (lap_time_5-lap_time_3) * 1000  # ms

print(f'clear_screen:    {cls_time} ms')
print(f'seek:            {sk_time} ms')
print(f'write_px_to_buf: {wp_time} ms/px')
print(f'write_px_to_buf: {wp_rate} px/s')
print(f'update_fb:       {update_fb_time} ms')
print(f'W/ BUF TOTAL:    {buf_total_time} ms')
print(f'---')

fb0.clear_screen()
fb0.fb.seek(0)

lap_time_6 = time.time()

for i in range(len(px_list)):
    fb0.write_pixel(x=px_list[i][0], y=px_list[i][1])

lap_time_7 = time.time()

wp_time = 1000* (lap_time_7-lap_time_6) / NUM_PIXELS  # ms/px
wp_rate = 1 / (wp_time / 1000)  # px/s
no_buf_total_time = (lap_time_7-lap_time_6) * 1000  # ms

print(f'write_px NO BUF: {wp_time} ms/px')
print(f'write_px NO BUF: {wp_rate} px/s')
print(f'NO BUF TOTAL:    {no_buf_total_time} ms')

wait_ = input("clear screen...")
fb0.clear_screen()