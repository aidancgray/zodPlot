#!/usr/bin/python3

import sys, os
import time
import numpy as np

from frame_buffer import Framebuffer


start_time = time.time()
NUM_PIXELS = 100000

def main():
    
    print(f'~~~~~~ {os.path.realpath(os.path.dirname(__file__))}  ~~~~~~')

    # generate random data
    px_list = np.random.randint(0,479,(NUM_PIXELS,2))

    fb0 = Framebuffer(use_buffer_fb=True)
    
    proc_time_1 = time.time()

    # add each "photon" to the buffer
    for i in range(len(px_list)):
        fb0.write_px(x=px_list[i][0], y=px_list[i][1], update=False)

    proc_time_2 = time.time()

    wp_time = 1000 * ( proc_time_2 - proc_time_1 )  # ms
    wp_time_ppx = 1000 * ( proc_time_2 - proc_time_1 ) / NUM_PIXELS  # ms/px
    wp_rate = 1 / ( wp_time_ppx / 1000 )  # px/s
    
    print(f'write_px:  {wp_time} ms')
    print(f'write_px:  {wp_time_ppx} ms/px')
    print(f'write_px:  {wp_rate} px/s')

    wait_ = input("update screen...")

    proc_time_3 = time.time()

    # blit buffer into framebuffer
    fb0.update_fb()

    proc_time_4 = time.time()

    update_time = ( proc_time_4 - proc_time_3  ) * 1000  # ms 
    total_time = ( wp_time + update_time ) * 1000  # ms

    print(f'update_fb: {update_time} ms')
    print(f'TOTAL:     {total_time} ms')

    wait_ = input("clear screen...")
    fb0.clear_screen()

if __name__ == "__main__":
    main()