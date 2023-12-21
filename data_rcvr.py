import time
import logging
import asyncio
from frame_buffer import Framebuffer

class Plot2FrameBuffer():

    def __init__(self, pipe_tail, closing_event, opts):
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('FB_DISP')
        
        self.pipe_tail = pipe_tail
        self.closing_event = closing_event
        self.update_time = opts.updateTime

        self.fb = Framebuffer()

    async def start(self):
        while True:
            if self.pipe_tail.poll():
                new_data = self.pipe_tail.recv()
                self.logger.debug(f"PIPE_TAIL_RECV: {new_data}")
            await asyncio.sleep(self.update_time)