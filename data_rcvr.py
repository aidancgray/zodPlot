import logging
import asyncio
from frame_buffer import Framebuffer

SLEEP_TIME = 0.000001  # for short sleeps at the end of loops

class Plot2FrameBuffer():

    def __init__(self, pipe_tail, closing_event, opts):
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('FB_DISP')
        
        self.pipe_tail = pipe_tail
        self.closing_event = closing_event
        self.update_time = opts.updateTime / 1000

        self.fb = Framebuffer(use_buffer_fb=True)

    async def start_pipe_rcv(self):
        while True:
            if self.pipe_tail.poll():
                new_data = self.pipe_tail.recv()
                self.logger.debug(f"PIPE_TAIL_RECV: {new_data}")
                self.fb.raw_data_to_screen_mono(new_data[0],
                                                new_data[1],
                                                new_data[2],)

            else:
                await asyncio.sleep(SLEEP_TIME)
    
    async def start_fb_plot(self):
        while True:
            self.fb.update_fb()
            await asyncio.sleep(self.update_time)
