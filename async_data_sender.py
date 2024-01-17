import sys
import asyncio
import logging


class AsyncDataSender:
    def __init__(self, logger, q_mp, closing_event, q_fifo) -> None:
        self.logger = logger
        self.logger.info(f'starting async_data_sender ...')

        self.q_mp = q_mp
        self.closing_event = closing_event
        self.q_fifo = q_fifo

    async def start(self):
        self.logger.info(f'... async_data_sender started')

        try:
            # Make sure the receiver is still running
            while not self.closing_event.is_set():
                # Check if the multiprocess queue is full
                if not self.q_mp.full():
                    # Check if anything is in the queue 
                    if not self.q_fifo.empty():
                        # self.logger.debug(f'q_fifo.qsize: {self.q_fifo.qsize()}')
                        new_data = await self.q_fifo.get()
                        self.q_mp.put(new_data)
                    else:
                        await asyncio.sleep(0)
                else:
                    await asyncio.sleep(0)
        except KeyboardInterrupt:
            self.closing_event.set()