import sys
import asyncio
import logging

SLEEP_TIME = 0.000001  # for short sleeps at the end of loops

class AsyncDataSender:
    def __init__(self, q_mp, closing_event, q_fifo, opts) -> None:
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('DAQ')
        self.logger.setLevel(opts.logLevel)
        self.q_mp = q_mp
        self.closing_event = closing_event
        self.q_fifo = q_fifo

    async def start(self):
        self.logger.info('AsyncDataSender started')

        try:
            # Make sure the receiver is still running
            while not self.closing_event.is_set():
                # Check if the multiprocess queue is full
                if not self.q_mp.full():
                    # Check if anything is in the queue 
                    if not self.q_fifo.empty():
                        new_data = await self.q_fifo.get()
                        self.logger.debug(f'Q_MP.PUT(): {new_data}')
                        self.q_mp.put(new_data)
                    else:
                        await asyncio.sleep(SLEEP_TIME)
                else:
                    await asyncio.sleep(SLEEP_TIME)
        except KeyboardInterrupt:
            self.closing_event.set()