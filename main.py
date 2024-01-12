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

from signal import SIGINT, SIGTERM
from multiprocessing import Process, Queue, Event

from async_data_sender import AsyncDataSender

from data_rcvr import Plot2FrameBuffer

from udp_server import AsyncUDPServer
from packet_handler import packetHandler

TDC_0_IP = '192.168.1.10'
TEST_0_IP = '172.16.0.10'
TEST_1_IP = '192.168.1.123'
TEST_2_IP = '172.16.0.171'
TEST_3_IP = '172.16.1.112'

async def runDAQ(q_mp, closing_event, opts):
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                        format = '%(asctime)s.%(msecs)03dZ ' \
                                 '%(name)-10s %(levelno)s ' \
                                 '%(filename)s:%(lineno)d %(message)s')
    
    logger = logging.getLogger('DAQ')
    logger.setLevel(opts.logLevel)
    logger.info('~~~~~~ starting data acquisition ~~~~~~')

    try:
        local_ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
    except:
        local_ip = '192.168.1.123'
    
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

    logger.info(f'ZPLOT IP = {local_ip}')
    logger.info(f'TDC_0 IP = {tdc_dict["tdc_0_ip"]}')
    logger.info(f'PORT = {port}')

    udp_server = AsyncUDPServer(local_ip='', 
                                port=port, 
                                tdc_dict=tdc_dict, 
                                ip_dict=ip_dict,
                                opts=opts)
    
    pkt_handler = packetHandler(q_packet=udp_server.q_packet, 
                                q_fifo=udp_server.q_fifo, 
                                ip_dict=ip_dict)
    
    data_sender = AsyncDataSender(q_mp,
                                  closing_event,
                                  udp_server.q_fifo,
                                  opts)

    await asyncio.gather(udp_server.start_server(), 
                         pkt_handler.start(), 
                         data_sender.start(),)
    
async def run_framebuffer_display(q_mp, closing_event, opts):
    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                        format = '%(asctime)s.%(msecs)03dZ ' \
                                 '%(name)-10s %(levelno)s ' \
                                 '%(filename)s:%(lineno)d %(message)s')
    
    logger = logging.getLogger('FB_DISP')
    logger.setLevel(opts.logLevel)
    logger.info('~~~~~~ starting framebuffer display ~~~~~~')

    plot2FB = Plot2FrameBuffer(q_mp, closing_event, opts)
    
    await asyncio.gather(plot2FB.start_get_q_mp_data(), plot2FB.start_fb_plot())

def start_receiver(q_mp, closing_event, opts):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for signal_enum in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal_enum, loop.stop)

    try:
        loop.run_until_complete(run_framebuffer_display(q_mp, closing_event, opts))
        loop.run_forever()
    except RuntimeError as exc:
        print(exc)
    finally:
        loop.close()
        asyncio.set_event_loop(None)

def start_sender(q_mp, closing_event, opts):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for signal_enum in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal_enum, loop.stop)

    try:
        loop.run_until_complete(runDAQ(q_mp, closing_event, opts))
        loop.run_forever()
    except RuntimeError as exc:
        print(exc)
    finally:
        loop.close()
        asyncio.set_event_loop(None)

def argparser(argv):
    if argv is None:
        argv = sys.argv[1:]
    if isinstance(argv, str):
        argv = shlex.split(argv)

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--logLevel', type=int, default=logging.INFO,
                        help='logging threshold. 10=debug, 20=info, 30=warn')
    parser.add_argument('--updateTime', type=int, default=1000,
                        help='screen update time (ms)')
    opts = parser.parse_args(argv)

    return opts

def main(argv=None):
    opts = argparser(argv)    

    logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                        format = '%(asctime)s.%(msecs)03dZ ' \
                                 '%(name)-10s %(levelno)s ' \
                                 '%(filename)s:%(lineno)d %(message)s')
    
    logger = logging.getLogger('ZODPLOT')
    logger.setLevel(opts.logLevel)

    closing_event = Event()  # Event to signal closing of the receiver to the other process
    
    q_mp = Queue(maxsize=0)

    receiver = Process(target=start_receiver, args=(
        q_mp, 
        closing_event,
        opts,))
    receiver.start()
    
    sender = Process(target=start_sender, args=(
        q_mp, 
        closing_event, 
        opts))
    sender.start()
    
    try:
        receiver.join()
        sender.join()
    except KeyboardInterrupt:
        closing_event.set()
        logger.info('~~~~~~ stopping zodPlot main process ~~~~~~')

if __name__ == "__main__":
    main()
