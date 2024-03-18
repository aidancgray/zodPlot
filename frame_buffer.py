import time
import os
import mmap
import subprocess
import numpy as np

class Framebuffer():
    def __init__(self, fb_path="/dev/fb0", src_size_bit_depth=14, gain=1,
                 scr_shot_path='/home/idg/imgs/'):

        self.gain = gain
        self.scr_shot_path = scr_shot_path

        with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
            screen = f.read()
            self.width, self.height = [int(i) for i in screen.split(",")]

        with open("/sys/class/graphics/fb0/bits_per_pixel", "r") as f:
            self.bits_pp = int(f.read()[:2])
            self.bytes_pp = self.bits_pp // 8

        self.total_bytes = self.width * self.height * self.bytes_pp
        self.size_ratio = (self.width - 1) / (2 ** src_size_bit_depth - 1)
        self.p_ratio = self.size_ratio ** 2
        
        fb_f = os.open(fb_path, os.O_RDWR)
        self.fb = mmap.mmap(fb_f, 
                            self.total_bytes)
        self.fb_buf = np.ndarray(shape=(self.height, self.width, self.bytes_pp), 
                                    dtype=np.single)
        self.fb_buf[:] = 0.0

        self.num_photons_total = self.num_photons_current = 0

    def get_max_pixel(self):
        self.fb.seek(0)
        all_bytes = self.fb.read(self.total_bytes)
        max_px = max(all_bytes)
        return max_px

    def screenshot(self):
        filename = time.strftime("%Y%m%d_%H%M%S")
        filepath = f'{self.scr_shot_path}{filename}.cap'
        subprocess.run(['cp', '/dev/fb0', filepath])

    def write_bytes_to_fb(self, bytes_):
        self.fb.seek(0)
        self.fb.write(bytes_)

    def update_fb(self):
        buf_tmp = self.fb_buf * self.gain
        buf_tmp_flat = buf_tmp.reshape(-1)
        buf_tmp_int = (buf_tmp_flat + 0.5).astype(np.uint8)
        buf_tmp_ready = np.clip(buf_tmp_int, 0, 255)
        self.fb.seek(0)
        self.fb.write(buf_tmp_ready)

    def _write_px_to_buf(self, x, y, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb_buf[y, x] += [b, g, r, t]
        else:
            self.fb_buf[y, x] += [r, g, b]

    def write_px(self, x, y, r=255, g=255, b=255, t=0, update=True):
        self._write_px_to_buf(x, y, r, g, b, t)
        if update:
            self.update_fb()

    def fill_row(self, y, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb_buf[y, :] = [b, g, r, t]
        else:
            self.fb_buf[y, :] = [r, g, b]
        
        self.update_fb()
        
    def fill_column(self, x, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb_buf[: ,x] = [b, g, r, t]
        else:
            self.fb_buf[: ,x] = [r, g, b]
        
        self.update_fb()
        
    def fill_screen(self, r=255, g=255, b=255, t=0):    
        if self.bits_pp == 32:
            self.fb_buf[:] = [b, g, r, t]
        else:
            self.fb_buf[:] = [r, g, b]
        
        self.update_fb()

    def clear_screen(self):
        self.fill_screen(0, 0, 0, 0)
        self.num_photons_current = 0

    def raw_data_to_screen_mono(self, x, y, p, update=False):
        self.num_photons_current += 1
        self.num_photons_total += 1

        x_screen = int((x * self.size_ratio) + 0.5)
        y_screen = int((y * self.size_ratio) + 0.5)

        p_screen = p * self.p_ratio
        
        self.write_px(x_screen, y_screen, p_screen, p_screen, p_screen, 0, update)

    def reset_fb(self):
        # self.screenshot()
        self.clear_screen()