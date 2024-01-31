import time
import asyncio
import pigpio as gpio
from frame_buffer import Framebuffer


class Plot2FrameBuffer():

    def __init__(self, logger, q_mp, closing_event, opts):
        self.logger = logger
        self.logger.info('starting framebuffer display ...')

        self.q_mp = q_mp
        self.closing_event = closing_event
        self.timer = time.time()
        self.update_time = opts.updateTime / 1000

        self.fb = Framebuffer(gain=opts.gain)

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
            while not self.closing_event.is_set():
                self.fb.update_fb()
                await asyncio.sleep(self.update_time)
        except KeyboardInterrupt:
            self.closing_event.set()
