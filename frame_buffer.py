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
            
    def draw_line(self, x0, y0, x1, y1, r=255, g=255, b=255, t=0):
        # Start and stop coords must be positive
        if (x0 < 0) or (x1 < 0) or (y0 < 0) or (y1 < 0):
            return -1

        # check if horiz line - easiest line to draw
        if y0 == y1:
            px_bytes = self._construct_px_bytes(r, g, b, t)
            if x0 == x1:
                line_bytes = px_bytes
            else:
                line_bytes = px_bytes * abs(x1 - x0)
            mem_pos = (y0 * self.bytes_pp * self.width) + min(x0, x1)
            self.fb.seek(mem_pos)
            bits_written = self.fb.write(line_bytes)
        
        # check if vert line - simply loop through row
        elif x0 == x1:
            line_len = abs(y1 - y0)
            bits_written = 0
            for y in range(line_len):
                bits_written = bits_written + self.write_pixel(x0, y, r, g, b, t)

        # must be diagonal...
        else:
            m = ( y1 - y0 ) / ( x1 - x0 )
            c = y0 - ( m * x0 )

            # draw the pixelated line whichever way results in more pixels
            num_x = abs(x1-x0)
            num_y = abs(y1-y0)
            px_list = []

            if num_x >= num_y:
                # solve y = m * x + c for each x
                for x in range(min(x0,x1), max(x0,x1)+1):
                    y = round(( x * m ) + c)
                    px = (x, y)
                    px_list.append(px)
            else:
                # solve x = ( y - c ) / m for each y
                for y in range(min(y0,y1), max(y0,y1)):
                    x = round(( y - c ) / m)
                    px = (x, y)
                    px_list.append(px)

            # draw the line pixel-by-pixel
            bits_written = 0
            for px in px_list:
                bits_written = bits_written + self.write_pixel(px[0], px[1], r, g, b, t)
        
        return bits_written