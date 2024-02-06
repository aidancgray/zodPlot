import sys
from math import ceil

DISPLAY_BITS_PP = 32
BMP_FILE_HDR_LEN = 14
# bmp_filename = 'test-bmp-1.bmp'

bmp_filename = sys.argv[1]
fb_filename = bmp_filename.split('.')[0] + '.fb'

# read the binary data into a bytearray
with open(bmp_filename, 'rb') as bmp_file:
    bmp_data = bmp_file.read()  

try: 
    if bmp_data[:2] != b'\x42\x4D':
        raise IndexError
    
    filesize = int.from_bytes(bmp_data[2:6], 'little')
    px_array_offset = int.from_bytes(bmp_data[10:BMP_FILE_HDR_LEN], 'little')
    dib_hdr_len = int.from_bytes(bmp_data[BMP_FILE_HDR_LEN:BMP_FILE_HDR_LEN+4], 'little')
    bmp_width = int.from_bytes(bmp_data[18:22], 'little')
    bmp_height = int.from_bytes(bmp_data[22:26], 'little')
    bpp = int.from_bytes(bmp_data[28:30], 'little')
    img_size = int.from_bytes(bmp_data[34:38], 'little')

    img_data = bmp_data[px_array_offset:]

    assert img_size == len(img_data)

    row_size = ceil( ( bpp * bmp_width ) / 32 ) * 4
    row_list_r = [img_data[i:i+row_size] for i in range(0, len(img_data),row_size)]
    row_list = row_list_r[::-1]  # reverse the row list, so the image data is in order for fb

    img_data_fb = b''

    for row in row_list:
        # Split the byterow into 3-byte chunks (BGR) and ignore anything after width of image
        row_split = [row[i:i+3] for i in range(0, len(row), 3)][:bmp_width]
        
        if DISPLAY_BITS_PP == 32:
            # add the transparency value
            for i, px in enumerate(row_split):
                row_split[i] = px + b'\x00' 
        
        img_data_fb += b''.join(row_split)

    if DISPLAY_BITS_PP == 32:
        img_size_fb = bmp_width * bmp_height * 4
    elif DISPLAY_BITS_PP == 24:
        img_size_fb = bmp_width * bmp_height * 3

    assert img_size_fb == len(img_data_fb)

    with open(fb_filename, 'wb') as fb_file:
        fb_file.write(img_data_fb)
    
    print('done')

except IndexError as exc:
    print('Invalid BMP')

except AssertionError:
    print('Image size does not match expected')

