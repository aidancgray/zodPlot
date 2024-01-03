import os
import mmap
import numpy as np

class Framebuffer():
    def __init__(self, fb_path="/dev/fb0", 
                 src_size_bit_depth=16, 
                 use_numpy_memmap=False, 
                 use_buffer_array=False):
        
        with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
            screen = f.read()
            self.width, self.height = [int(i) for i in screen.split(",")]

        with open("/sys/class/graphics/fb0/bits_per_pixel", "r") as f:
            self.bits_pp = int(f.read()[:2])
            self.bytes_pp = self.bits_pp // 8

        self.size_ratio = (self.width - 1) / (2 ** src_size_bit_depth - 1)
        self.p_ratio = self.size_ratio ** 2

        if use_numpy_memmap:
            self.fb = np.memmap(fb_path, 
                                dtype='uint8', 
                                mode='w+', 
                                shape=(self.height,self.width,self.bytes_pp))
        elif use_buffer_array:
            fb_f = os.open(fb_path, os.O_RDWR)
            fb_mmap = mmap.mmap(fb_f, self.width * self.height * self.bytes_pp)
            self.fb = np.ndarray(shape=(self.height, self.width, self.bytes_pp), dtype=np.uint8, buffer=fb_mmap)
            self.fb_buf = np.ndarray(shape=self.fb.shape, dtype=float)
            self.fb_buf[:] = 0
        else:
            fb_f = os.open(fb_path, os.O_RDWR)
            fb_mmap = mmap.mmap(fb_f, self.width * self.height * self.bytes_pp)
            self.fb = np.ndarray(shape=(self.height, self.width, self.bytes_pp), dtype=np.uint8, buffer=fb_mmap)

    def update_fb(self):
        self.fb[:] = self.fb_buf.round()

    def write_px_to_buf(self, x, y, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb_buf[y, x] += [b, g, r, t]
        else:
            self.fb_buf[y, x] += [r, g, b]

    def write_px(self, x, y, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb[y, x] += np.array([b, g, r, t], np.uint8)
        else:
            self.fb[y, x] += np.array([r, g, b], np.uint8)

    def fill_row(self, y, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb[y, :] = [b, g, r, t]
        else:
            self.fb[y, :] = [r, g, b]
        
    def fill_column(self, x, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb[: ,x] = [b, g, r, t]
        else:
            self.fb[: ,x] = [r, g, b]
        
    def fill_screen(self, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb[:] = [b, g, r, t]
        else:
            self.fb[:] = [r, g, b]

    def clear_screen(self):
        self.fill_screen(0, 0, 0, 0)

    def raw_data_to_screen_mono(self, x, y, p):
        x_screen = round(x * self.size_ratio)
        y_screen = round(y * self.size_ratio)
        p_screen = p * self.p_ratio
        self.write_px(y_screen, x_screen, p_screen, p_screen, p_screen)