import time
import asyncio
import pigpio as gpio
from frame_buffer import Framebuffer


class Plot2FrameBuffer():

    def __init__(self, logger, q_mp, closing_event, gpio_num, opts):
        self.logger = logger
        self.logger.info('starting framebuffer display ...')

        self.q_mp = q_mp
        self.closing_event = closing_event
        self.gpio_num = gpio_num

        self.timer = time.time()
        self.update_time = opts.updateTime / 1000

        self.fb = Framebuffer(gain=opts.gain)

        self.zodpi = gpio.pi()
        self.zodpi.set_mode(self.gpio_num, gpio.INPUT)
        self.zodpi.set_pull_up_down(self.gpio_num, gpio.PUD_UP)
        self.zodpi.set_glitch_filter(self.gpio_num, 300)
    
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
            else:
                self.cb = self.zodpi.callback(self.gpio_num, 
                                              gpio.FALLING_EDGE, 
                                              self.clear_screen_cb)
                
            while not self.closing_event.is_set():
                self.fb.update_fb()
                await asyncio.sleep(self.update_time)

        except KeyboardInterrupt:
            self.closing_event.set()
        
        finally:
            try:
                self.cb.cancel()
                self.zodpi.stop()
            except Exception as e:
                self.logger.error(f'{e}')

    def clear_screen_cb(self, GPIO, level, tick):
        self.fb.reset_fb()
        self.clr_count += 1 
        self.logger.info(f'reset count: {self.clr_count}')