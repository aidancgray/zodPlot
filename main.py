# main.py
# 12/6/2023
# Aidan Gray
# aidan.gray@idg.jhu.edu
#
# udp listen on Port 60000 for *.*.*.10
###############################################################################

import sys, os
import asyncio
import netifaces
import logging
import argparse
import shlex
import numpy as np
import pigpio as gpio

from signal import SIGINT, SIGTERM
from multiprocessing import Process, Queue, Event

from data_rcvr import Plot2FrameBuffer
from udp_server import AsyncUDPServer


LOGGER_NAME = 'zod_plot'
GPIO_MAP = {
    'clear': 21,
    'screenshot': 20,
    'enc_lo': 26,
    'enc_hi': 19,
    'enc_switch': 13,
}

TDC_0_IP = '192.168.1.10'
TEST_0_IP = '172.16.0.10'
TEST_1_IP = '192.168.1.123'
TEST_2_IP = '172.16.0.171'
TEST_3_IP = '172.16.1.112'

async def runDAQ(q_mp, closing_event):
    logger = logging.getLogger(LOGGER_NAME)

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

    udp_server = AsyncUDPServer(logger.getChild('udp_server'),
                                '', 
                                port,
                                q_mp,
                                closing_event, 
                                tdc_dict, 
                                ip_dict)
    
    await asyncio.gather(udp_server.start_server()) 
    
async def run_framebuffer_display(q_mp, closing_event, opts):
    logger = logging.getLogger(LOGGER_NAME)

    plot2FB = Plot2FrameBuffer(logger.getChild('fb_display'), 
                               q_mp, 
                               closing_event, 
                               GPIO_MAP,
                               opts,)
    
    await asyncio.gather(plot2FB.start_get_q_mp_data(), 
                         plot2FB.start_fb_plot())

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

def start_sender(q_mp, closing_event):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for signal_enum in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal_enum, loop.stop)

    try:
        loop.run_until_complete(runDAQ(q_mp, closing_event))
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
    parser.add_argument('--gain', type=int, default=1,
                        help='gain to increase photon brightness per pixel. \
                            A value of 18718 would use the original photon value.')
    parser.add_argument('--imgLog', type=str, default=f'/home/{os.getlogin()}/imgs/',
                        help='path to the screenshots')
    opts = parser.parse_args(argv)

    return opts

def main(argv=None):
    opts = argparser(argv)    

    # create logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(opts.logLevel)
    # create stream handler
    con_hdlr = logging.StreamHandler()
    con_hdlr.setLevel(opts.logLevel)
    # create formatter and add to handler
    log_format = '%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s'
    log_formatter = logging.Formatter(datefmt = '%Y-%m-%d | %H:%M:%S',
                                      fmt = log_format)
    con_hdlr.setFormatter(log_formatter)
    # add handler to logger
    logger.addHandler(con_hdlr)

    

    closing_event = Event()  # Event to signal closing of the receiver to the other process
    reset_event = Event()  # Event to signal the press of the reset button

    q_mp = Queue(maxsize=0)

    receiver = Process(target=start_receiver, args=(q_mp, closing_event, opts))
    sender = Process(target=start_sender, args=(q_mp, closing_event))
    # interrupter = Process(target=start_interrupter, args=(closing_event, reset_event))
    
    receiver.start()
    sender.start()
    # interrupter.start()

    try:
        receiver.join()
        sender.join()
        # interrupter.join()
    except KeyboardInterrupt:
        closing_event.set()
        logger.info('~~~~~~ stopping zodPlot main process ~~~~~~')

if __name__ == "__main__":
    main()
