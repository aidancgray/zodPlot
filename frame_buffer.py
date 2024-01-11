import os
import mmap
import numpy as np
import logging

class Framebuffer():
    def __init__(self, fb_path="/dev/fb0",src_size_bit_depth=16,
                 use_numpy_memmap=False, use_numpy_buffer=False, 
                 use_buffer_fb=False, use_numpy_ndarray=False):
        '''
        mode 1 = use_numpy_memmap
        mode 2 = use_numpy_buffer
        mode 3 = use_buffer_fb
        mode 4 = use_numpy_ndarray
        '''
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('FBUFF')
        self.logger.setLevel(logging.INFO) 

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
            self.mode = 1
            
        elif use_numpy_buffer:
            fb_f = os.open(fb_path, os.O_RDWR)
            fb_mmap = mmap.mmap(fb_f, self.width * self.height * self.bytes_pp)
            self.fb = np.ndarray(shape=(self.height, self.width, self.bytes_pp), dtype=np.uint8, buffer=fb_mmap)
            self.fb_buf = np.ndarray(shape=self.fb.shape, dtype=float)
            self.fb_buf[:] = 0.0
            self.mode = 2
        
        elif use_buffer_fb:
            fb_f = os.open(fb_path, os.O_RDWR)
            self.fb = mmap.mmap(fb_f, self.width * self.height * self.bytes_pp)
            self.fb_buf = np.ndarray(shape=(self.height, self.width, self.bytes_pp), dtype=float)
            self.fb_buf[:] = 0.0
            self.mode = 3

        elif use_numpy_ndarray:
            fb_f = os.open(fb_path, os.O_RDWR)
            fb_mmap = mmap.mmap(fb_f, self.width * self.height * self.bytes_pp)
            self.fb = np.ndarray(shape=(self.height, self.width, self.bytes_pp), dtype=np.uint8, buffer=fb_mmap)
            self.mode = 4

        else:
            fb_f = os.open(fb_path, os.O_RDWR)
            self.fb = mmap.mmap(fb_f, self.width * self.height * self.bytes_pp)
            self.mode = 0
            self.fb_zero = b'\x00' * self.width * self.height * self.bytes_pp

        self.num_photons_total = self.num_photons_current = 0

    def update_fb(self):
        if self.mode==2:
            self.fb[:] = self.fb_buf.round()
        elif self.mode==3:
            buf_tmp = np.uint8(np.clip(self.fb_buf.reshape(-1).round(), 0, 255))
            self.fb.seek(0)
            self.fb.write(buf_tmp)

    def _write_px_to_buf(self, x, y, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb_buf[y, x] += [b, g, r, t]
        else:
            self.fb_buf[y, x] += [r, g, b]

    def write_px(self, x, y, r=255, g=255, b=255, t=0, update=True):
        if self.mode == 2 or self.mode == 3:
            self._write_px_to_buf(x, y, r, g, b, t)
            if update:
                self.update_fb()

        elif self.mode == 0:
            # Not yet implemented
            pass

        else:
            if self.bits_pp == 32:
                self.fb[y, x] += np.array([b, g, r, t], np.uint8)
            else:
                self.fb[y, x] += np.array([r, g, b], np.uint8)

    def fill_row(self, y, r=255, g=255, b=255, t=0):
        if self.mode == 2 or self.mode == 3:
            if self.bits_pp == 32:
                self.fb_buf[y, :] = [b, g, r, t]
            else:
                self.fb_buf[y, :] = [r, g, b]
            
            self.update_fb()
        
        elif self.mode == 0:
            # Not yet implemented
            pass

        else:
            if self.bits_pp == 32:
                self.fb[y, :] = np.array([b, g, r, t], np.uint8)
            else:
                self.fb[y, :] = np.array([r, g, b], np.uint8)
        
    def fill_column(self, x, r=255, g=255, b=255, t=0):
        if self.mode == 2 or self.mode == 3:
            if self.bits_pp == 32:
                self.fb_buf[: ,x] = [b, g, r, t]
            else:
                self.fb_buf[: ,x] = [r, g, b]
            
            self.update_fb()
        
        elif self.mode == 0:
            # Not yet implemented
            pass

        else:
            if self.bits_pp == 32:
                self.fb[: ,x] = np.array([b, g, r, t], np.uint8)
            else:
                self.fb[: ,x] = np.array([r, g, b], np.uint8)
        
    def fill_screen(self, r=255, g=255, b=255, t=0):    
        if self.mode == 2 or self.mode == 3:
            if self.bits_pp == 32:
                self.fb_buf[:] = [b, g, r, t]
            else:
                self.fb_buf[:] = [r, g, b]
            
            self.update_fb()
            
        elif self.mode == 0:
            # Not yet implemented
            pass

        else:
            if self.bits_pp == 32:
                self.fb[:] = np.array([b, g, r, t], np.uint8)
            else:
                self.fb[:] = np.array([r, g, b], np.uint8)

    def clear_screen(self):
        if self.mode == 0:
            self.fb.seek(0)
            self.fb.write(self.fb_zero)
        else:
            self.fill_screen(0, 0, 0, 0)
        
        self.num_photons_current = 0

    def raw_data_to_screen_mono(self, x, y, p, update=False):
        self.logger.debug(f'x_raw: {x}')
        self.logger.debug(f'y_raw: {y}')

        self.num_photons_current += 1
        self.num_photons_total += 1

        x_screen = round(x * self.size_ratio)
        y_screen = round(y * self.size_ratio)
        # p_screen = p * self.p_ratio
        p_screen = p
        self.write_px(x_screen, y_screen, p_screen, p_screen, p_screen, 0, update)
        self.logger.debug(f'y: {y_screen} | x: {x_screen} | p: {p_screen}')