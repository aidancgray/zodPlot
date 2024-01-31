import sys
import time
import pigpio as gpio

CLR_BTN_PN = 21
zodpi = gpio.pi()
zodpi.set_mode(CLR_BTN_PN, gpio.INPUT)
zodpi.set_pull_up_down(CLR_BTN_PN, gpio.PUD_UP)
zodpi.set_glitch_filter(CLR_BTN_PN, 300)

clr_count = 0 

def clear_screen_cb(GPIO, level, tick):
    # tell framebuffer to clear
    global clr_count
    clr_count += 1
    print(f'CLEAR_SCREEN:{clr_count}')

if not zodpi.connected:
    exit()
   
cb = zodpi.callback(CLR_BTN_PN, gpio.FALLING_EDGE, clear_screen_cb)

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("\nTidying up")
    cb.cancel()

zodpi.stop()
