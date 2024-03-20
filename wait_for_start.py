import sys
import subprocess
import pigpio as gpio


START_BUTTON_PIN = 21
CLEAR_BUTTON_PIN = 20
ENC_BUTTON_PIN = 13

def setup_gpio(pi_gpio, pin):
    pi_gpio.set_mode(pin, gpio.INPUT)
    pi_gpio.set_pull_up_down(pin, gpio.PUD_UP)
    pi_gpio.set_glitch_filter(pin, 10000)

def main(files):
    exit_code = 0
    file_count = len(files)-1

    pi_gpio = gpio.pi()
    setup_gpio(pi_gpio, START_BUTTON_PIN)
    setup_gpio(pi_gpio, CLEAR_BUTTON_PIN)
    setup_gpio(pi_gpio, ENC_BUTTON_PIN)

    start_flag = True
    while start_flag:
        if pi_gpio.wait_for_edge(START_BUTTON_PIN, gpio.FALLING_EDGE, 1):
            start_flag = False
            if pi_gpio.read(ENC_BUTTON_PIN) == 0:
                exit_code = 1
            elif pi_gpio.read(CLEAR_BUTTON_PIN) == 0:
                exit_code = 2
        else:
            if files != None:
                subprocess.run(["cp", files[file_count], "/dev/fb0"])
                if file_count == 0:
                    file_count = len(files)-1
                else:
                    file_count -= 1
    
    return exit_code

if __name__ == "__main__":
    if len(sys.argv) == 3:
        files = [sys.argv[1], sys.argv[2]]
    else:
        files = None
    sys.exit(main(files))
