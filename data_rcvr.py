import logging
import asyncio
from frame_buffer import Framebuffer

SLEEP_TIME = 0.000001  # for short sleeps at the end of loops

class Plot2FrameBuffer():

    def __init__(self, q_mp, closing_event, opts):
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('FB_DISP')
        
        self.q_mp = q_mp
        self.closing_event = closing_event
        self.update_time = opts.updateTime / 1000

        self.fb = Framebuffer(use_buffer_fb=True)

    def print_photon_count(self):
        self.logger.info(f'  total photons: {self.fb.num_photons_total}')
        self.logger.info(f'current photons: {self.fb.num_photons_current}')

    async def start_get_q_mp_data(self):
        try:
            while not self.closing_event.is_set():
                if not self.q_mp.empty():
                    new_data = self.q_mp.get()
                    self.logger.debug(f"q_mp.get(): {new_data}")
                    self.fb.raw_data_to_screen_mono(new_data[0],
                                                    new_data[1],
                                                    new_data[2],
                                                    update=False,)
                else:
                    await asyncio.sleep(SLEEP_TIME)
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
