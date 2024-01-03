import sys
import asyncio
import logging

class AsyncDataSender:
    def __init__(self, pipe_head, pipe_tail, closing_event, q_fifo, opts) -> None:
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('ZOD')

        self.pipe_head = pipe_head
        self.pipe_tail = pipe_tail
        self.closing_event = closing_event
        self.q_fifo = q_fifo

    async def start(self):
        self.logger.info('AsyncDataSender started')

        # Make sure the receiver is still running
        while not self.closing_event.is_set():
            #  Check if the pipe is empty
            if not self.pipe_tail.poll():
                # Check if anything is in the queue 
                if not self.q_fifo.empty():
                    new_data = await self.q_fifo.get()
                    self.logger.debug(f'PIPE_HEAD_SEND: {new_data}')
                    self.pipe_head.send(new_data)
            else:
                await asyncio.sleep(0.000001)
        
        self.logger.info('closing_event.is_set()')
        sys.exit(0)