# packet_handler.py
# 12/6/2023
# Aidan Gray
# aidan.gray@idg.jhu.edu
#
#
###############################################################################

import logging
import asyncio

SLEEP_TIME = 0.000001  # for short sleeps at the end of loops

class packetHandler:
    def __init__(self, q_packet, q_fifo, ip_dict):
        self.logger = logging.getLogger('ZPLOT')
        self.q_packet = q_packet
        self.q_fifo = q_fifo
        self.ip_dict = ip_dict
        self.packet_count = 0

    async def start(self):
        while True:
            if not self.q_packet.empty():
                pkt = await self.q_packet.get()
                await self.handlePacket(pkt)
            await asyncio.sleep(SLEEP_TIME)

    async def handlePacket(self, pkt):
        try:
            pkt_timestamp = pkt[0]
            pkt_src_addr = pkt[1]
            pkt_data = pkt[2]

            pkt_src = self.ip_dict[pkt_src_addr[0]]
            pkt_count = (pkt_data[3]<<8) + pkt_data[2]

            self.logger.debug(f'PACKET_TIMESTAMP: {pkt_timestamp}')
            self.logger.debug(f'PACKET_SOURCE: {pkt_src}')
            self.logger.debug(f'PACKET_COUNT: {pkt_count}')
            
            # await self.enqueue_fifo((pkt_src, pkt_timestamp))

            # Make sure the data is aligned properly and is newest packet            
            if (pkt_data[4] == 0) and pkt_data[5] == 0 and (pkt_count > self.packet_count):
                num_photons = (pkt_data[1]<<8) + pkt_data[0]
                num_photon_bytes = num_photons * 6
                self.logger.debug(f'NUM_PHOTONS: {num_photons} ({num_photon_bytes}B)')

                if num_photons > 0:
                    # Split the packet into photons (X, Y, P) each consisting of 2 bytes
                    data_photons = pkt_data[6:]
                    photon_list = [data_photons[i:i+6] for i in range(0, num_photon_bytes, 6)]

                    p_num = 0
                    for photon in photon_list:
                        self.logger.debug(f'PHOTON[{p_num}]: ' \
                                          f'{photon[0:1].hex()} {photon[1:2].hex()} ' \
                                          f'{photon[2:3].hex()} {photon[3:4].hex()} ' \
                                          f'{photon[4:5].hex()} {photon[5:6].hex()}')
                        
                        xA = (photon[1] & 63) << 8
                        xB = photon[0]
                        yA = (photon[3] & 63) << 8
                        yB = photon[2]

                        x = xA + xB
                        y = yA + yB
                        p = photon[4]
                        
                        self.logger.debug(f'x={xA}+{xB} = {x}')
                        self.logger.debug(f'y={yA}+{yB} = {y}')
                        self.logger.debug(f'p={p}')

                        await self.enqueue_fifo((x, y, p))
                        p_num+=1            
                else:
                    self.logger.debug(f'NO PHOTONS')
                    await asyncio.sleep(SLEEP_TIME)

        except Exception as e:
            self.logger.error(e)
            pass

    async def enqueue_fifo(self, data):
        if self.q_fifo.full():
            self.logger.warn(f'Transmit Data Queue is FULL')
        else:
            await self.q_fifo.put(data)

async def runPktHandlerTest(loop):
    pkt_handler = packetHandler(q_packet=asyncio.Queue(),
                                q_fifo=asyncio.Queue())
    
    test_pkt_0 = b'\x08\x00\x02\x00\x00\x00'
    test_pkt_1 = b'\xe3\x15\x57\x0a\x83\x00'
    test_pkt_2 = b'\x16\x30\xad\x1a\xa1\x00'
    test_pkt_3 = b'\x65\x06\x00\x09\xff\x00'
    test_pkt_4 = b'\x95\x26\x2c\x2d\x99\x00'
    test_pkt_5 = b'\xaa\x24\xf7\x2f\x92\x00'
    test_pkt_6 = b'\x55\x07\xad\x0c\x42\x00'
    test_pkt_7 = b'\x47\x13\xf2\x16\xe0\x00'
    test_pkt_8 = b'\x2a\x2d\x57\x08\xb6\x00'
    
    test_pkt = test_pkt_0 + test_pkt_1 + test_pkt_2 + test_pkt_3 + test_pkt_4 + test_pkt_5 + test_pkt_6 + test_pkt_7 + test_pkt_8 
    
    await pkt_handler.handlePacket(test_pkt)

    #await asyncio.gather(pktHandler.start())

if __name__ == "__main__":
    LOG_FORMAT = '%(asctime)s.%(msecs)03dZ %(name)-10s %(levelno)s \
        %(filename)s:%(lineno)d %(message)s'
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S", format = LOG_FORMAT)
    logger = logging.getLogger('ZPLOT')
    logger.setLevel(logging.DEBUG)
    logger.debug('~~~~~~starting log~~~~~~')

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(runPktHandlerTest(loop))
    except KeyboardInterrupt:
        print('Exiting Program...')