from PyQt5 import QtCore

import numpy as np
import time


class PlotThread(QtCore.QThread):

    plot_Signal = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, my_Pharp):
        QtCore.QThread.__init__(self)

        self.thread_Active = False
        self.my_Pharp = my_Pharp

    def run(self):
        self.thread_Active = True
        while self.thread_Active:
            histo = self.my_Pharp.Get_A_Histogram()

            self.plot_Signal.emit(np.array(histo, dtype=np.int))
            time.sleep(1)

    def stop(self):
        self.thread_Active = False
        self.wait()
