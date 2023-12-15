import sys, time
import numpy as np
import asyncio
import logging
import argparse
import shlex
from multiprocessing import Process, Pipe, Event

from PyQt6.QtGui import * 
from PyQt6.QtCore import QTimer
from PyQt6 import QtWidgets
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph import GraphicsLayoutWidget

class PyQtGraphTest(GraphicsLayoutWidget):

    def __init__(self, pipe_tail, opts):
        super().__init__()
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        
        self.logger = logging.getLogger('PyQtG')
        self.logger.setLevel(opts.logLevel)
        self.logger.info('~~~~~~starting log~~~~~~')

        self.pipe_tail = pipe_tail
        self.plot_size = opts.plotSize
        self.update_time = opts.updateTime

        pg.setConfigOptions(imageAxisOrder='row-major')

        # Configure plot area
        self.setWindowTitle('Zero-Order Data')
        self.resize(800, 800)
        # self.setBackground(0.85)
        
        # self.label_style = {'color': 0.0, 'font-size': '20pt',}
        # self.tick_font = QtGui.QFont()
        # self.tick_font.setPixelSize(20)
        # self.tick_text_style = {'color': 0.0}
        
        self.plot_tdc_0 = self.addPlot()
        self.img_tdc_0 = pg.ImageItem()
        self.plot_tdc_0.addItem(self.img_tdc_0)

        self.plot_tdc_0.setRange(xRange=(0, self.plot_size-1), yRange=(0, self.plot_size-1))
        # self.setup_tdc_0_plot(self.plot_tdc_0)        

        self.data_tdc_0 = np.zeros(shape=(self.plot_size, self.plot_size), dtype=np.uint8)
        self.img_tdc_0.setImage(self.data_tdc_0)

        # Timer to trigger check for new data and plot updates
        self.update_timer = QTimer()
        self.update_timer.setInterval(self.update_time)
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start()

        
    def setup_tdc_0_plot(self, tmp_plot):
        x_axis = tmp_plot.getAxis('bottom')
        y_axis = tmp_plot.getAxis('left')

        x_axis.setPen(pg.mkPen(0.0, width=3))
        x_axis.setTickFont(self.tick_font)
        x_axis.setTextPen(**self.tick_text_style)
        x_axis.setLabel('X', **self.label_style)

        y_axis.setPen(pg.mkPen(0.0, width=3))
        y_axis.setTickFont(self.tick_font)
        y_axis.setTextPen(**self.tick_text_style)
        y_axis.setLabel('Y', **self.label_style)

    def update_plot(self):
        if self.pipe_tail.poll():
            new_data = self.pipe_tail.recv()
            self.data_tdc_0 = new_data
            self.img_tdc_0.setImage(self.data_tdc_0)

class AsyncDataSender:
    def __init__(self, pipe_head, pipe_tail, closing_event, q_fifo, opts) -> None:
        logging.basicConfig(datefmt = "%Y-%m-%d %H:%M:%S",
                            format = '%(asctime)s.%(msecs)03dZ ' \
                                     '%(name)-10s %(levelno)s ' \
                                     '%(filename)s:%(lineno)d %(message)s')
        self.logger = logging.getLogger('ZPLOT')

        self.pipe_head = pipe_head
        self.pipe_tail = pipe_tail
        self.closing_event = closing_event
        self.q_fifo = q_fifo
        self.plot_size = opts.plotSize

        self.data = np.zeros(shape=(self.plot_size, self.plot_size), dtype=np.uint8)

    async def start(self):
        self.logger.info('AsyncDataSender started')

        # Make sure PyQtGraph Window is still open
        while not self.closing_event.is_set():
            # Check if anything is in the queue 
            if not self.q_fifo.empty():
                new_data = await self.q_fifo.get()
                self.data[new_data[1], new_data[0]] = new_data[2]

                #  Check if the pipe is empty
                if not self.pipe_tail.poll():    
                    self.pipe_head.send(self.data)
            await asyncio.sleep(0.000001)
        
        self.logger.info('PyQtGraph closing_event.is_set()')
        sys.exit(0)

def start_receiver(pipe_tail, opts):
    app = QtWidgets.QApplication(sys.argv)
    window = PyQtGraphTest(pipe_tail, opts)
    window.show()
    app.exec()

# Routine to acquire and serve data
def start_sender(pipe_head, pipe_tail, closing_event, opts):
    data = np.zeros(shape=(opts.plotSize, opts.plotSize), dtype=np.uint8)
    
    while not closing_event.is_set():
        for i in range(1000):
            data[np.random.randint(opts.plotSize), np.random.randint(opts.plotSize)] = np.random.randint(128,256)
        
        if not pipe_tail.poll():
            pipe_head.send(data)
        
        time.sleep(0.000001)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if isinstance(argv, str):
        argv = shlex.split(argv)

    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--logLevel', type=int, default=logging.INFO,
                        help='logging threshold. 10=debug, 20=info, 30=warn')
    parser.add_argument('--plotSize', type=int, default=10,
                        help='plot size (square)')
    parser.add_argument('--updateTime', type=int, default=1,
                        help='plot update time (ms)')
    opts = parser.parse_args(argv)

    # Event to signal closing of the plot window to the other process
    closing_event = Event()
    # Pipe for data transport
    pipe_tail, pipe_head = Pipe(False)
    print("Starting reciever...")
    receiver = Process(target=start_receiver, args=(pipe_tail, opts))
    receiver.start()
    print("Starting sender...")
    sender = Process(target=start_sender, args=(pipe_head, pipe_tail, closing_event, opts))
    sender.start()
    receiver.join()
    print("Waiting for sender to exit...")
    closing_event.set()
    if pipe_tail.poll():
        pipe_tail.recv()
    sender.join()
    print("Processes finished.")
    sys.exit(0)

if __name__ == '__main__':    
    main()