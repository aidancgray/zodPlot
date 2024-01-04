from frame_buffer import Framebuffer
import time
import numpy as np

start_time = time.time()
NUM_PIXELS = 100000

def test_1():
    print('### test_1: mmap + ndarray ###')

    px_list = np.random.randint(0,479,(NUM_PIXELS,2))
    fb0 = Framebuffer(use_numpy_ndarray=True)
    fb0.clear_screen()

    lap_time_1 = time.time()

    for i in range(len(px_list)):
        fb0.write_px(x=px_list[i][0], y=px_list[i][1])

    lap_time_2 = time.time()

    wp_time = 1000* (lap_time_2-lap_time_1) / NUM_PIXELS  # ms/px
    wp_rate = 1 / (wp_time / 1000)  # px/s
    total_time = (lap_time_2-lap_time_1) * 1000  # ms

    print(f'write_px: {wp_time} ms/px')
    print(f'write_px: {wp_rate} px/s')
    print(f'TOTAL:    {total_time} ms')

    wait_ = input("clear screen...")
    fb0.clear_screen()

def test_2():
    print('### test_2: mmap + ndarray + buffer array ###')

    px_list = np.random.randint(0,479,(NUM_PIXELS,2))
    fb0 = Framebuffer(use_numpy_buffer=True)
    lap_time_1 = time.time()

    for i in range(len(px_list)):
        fb0.write_px_to_buf(x=px_list[i][0], y=px_list[i][1])

    lap_time_2 = time.time()

    fb0.update_fb()

    lap_time_3 = time.time()

    wp_time = 1000* (lap_time_2-lap_time_1) / NUM_PIXELS  # ms/px
    wp_rate = 1 / (wp_time / 1000)  # px/s
    update_time = (lap_time_3-lap_time_2) * 1000  # ms
    total_time = (lap_time_3-lap_time_1) * 1000  # ms

    print(f'write_px_to_buf: {wp_time} ms/px')
    print(f'write_px_to_buf: {wp_rate} px/s')
    print(f'update_fb:       {update_time} ms')
    print(f'TOTAL:           {total_time} ms')

    wait_ = input("clear screen...")
    fb0.clear_screen()

def test_3():
    print('### test_3: numpy memmap ###')

    px_list = np.random.randint(0,479,(NUM_PIXELS,2))
    fb0 = Framebuffer(use_numpy_memmap=True)
    lap_time_1 = time.time()

    for i in range(len(px_list)):
        fb0.write_px(x=px_list[i][0], y=px_list[i][1])

    lap_time_2 = time.time()

    wp_time = 1000* (lap_time_2-lap_time_1) / NUM_PIXELS  # ms/px
    wp_rate = 1 / (wp_time / 1000)  # px/s
    total_time = (lap_time_2-lap_time_1) * 1000  # ms

    print(f'write_px: {wp_time} ms/px')
    print(f'write_px: {wp_rate} px/s')
    print(f'TOTAL:    {total_time} ms')

    wait_ = input("clear screen...")
    fb0.clear_screen()

def test_4():
    print('### test_4: mode 3 ###')

    px_list = np.random.randint(0,479,(NUM_PIXELS,2))
    fb0 = Framebuffer(use_buffer_fb=True)
    lap_time_1 = time.time()

    for i in range(len(px_list)):
        fb0.write_px(x=px_list[i][0], y=px_list[i][1], update=False)

    lap_time_2 = time.time()

    fb0.update_fb()

    lap_time_3 = time.time()

    wp_time = 1000 * (lap_time_2-lap_time_1)  # ms
    wp_time_ppx = 1000 * (lap_time_2-lap_time_1) / NUM_PIXELS  # ms/px
    wp_rate = 1 / (wp_time_ppx / 1000)  # px/s
    update_time = (lap_time_3-lap_time_2) * 1000  # ms 
    total_time = (lap_time_3-lap_time_1) * 1000  # ms

    print(f'write_px:  {wp_time} ms')
    print(f'write_px:  {wp_time_ppx} ms/px')
    print(f'write_px:  {wp_rate} px/s')
    print(f'update_fb: {update_time} ms')
    print(f'TOTAL:     {total_time} ms')

    wait_ = input("clear screen...")
    fb0.clear_screen()

if __name__ == "__main__":
    # test_1()  # 38k px/s
    # test_2()  # 23k px/s
    # test_3()  # 12k px/s
    test_4()