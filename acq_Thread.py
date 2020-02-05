import time

from PyQt5 import QtCore
import numpy as np


class Acq_Thread(QtCore.QThread):
    """
    Thread to get histograms and counts from the picoharp.
    """

    count_Signal = QtCore.pyqtSignal(int, int)
    plot_Signal = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, my_Pharp):
        QtCore.QThread.__init__(self)

        self.thread_Active = True
        self.histogram_Active = False
        self.my_Pharp = my_Pharp

    def run(self):
        while self.thread_Active:
            ch0, ch1 = self.my_Pharp.Get_CountRate()
            self.count_Signal.emit(ch0, ch1)

            if self.histogram_Active:
                histo = self.my_Pharp.Get_A_Histogram()
                self.plot_Signal.emit(np.array(histo, dtype=np.int))
            else:
                time.sleep(self.my_Pharp.options["acq_Time"] / 1000)

    def stop(self):
        self.thread_Active = False
        self.wait()
