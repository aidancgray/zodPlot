import pigpio as gpio

class Encoder:
    def __init__(self, low, high, switch, callback=None):
        self.pin_low = low
        self.pin_high = high
        self.pin_switch = switch
        self.callback = callback

        self.value = 0
        self.prev_state = 0  # 00 | 01 | 10 | 11
        self.direction = None  # l | r

        self.pi_gpio = gpio.pi()
        self.pi_gpio.set_mode(self.pin_low, gpio.INPUT)
        self.pi_gpio.set_mode(self.pin_high, gpio.INPUT)
        self.pi_gpio.set_mode(self.pin_switch, gpio.INPUT)
        self.pi_gpio.set_pull_up_down(self.pin_low, gpio.PUD_DOWN)
        self.pi_gpio.set_pull_up_down(self.pin_high, gpio.PUD_DOWN)
        self.pi_gpio.set_pull_up_down(self.pin_switch, gpio.PUD_DOWN)
        
        self.cb_list = []
        self.cb_list.append(
            self.pi_gpio.callback(self.pin_low, gpio.EITHER_EDGE, self.rotary_cb))
        self.cb_list.append(
            self.pi_gpio.callback(self.pin_high, gpio.EITHER_EDGE, self.rotary_cb))
        self.cb_list.append(
            self.pi_gpio.callback(self.pin_switch, gpio.FALLING_EDGE, self.callback))

    def rotary_cb(self, GPIO, level, tick):
        new_state = self.pi_gpio.read(self.pin_low) \
                  + (self.pi_gpio.read(self.pin_high) << 1)
        
        if self.prev_state == 0:
            if new_state == 0b01:
                self.direction = 'r'
            elif new_state == 0b10:
                self.direction = 'l'

        elif self.prev_state == 0b01:
            if new_state == 0b00:
                if self.direction == 'l':
                    self.value -= 1    
            elif new_state == 0b11:
                self.direction = 'r'

        elif self.prev_state == 0b10:
            if new_state == 0b00:
                if self.direction == 'r':
                    self.value += 1
            elif new_state == 0b11:
                self.direction = 'l'

        else:
            if new_state == 0b00:
                if self.direction == 'l':
                    self.value -= 1
                elif self.direction == 'r':
                    self.value += 1
            elif new_state == 0b01:
                self.direction = 'l'
            elif new_state == 0b10:
                self.direction = 'r'

        self.prev_state = new_state

    def __del__(self):
        for cb in self.cb_list:
            cb.cancel()
        self.pi_gpio.stop()
