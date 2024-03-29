import pigpio as gpio

class Encoder:
    def __init__(self, low, high, switch, 
                 start_val=0, min_val=None, max_val=None, callback=None):
        self.pin_lo = low
        self.pin_hi = high
        self.pin_switch = switch
        self.start_val = start_val
        self.min_val = min_val
        self.max_val = max_val
        self.callback = callback
        
        self.value = self.start_val
        self.prev_state = 0b11  # 00 | 01 | 10 | 11
        self.direction = None  # l | r

        self.pi_gpio = gpio.pi()
        self.pi_gpio.set_mode(self.pin_lo, gpio.INPUT)
        self.pi_gpio.set_mode(self.pin_hi, gpio.INPUT)
        self.pi_gpio.set_mode(self.pin_switch, gpio.INPUT)
        self.pi_gpio.set_pull_up_down(self.pin_lo, gpio.PUD_UP)
        self.pi_gpio.set_pull_up_down(self.pin_hi, gpio.PUD_UP)
        self.pi_gpio.set_pull_up_down(self.pin_switch, gpio.PUD_UP)
        self.pi_gpio.set_glitch_filter(self.pin_lo, 1)
        self.pi_gpio.set_glitch_filter(self.pin_hi, 1)
        self.pi_gpio.set_glitch_filter(self.pin_switch, 10000)
        
        self.cb_list = []
        self.cb_list.append(
            self.pi_gpio.callback(self.pin_lo, gpio.EITHER_EDGE, self.rotary_cb))
        self.cb_list.append(
            self.pi_gpio.callback(self.pin_hi, gpio.EITHER_EDGE, self.rotary_cb))
        self.cb_list.append(
            self.pi_gpio.callback(self.pin_switch, gpio.FALLING_EDGE, self.reset_value))
    
    def get_status(self):
        return self.value, self.direction

    def reset_value(self, GPIO, level, tick):
        self.value = self.start_val
        self.prev_state = 0b11
        self.direction = None

    def rotary_cb(self, GPIO, level, tick):
        new_state = self.pi_gpio.read(self.pin_hi) \
                  + (self.pi_gpio.read(self.pin_lo) << 1)
        
        # ENC is pulled hi, so 0 is trigger
        if self.prev_state == 0b11:
            if new_state == 0b10:
                self.direction = 'r'
            elif new_state == 0b01:
                self.direction = 'l'

        elif self.prev_state == 0b10:
            if new_state == 0b11:
                if self.direction == 'l':
                    # self.value -= 1 
                    self.dec_val()   
            elif new_state == 0b00:
                self.direction = 'r'

        elif self.prev_state == 0b01:
            if new_state == 0b11:
                if self.direction == 'r':
                    # self.value += 1
                    self.inc_val()
            elif new_state == 0b00:
                self.direction = 'l'

        else:
            if new_state == 0b11:
                if self.direction == 'l':
                    # self.value -= 1
                    self.dec_val()
                elif self.direction == 'r':
                    # self.value += 1
                    self.inc_val()
            elif new_state == 0b10:
                self.direction = 'l'
            elif new_state == 0b01:
                self.direction = 'r'

        self.prev_state = new_state

    def inc_val(self, inc=1):
        if self.max_val != None:
            if ( self.value + inc) > self.max_val:
                self.value = self.max_val
            else:
                self.value += inc
        else:
            self.value += inc

    def dec_val(self, dec=1):
        if self.min_val != None:
            if ( self.value - dec ) < self.min_val:
                self.value = self.min_val
            else:
                self.value -= dec
        else:
            self.value -= dec

    def __del__(self):
        for cb in self.cb_list:
            cb.cancel()
        self.pi_gpio.stop()

if __name__ == "__main__":
    import time

    enc = Encoder(26, 19, 13)

    while True:
        val, dir = enc.get_status()
        print(f'{val}', end='\r')
        time.sleep(0.1)