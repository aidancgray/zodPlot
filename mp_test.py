import os
import sys
import time
import asyncio
import mmap
import logging
import numpy as np
import timeit

from multiprocessing import Pool, Process, Queue, Event
from signal import SIGINT, SIGTERM


NUM_PIXELS = 1000
TIMEIT_LOOP = 100000

def say_hello():
    print('Hello!')

def run_process():
    result = timeit.timeit('say_hello()', globals=globals(), number=TIMEIT_LOOP)
    print(result/TIMEIT_LOOP)

def proc_test():
    p = Process(target=run_process,
                args=())
    
    p.start()
    p.join()

def f(x):
    time.sleep(1)
    # print(x)
    return x*x

def pool_test():
    with Pool(processes=10) as pool:
        # print(p.map(f, [1, 2, 3]))
        t0 = time.time()
        result = pool.apply_async(f, (10,))
        
        print(f'0: {time.time() - t0}')
        
        print(result.get(timeout=None))
        
        t1 = time.time()
        print(f'1: {t1 - t0}')

        print(pool.map(f, range(10)))

        t2 = time.time()
        print(f'2: {t2 - t1}')

        it = pool.imap(f, range(10))
        print(next(it))
        print(next(it))
        print(it.next(timeout=None))

        result = pool.apply_async(time.sleep, (10,))
        print(result.get(timeout=None))

        print('Done')

class Framebuffer():
    def __init__(self):
        with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
            screen = f.read()
            width, height = [int(i) for i in screen.split(",")]
    
        with open("/sys/class/graphics/fb0/bits_per_pixel", "r") as f:
            bits_pp = int(f.read()[:2])
            bytes_pp = bits_pp // 8
        
        size_ratio = (width - 1) / (2 ** 16 - 1)
        p_ratio = size_ratio ** 2
    
        fb_path="/dev/fb0"
        fb_f = os.open(fb_path, os.O_RDWR)
        len_fb = width * height * bytes_pp
        
        self.fb = mmap.mmap(fb_f, len_fb)
        self.fb_buf = np.ndarray(shape=(height, width, bytes_pp), dtype=np.single)
        self.fb_buf[:] = 0.0

    def update_fb(self):
        buf_tmp = self.fb_buf

        t0 = time.time()
        buf_tmp = buf_tmp.reshape(-1)

        t1 = time.time()
        # buf_tmp = np.round(buf_tmp)
        
        t2 = time.time()
        buf_tmp = (buf_tmp + 0.5).astype(np.uint8)
        
        t3 = time.time()
        buf_tmp = np.clip(buf_tmp, 0, 255)
        
        t4 = time.time()
        self.fb.seek(0)
        t5 = time.time()
        self.fb.write(buf_tmp)
        t6 = time.time()

        print(f'----------------------')
        print(f'1: {np.float16((t1-t0)*1000)} ms')
        print(f'2: {np.float16((t2-t1)*1000)} ms')
        print(f'3: {np.float16((t3-t2)*1000)} ms')
        print(f'4: {np.float16((t4-t3)*1000)} ms')
        print(f'----------------------')

    def _write_px_to_buf(self, x, y, r=255, g=255, b=255, t=0):
        self.fb_buf[y, x] += [b, g, r, t]

    def write_px(self, x, y, r=255, g=255, b=255, t=0, update=True):
        self._write_px_to_buf(x, y, r, g, b, t)
        if update:
            self.update_fb()

def main():
    
    fb_ = Framebuffer()

    px_list = np.random.randint(0,479,(NUM_PIXELS,2))
    
    print("write px to fb_buf...")
    t0 = time.time()
    for i in range(len(px_list)):
        fb_.write_px(x=px_list[i][0], y=px_list[i][1], update=False)
    t1 = time.time()
    print(f'write_px:  {((t1-t0)/NUM_PIXELS)*1000} ms')
    
    print("blit to fb...")
    t2 = time.time()
    fb_.update_fb()
    t3 = time.time()

    print(f'update_fb: {(t3-t2)*1000} ms')

    print("...done")

if __name__ == "__main__":
    main()
