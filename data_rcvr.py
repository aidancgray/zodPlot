import time
import logging
import asyncio
from frame_buffer import Framebuffer


class Plot2FrameBuffer():

    def __init__(self, logger, q_mp, closing_event, opts):
        self.logger = logger
        self.logger.info('starting framebuffer display ...')

        self.q_mp = q_mp
        self.closing_event = closing_event
        self.timer = time.time()
        self.update_time = opts.updateTime / 1000

        self.fb = Framebuffer(use_buffer_fb=True)

    def print_photon_count(self):
        self.logger.info('')
        self.logger.info(f'    total photons: {self.fb.num_photons_total}')
        self.logger.info(f'  current photons: {self.fb.num_photons_current}')
        
    async def start_get_q_mp_data(self):
        self.logger.info('... framebuffer display started')
        try:
            while not self.closing_event.is_set():
                if not self.q_mp.empty():
                    new_data = self.q_mp.get()
                    self.fb.raw_data_to_screen_mono(new_data[0],
                                                    new_data[1],
                                                    new_data[2],
                                                    update=False,)
                await asyncio.sleep(0)

        except KeyboardInterrupt:
            self.closing_event.set()
        finally:
            self.print_photon_count()

    async def start_fb_plot(self):
        try:
            while not self.closing_event.is_set():
                now = time.time()
                # self.logger.info(f'time since update:{now-self.timer}')
                self.timer = now
                self.fb.update_fb()
                await asyncio.sleep(self.update_time)
        except KeyboardInterrupt:
            self.closing_event.set()
