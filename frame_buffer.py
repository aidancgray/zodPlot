import os
import mmap

class Framebuffer():
    def __init__(self, fb_path="/dev/fb0"):
        with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
            screen = f.read()
            self.width, self.height = [int(i) for i in screen.split(",")]

        with open("/sys/class/graphics/fb0/bits_per_pixel", "r") as f:
            self.bits_pp = int(f.read()[:2])
            self.bytes_pp = self.bits_pp // 8

        fb_f = os.open(fb_path, os.O_RDWR)
        self.fb = mmap.mmap(fb_f, self.width * self.height * self.bytes_pp)

    def _construct_px_bytes(self, r, g, b, t):
        if self.bits_pp == 32:
            px_bytes = (b.to_bytes(1, byteorder='little') 
                        + g.to_bytes(1, byteorder='little') 
                        + r.to_bytes(1, byteorder='little') 
                        + t.to_bytes(1, byteorder='little'))
        else:
            px_bytes = (r.to_bytes(1, byteorder='little') 
                        + g.to_bytes(1, byteorder='little') 
                        + b.to_bytes(1, byteorder='little'))
        return px_bytes

    def write_pixel(self, x, y, r=255, g=255, b=255, t=0):
        # mmap position: ( X * bytes-per-pixel ) + ( Y * bytes-per-row )
        mem_pos = (x * self.bytes_pp) + (y * self.bytes_pp * self.width)
        self.fb.seek(mem_pos)
        px_bytes = self._construct_px_bytes(r, g, b, t)
        bits_written = self.fb.write(px_bytes)
        return bits_written

    def fill_row(self, y, r=255, g=255, b=255, t=0):
        mem_pos = y * self.bytes_pp * self.width
        self.fb.seek(mem_pos)
        px_bytes = self._construct_px_bytes(r, g, b, t)
        row_bytes = px_bytes * self.width
        bits_written = self.fb.write(row_bytes)
        return bits_written

    def fill_column(self, x, r=255, g=255, b=255, t=0):
        bits_written = 0
        for y in range(self.height):
            bits_written = bits_written + self.write_pixel(x, y, r, g, b, t)
        return bits_written

    def fill_screen(self, r=255, g=255, b=255, t=0):
        self.fb.seek(0)
        px_bytes = self._construct_px_bytes(r, g, b, t)
        screen_bytes = px_bytes * self.width * self.height
        bits_written = self.fb.write(screen_bytes)
        return bits_written

    def clear_screen(self):
        bits_written = self.fill_screen(0, 0, 0, 0)
        return bits_written
            
