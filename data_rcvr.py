import time
import asyncio
import pigpio as gpio
from frame_buffer import Framebuffer
from ec11 import Encoder

class Plot2FrameBuffer():

    def __init__(self, logger, q_mp, closing_event, gpio_map, opts):
        self.logger = logger
        self.logger.info('starting framebuffer display ...')

        self.q_mp = q_mp
        self.closing_event = closing_event
        self.gpio_map = gpio_map

        self.timer = time.time()
        self.update_time = opts.updateTime / 1000

        self.fb = Framebuffer(gain=opts.gain, scr_shot_path=opts.imgLog)

        # Setup GPIO pins
        self.zodpi = gpio.pi()

        # Setup SCREENSHOT button
        self.zodpi.set_mode(self.gpio_map['screenshot'], gpio.INPUT)
        self.zodpi.set_pull_up_down(self.gpio_map['screenshot'], gpio.PUD_UP)
        self.zodpi.set_glitch_filter(self.gpio_map['screenshot'], 10000)

        # Setup CLEAR button
        self.zodpi.set_mode(self.gpio_map['clear'], gpio.INPUT)
        self.zodpi.set_pull_up_down(self.gpio_map['clear'], gpio.PUD_UP)
        self.zodpi.set_glitch_filter(self.gpio_map['clear'], 10000)
    
        # Setup GAIN control knob
        self.enc = Encoder(low=self.gpio_map['enc_lo'],
                           high=self.gpio_map['enc_hi'],
                           switch=self.gpio_map['enc_switch'])

        self.clr_count = 0

    def print_photon_count(self):
        self.logger.info('')
        self.logger.info(f'total photons:   {self.fb.num_photons_total}')
        self.logger.info(f'current photons: {self.fb.num_photons_current}')
        
    async def start_get_q_mp_data(self):
        self.logger.info('... framebuffer display started')
        try:
            while not self.closing_event.is_set():
                if not self.q_mp.empty():
                    photon_list = self.q_mp.get()
                    
                    for photon in photon_list:                         
                        x = (photon[1] << 8) + photon[0]
                        y = (photon[3] << 8) + photon[2]
                        p = photon[4]

                        self.fb.raw_data_to_screen_mono(x, y, p, update=False)

                await asyncio.sleep(0)

        except KeyboardInterrupt:
            self.closing_event.set()
        finally:
            self.print_photon_count()

    async def start_fb_plot(self):
        try:
            if not self.zodpi.connected:
                self.logger.error('!!! GPIO not connected !!!')
                cb_list = []
            else:
                cb_list = self.setup_gpio_callbacks()
                
            while not self.closing_event.is_set():
                if self.enc.value == 0:
                    gain = 1
                elif self.enc.value > 0 and self.enc.value <= 50:
                    gain = self.enc.value * 200
                elif self.enc.value > 50:
                    gain = 10000
                else:
                    gain = 1
               
                self.fb.gain = gain
                self.fb.update_fb()
                await asyncio.sleep(self.update_time)

        except KeyboardInterrupt:
            self.closing_event.set()
        
        finally:
            try:
                for cb in cb_list:
                    cb.cancel()
                self.zodpi.stop()
            except Exception as e:
                self.logger.error(f'{e}')

    def setup_gpio_callbacks(self):
        cb_list = []
        cb_list.append(self.zodpi.callback(self.gpio_map['clear'], 
                                           gpio.FALLING_EDGE, 
                                           self.clear_screen_cb))
        
        cb_list.append(self.zodpi.callback(self.gpio_map['screenshot'], 
                                           gpio.FALLING_EDGE, 
                                           self.screenshot_cb))

    def clear_screen_cb(self, GPIO, level, tick):
        self.fb.reset_fb()
        self.clr_count += 1 
        self.logger.info(f'reset count: {self.clr_count}')

    def screenshot_cb(self, GPIO, level, tick):
        self.fb.screenshot()
        self.logger.info('*screenshot*')