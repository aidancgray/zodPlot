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
from signal import SIGINT, SIGTERM


class AsyncUDPServer:
    def __init__(self, logger, local_ip, port, tdc_dict, ip_dict):
        self.logger = logger
        self.q_packet = asyncio.Queue()
        self.q_fifo = asyncio.Queue()
        self.addr = (local_ip, port)
        self.tdc_dict = tdc_dict
        self.ip_dict = ip_dict
        self.server_task = None
        self.logger.info(f'starting udp_server ...')

            
    async def start_server(self):

        class AsyncUDPServerProtocol(asyncio.DatagramProtocol):
            def __init__(self, logger, loop, q_packet, tdc_dict, ip_dict):
                self.logger = logger
                self.loop = loop
                self.q_packet = q_packet
                self.tdc_dict = tdc_dict
                self.ip_dict = ip_dict
                super().__init__()

            def connection_made(self, transport):
                self.transport = transport
                self.logger.info('... udp server started')
                
            def datagram_received(self, data, addr):
                rcv_time = time.time()    
                if addr[0] in self.tdc_dict.values():
                    self.logger.debug(f'DATA: \'{data}\'')
                    self.logger.debug(f'SRC: \'{addr}\'' ) 
                    self.logger.debug(f'TIME: \'{rcv_time}\'')
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
            self.logger,
            loop, 
            self.q_packet,
            self.tdc_dict,
            self.ip_dict,
            )
        
        return await loop.create_datagram_endpoint(
            lambda: protocol, sock=s)

async def runUDPserverTest(local_ip, port, tdc_dict, ip_dict, opts):
    udp_server = AsyncUDPServer(local_ip, port, tdc_dict, ip_dict, opts)
    task_ret = await asyncio.gather(udp_server.start_server())

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

def start_processes(logger, local_ip, port, tdc_dict, ip_dict, opts):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for signal_enum in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal_enum, loop.stop)
    
    try:
        loop.run_until_complete(runUDPserverTest(local_ip, port, tdc_dict, ip_dict, opts))
        # asyncio.run(runUDPserverTest(local_ip, port, tdc_dict, ip_dict, opts))
        loop.run_forever()
    except RuntimeError as exc:
        logger.info(exc)
    finally:
        loop.close()
        asyncio.set_event_loop(None)

def main(argv=None):
    opts = argparser(argv)

    LOG_FORMAT = '%(asctime)s.%(msecs)03dZ %(name)-10s %(levelno)s \
        %(filename)s:%(lineno)d %(message)s'
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S", format = LOG_FORMAT)
    logger = logging.getLogger('DAQ')
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
    
    p = Process(target=start_processes,
                args=(logger, 
                      local_ip, 
                      port, 
                      tdc_dict, 
                      ip_dict, 
                      opts))
    p.start()
    try:
        p.join()
    except KeyboardInterrupt:
        logger.info('~~~~~~ stopping udp_server ~~~~~~')
    
if __name__ == "__main__":
    main() 
