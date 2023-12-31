# main.py
# 12/6/2023
# Aidan Gray
# aidan.gray@idg.jhu.edu
#
# udp listen on Port 60000 for .10
###############################################################################

import sys
import time
import asyncio
import netifaces
import logging
import argparse
import shlex
import numpy as np

from multiprocessing import Process, Pipe, Event
from async_data_sender import AsyncDataSender

from data_rcvr import Plot2FrameBuffer

from udp_server import AsyncUDPServer
from packet_handler import packetHandler

TDC_0_IP = '192.168.1.10'
TEST_0_IP = '172.16.1.112'
TEST_1_IP = '192.168.1.123'

def custom_except_hook(loop, context):
    logger = logging.getLogger('ZOD')
    logger.setLevel(logging.WARN)
    
    if repr(context['exception']) == 'SystemExit()':
        logger.debug('Exiting Program...')

async def runDAQ(loop, pipe_head, pipe_tail, closing_event, opts):
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                        format = '%(asctime)s.%(msecs)03dZ ' \
                                 '%(name)-10s %(levelno)s ' \
                                 '%(filename)s:%(lineno)d %(message)s')
    
    logger = logging.getLogger('ZOD')
    logger.setLevel(opts.logLevel)
    logger.info('~~~~~~starting log~~~~~~')

    try:
        local_iP = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
    except:
        local_iP = '192.168.1.123'
    
    port = 60000
    
    tdc_dict = {"tdc_0_ip": TDC_0_IP, 
                "test_0_ip": TEST_0_IP, 
                "test_1_ip": TEST_1_IP,}

    ip_dict = {TDC_0_IP: "tdc_0_ip", 
               TEST_0_IP: "test_0_ip", 
               TEST_1_IP: "test_1_ip",}

    logger.info(f'ZPLOT IP = {local_iP}')
    logger.info(f'TDC_0 IP = {tdc_dict["tdc_0_ip"]}')
    logger.info(f'PORT = {port}')
    
    udp_server = AsyncUDPServer(loop=loop, 
                                local_ip='', 
                                port=port, 
                                tdc_dict=tdc_dict, 
                                ip_dict=ip_dict)
    
    pkt_handler = packetHandler(q_packet=udp_server.q_packet, 
                                q_fifo=udp_server.q_fifo, 
                                ip_dict=ip_dict)
    
    data_sender = AsyncDataSender(pipe_head,
                                  pipe_tail,
                                  closing_event,
                                  udp_server.q_fifo,
                                  opts)

    await asyncio.gather(udp_server.start_server(),
                         pkt_handler.start(),
                         data_sender.start(),)
    
async def run_framebuffer_display(loop, pipe_tail, closing_event, opts):
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                        format = '%(asctime)s.%(msecs)03dZ ' \
                                 '%(name)-10s %(levelno)s ' \
                                 '%(filename)s:%(lineno)d %(message)s')
    
    logger = logging.getLogger('FB_DISP')
    logger.setLevel(opts.logLevel)
    logger.info('~~~~~~starting log~~~~~~')

    plot2FB = Plot2FrameBuffer(pipe_tail, closing_event, opts)
    
    await asyncio.gather(plot2FB.start_pipe_rcv(),
                         )

def start_receiver(pipe_tail, closing_event, opts):
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(custom_except_hook)
    loop.run_until_complete(run_framebuffer_display(loop, pipe_tail, closing_event, opts))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Exiting Program...')
    finally:
        loop.close()
        asyncio.set_event_loop(None)

def start_sender(pipe_head, pipe_tail, closing_event, opts):
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(custom_except_hook)
    loop.run_until_complete(runDAQ(loop, pipe_head, pipe_tail, closing_event, opts))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Exiting Program...')
    finally:
        loop.close()
        asyncio.set_event_loop(None)

def start_processes(opts):
    closing_event = Event()  # Event to signal closing of the receiver to the other process
    
    pipe_tail, pipe_head = Pipe(False)  # Simplex Pipe for data transport
    
    receiver = Process(target=start_receiver, args=(
        pipe_tail, 
        closing_event,
        opts,))
    receiver.start()
    
    sender = Process(target=start_sender, args=(
        pipe_head, 
        pipe_tail, 
        closing_event, 
        opts))
    sender.start()
    
    receiver.join()
    closing_event.set()
    if pipe_tail.poll():
        pipe_tail.recv()
    sender.join()
    
    return 0

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if isinstance(argv, str):
        argv = shlex.split(argv)

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--logLevel', type=int, default=logging.INFO,
                        help='logging threshold. 10=debug, 20=info, 30=warn')
    parser.add_argument('--updateTime', type=int, default=1,
                        help='screen update time (ms)')
    opts = parser.parse_args(argv)
    
    exit_data = start_processes(opts)
    
    sys.exit(exit_data)
    
if __name__ == "__main__":
    main()
