import os
import sys
import subprocess
from frame_buffer import Framebuffer

fb0 = Framebuffer()
fb0.clear_screen()

filename = sys.argv[1]

if os.path.isfile(filename):
    subprocess.run(["cp", filename, "/dev/fb0"])
    print('OK')
else:
    print('BAD')