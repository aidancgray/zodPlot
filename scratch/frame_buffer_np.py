import numpy as np

class Framebuffer_np():
    def __init__(self, fb_path="/dev/fb0"):
        with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
            screen = f.read()
            self.width, self.height = [int(i) for i in screen.split(",")]

        with open("/sys/class/graphics/fb0/bits_per_pixel", "r") as f:
            self.bits_pp = int(f.read()[:2])
            self.bytes_pp = self.bits_pp // 8

        self.fb = np.memmap(fb_path, 
                            dtype='uint8', 
                            mode='w+', 
                            shape=(self.height,self.width,self.bytes_pp))

    def write_pixel(self, x, y, r=255, g=255, b=255, t=0):
        self.fb[y, x] = [b, g, r, t]
        """
        if self.bits_pp == 32:
            self.fb[y, x] = [b, g, r, t]
        else:
            self.fb[y, x] = [r, g, b]
        """
        
    def fill_screen(self, r=255, g=255, b=255, t=0):
        if self.bits_pp == 32:
            self.fb[:] = [b, g, r, t]
        else:
            self.fb[:] = [r, g, b]

    def clear_screen(self):
        self.fill_screen(0, 0, 0, 0)