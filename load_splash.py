import time
import sys
import os
import glob
from frame_buffer import Framebuffer


def extract_byte_data(file_):
    if not os.path.isfile(file_):
        return None
    else:
        with open(file_, 'rb') as f:
            return f.read()

def get_splash_images(dir_):
    byte_data_list = []
    
    file_list = glob.glob(f'{dir_}*.fb')
    file_list.sort(key=lambda f: int(''.join(filter(str.isdigit,f))))

    for file_ in file_list:
        r = extract_byte_data(file_)
        if r is not None:
            byte_data_list.append(r)
    
    return byte_data_list

if __name__ == "__main__":
    fb = Framebuffer()
    fb.clear_screen()
    
    if len(sys.argv) == 2:
        splash_dir = sys.argv[1]
        sleep_time = 1
    elif len(sys.argv) == 3:
        splash_dir = sys.argv[1]
        sleep_time = float(sys.argv[2])
    else:
        sys.exit(f'ERROR: invalid arguments')
    
    if splash_dir[0] == '~':
        splash_dir = os.path.expanduser('~')+splash_dir[1:]

    if splash_dir[-1] != '/':
        splash_dir += '/'

    if not os.path.isdir(splash_dir):
        sys.exit(f'ERROR: \'{splash_dir}\' is not a directory')
    
    byte_data_list = get_splash_images(splash_dir)

    byte_data_list = byte_data_list[:-1] + byte_data_list[::-1]

    if len(byte_data_list) > 0:
        for img_bytes in byte_data_list:
            fb.write_bytes_to_fb(img_bytes)
            time.sleep(sleep_time)
