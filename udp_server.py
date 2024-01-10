# udp_server.py
# Aidan Gray
# 12/6/2023
# Aidan Gray
# aidan.gray@idg.jhu.edu
#
#
###############################################################################

from socket import *
import logging
import asyncio
import time
import sys
import argparse
import shlex
from multiprocessing import Process

try:
    import signal
except ImportError:
    signal = None

class AsyncUDPServer:
    def __init__(self, loop, local_ip, port, tdc_dict, ip_dict, opts):
        self.log_level = opts.logLevel
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('ZOD')
        self.logger.setLevel(self.log_level)
        self.q_packet = asyncio.Queue(maxsize=1000)
        self.q_fifo = asyncio.Queue(maxsize=1000)
        self.loop = loop
        self.addr = (local_ip, port)
        self.tdc_dict = tdc_dict
        self.ip_dict = ip_dict
        self.server_task = None

    def startUDP(self):
        if signal is not None:
            self.loop.add_signal_handler(signal.SIGINT, self.loop.stop)
        
        transport, server = self.start_server()
        
        try:
            self.loop.run_forever()
        finally:
            server.close()
            self.loop.close()
    
    async def start_server(self):
        self.logger.debug('UDP Server started')

        class AsyncUDPServerProtocol(asyncio.DatagramProtocol):
            def __init__(self, loop, q_packet, tdc_dict, ip_dict, log_level, logger):
                self.loop = loop
                self.logger = logger
                self.q_packet = q_packet
                self.tdc_dict = tdc_dict
                self.ip_dict = ip_dict
                super().__init__()

            def connection_made(self, transport):
                self.logger.info('UDP Server started')
                self.transport = transport
                peername = self.transport.get_extra_info('peername')
                self.logger.debug(f'Connection made: \'{peername}\'')
                
            def datagram_received(self, data, addr):
                rcv_time = time.time()    
                if addr[0] in self.tdc_dict.values():
                    self.logger.debug(f'DATA: \'{data}\'')
                    self.logger.info(f'SRC: \'{addr}\'' ) 
                    self.logger.info(f'TIME: \'{rcv_time}\'')
                    datagram = (rcv_time, addr, data)
                    asyncio.ensure_future(self.datagram_handler(datagram))

            def error_received(self, exc):
                self.logger.error(f'Error received: \'{exc}\'')

            def connection_lost(self, exc):
                self.logger.warn(f'Connection lost: \'{exc}\'')

            async def datagram_handler(self, dgram): 
                self.loop.create_task(self.enqueue_packet(dgram))

            async def enqueue_packet(self, packet):
                if self.q_packet.full():
                    self.logger.warn(f'Incoming Packet Queue is full')
                else:
                    await self.q_packet.put(packet)

        loop = asyncio.get_event_loop()
        
        s=socket(AF_INET, SOCK_DGRAM)
        s.bind(self.addr)

        protocol = AsyncUDPServerProtocol(
            loop, 
            self.q_packet,
            self.tdc_dict,
            self.ip_dict,
            self.log_level,
            self.logger
            )
        
        return await loop.create_datagram_endpoint(
            lambda: protocol, sock=s)

async def runUDPserverTest(loop, local_ip, port, tdc_dict, ip_dict, opts):
    udp_server = AsyncUDPServer(loop, 
                                local_ip, 
                                port, 
                                tdc_dict, 
                                ip_dict, 
                                opts)
    await asyncio.gather(udp_server.start_server())

def argparser(argv):
    if argv is None:
        argv = sys.argv[1:]
    if isinstance(argv, str):
        argv = shlex.split(argv)

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--logLevel', type=int, default=logging.INFO,
                        help='logging threshold. 10=debug, 20=info, 30=warn')
    opts = parser.parse_args(argv)

    return opts

def main(argv=None):
    opts = argparser(argv)

    LOG_FORMAT = '%(asctime)s.%(msecs)03dZ %(name)-10s %(levelno)s \
        %(filename)s:%(lineno)d %(message)s'
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S", format = LOG_FORMAT)
    logger = logging.getLogger('ZOD')
    logger.setLevel(opts.logLevel)
    logger.info('~~~~~~starting log~~~~~~')

    TDC_0_IP = '192.168.1.10'
    TEST_0_IP = '172.16.0.10'
    TEST_1_IP = '192.168.1.123'
    TEST_2_IP = '172.16.0.171'
    TEST_3_IP = '172.16.1.112'

    local_ip = ''
    port = 60000
    tdc_dict = {
        "tdc_0_ip": TDC_0_IP,
        "test_0_ip": TEST_0_IP,
        "test_1_ip": TEST_1_IP,
        "test_2_ip": TEST_2_IP,
        "test_3_ip": TEST_3_IP,
    }

    ip_dict = {
        TDC_0_IP: "tdc_0_ip",
        TEST_0_IP: "test_0_ip",
        TEST_1_IP: "test_1_ip",
        TEST_2_IP: "test_2_ip",
        TEST_3_IP: "test_3_ip",
    }
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runUDPserverTest(loop, 
                                             local_ip, 
                                             port, 
                                             tdc_dict, 
                                             ip_dict, 
                                             opts))

    try:
        loop.run_forever()    
    except KeyboardInterrupt:
        logger.info('Exiting Program...')
    finally:
        loop.close()
        asyncio.set_event_loop(None)

if __name__ == "__main__":
    p = Process(target=main)
    p.start()
    p.join()
