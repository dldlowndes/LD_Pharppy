from PyQt5 import QtCore

import random
import time


class CountThread(QtCore.QThread):

    count_Signal = QtCore.pyqtSignal(int, int)

    def __init__(self, my_Pharp):
        QtCore.QThread.__init__(self)

        self.thread_Active = True
        self.my_Pharp = my_Pharp

    def run(self):
        self.thread_Active = True
        while self.thread_Active:
            counts0, counts1 = self.my_Pharp.Get_CountRate()

            self.count_Signal.emit(counts0, counts1)
            time.sleep(1)

    def stop(self):
        self.thread_Active = False
        self.wait()
