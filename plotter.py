from PyQt5 import QtCore

import numpy as np
import time


class PlotThread(QtCore.QThread):

    plot_Signal = QtCore.pyqtSignal(int, int, np.ndarray)

    def __init__(self, my_Pharp):
        QtCore.QThread.__init__(self)

        self.thread_Active = False
        self.my_Pharp = my_Pharp

    def run(self):
        self.thread_Active = True
        while self.thread_Active:
            histo = self.my_Pharp.Get_A_Histogram()
            ch0, ch1 = self.my_Pharp.Get_CountRate()
            self.plot_Signal.emit(ch0, ch1, np.array(histo, dtype=np.int))

    def stop(self):
        self.thread_Active = False
        self.wait()
