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
from multiprocessing import Process, Queue, Event
from signal import SIGINT, SIGTERM


class AsyncUDPServer:
    def __init__(self, logger, local_ip, port,  q_fifo, 
                 closing_event=None, tdc_dict=None, ip_dict=None):
        self.logger = logger
        self.addr = (local_ip, port)
        self.q_fifo = q_fifo
        self.closing_event = closing_event
        self.tdc_dict = tdc_dict
        self.ip_dict = ip_dict
        
        self.server_task = None

        self.logger.info(f'starting udp_server ...')
            
    async def start_server(self):
        class AsyncUDPServerProtocol(asyncio.DatagramProtocol):
            def __init__(self, logger, loop, q_fifo,
                         closing_event=None, tdc_dict=None, ip_dict=None):
                self.logger = logger
                self.loop = loop
                self.q_fifo = q_fifo
                self.closing_event = closing_event
                self.tdc_dict = tdc_dict
                self.ip_dict = ip_dict

                self.packet_count = 0
                
                super().__init__()

            def connection_made(self, transport):
                self.transport = transport
                self.logger.info('... udp server started')
                
            def datagram_received(self, data, addr):
                rcv_time = time.time()    
                if addr[0] in self.tdc_dict.values():
                    self.logger.debug(f'DATA=\'{data}\'')
                    self.logger.debug(f'SRC=\'{addr}\'' ) 
                    self.logger.debug(f'TIME=\'{rcv_time}\'')
                    datagram = (rcv_time, addr, data)
                    asyncio.ensure_future(self.datagram_handler(datagram))

            def error_received(self, exc):
                self.logger.error(f'Error received: \'{exc}\'')

            def connection_lost(self, exc):
                self.logger.warn(f'Connection lost: \'{exc}\'')

            async def datagram_handler(self, dgram): 
                pkt_timestamp = dgram[0]
                pkt_src_addr = dgram[1]
                pkt_data = dgram[2]
    
                pkt_src = self.ip_dict[pkt_src_addr[0]]
                pkt_count = (pkt_data[3]<<8) + pkt_data[2]
    
                self.logger.debug(f'PACKET_TIMESTAMP: {pkt_timestamp}')
                self.logger.debug(f'PACKET_SOURCE: {pkt_src}')
                self.logger.debug(f'PACKET_COUNT: {pkt_count}')
                
                # Make sure the data is aligned properly and is newest packet            
                if (pkt_data[4] == 0) and pkt_data[5] == 0 and (pkt_count >= self.packet_count):
                    num_photons = (pkt_data[1]<<8) + pkt_data[0]
                    num_photon_bytes = num_photons * 6
                    self.logger.debug(f'NUM_PHOTONS: {num_photons} ({num_photon_bytes}B)')
    
                    if num_photons > 0:
                        # Split the packet into photons (X, Y, P) each consisting of 2 bytes
                        data_photons = pkt_data[6:]
                        photon_list = [data_photons[i:i+6] for i in range(0, num_photon_bytes, 6)]
    
                        p_num = 0
                        for photon in photon_list:                         
                            xA = photon[1] << 8
                            xB = photon[0]
                            yA = photon[3] << 8
                            yB = photon[2]
    
                            x = xA + xB
                            y = yA + yB
                            p = photon[4]
                            self.logger.debug(f'PHOTON: ({x}, {y}, {p})')
                            self.enqueue_fifo((x, y, p))
                            p_num+=1            
                    else:
                        self.logger.debug(f'NO PHOTONS')
                        await asyncio.sleep(0)
                    
                    self.packet_count = pkt_count

            def enqueue_fifo(self, data):
                if self.q_fifo.full():
                    self.logger.warning(f'FIFO Queue is full')
                else:
                    self.q_fifo.put(data)

        loop = asyncio.get_event_loop()
        
        s=socket(AF_INET, SOCK_DGRAM)
        s.bind(self.addr)

        protocol = AsyncUDPServerProtocol(
            self.logger,
            loop, 
            self.q_fifo,
            self.closing_event,
            self.tdc_dict,
            self.ip_dict,
            )
        
        return await loop.create_datagram_endpoint(
            lambda: protocol, sock=s)

async def runUDPserverTest(logger, local_ip, port, q_fifo, closing_event, tdc_dict, ip_dict):
    udp_server = AsyncUDPServer(logger, local_ip, port, q_fifo, closing_event, tdc_dict, ip_dict)
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

def start_processes(logger, local_ip, port, q_fifo, closing_event, tdc_dict, ip_dict):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for signal_enum in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal_enum, loop.stop)
    
    try:
        loop.run_until_complete(runUDPserverTest(
            logger,
            local_ip, 
            port, 
            q_fifo, 
            closing_event, 
            tdc_dict, 
            ip_dict
            ))
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
    
    q_fifo = Queue()
    closing_event = Event()
    p = Process(target=start_processes,
                args=(
                    logger.getChild('udp_server'), 
                    local_ip, 
                    port,
                    q_fifo,
                    closing_event, 
                    tdc_dict, 
                    ip_dict, 
                    )
                )
    p.start()

    try:
        p.join()
    except KeyboardInterrupt:
        logger.warning('!!! stopping udp_server !!!')
    
if __name__ == "__main__":
    main() 
