import time

from PyQt5 import QtCore
import numpy as np


class Acq_Thread(QtCore.QThread):
    """
    Thread to get histograms and counts from the picoharp.
    """

    # Signals to carry the collected data out of the thread.
    # Separate for the counts and the histograms so the histogram mode can
    # be easily toggled on/off.
    count_Signal = QtCore.pyqtSignal(int, int)
    plot_Signal = QtCore.pyqtSignal(np.ndarray)
    status_Signal = QtCore.pyqtSignal(str)

    def __init__(self, my_Pharp):
        QtCore.QThread.__init__(self)

        # Flags.
        #Practically the thread will probably remain active whilever
        # the program is running.
        self.thread_Active = True
        # Histogramming starts switched off so that the settings can be
        # changed.
        self.histogram_Active = False
        self.histogram_Paused = False # temporarily stopped for some reason
        # The actual object
        self.my_Pharp = my_Pharp

    def run(self):
        while self.thread_Active:
            # Always get the counts from the device, whether histogramming or
            # not.
            ch0, ch1 = self.my_Pharp.Get_CountRate()
            self.count_Signal.emit(ch0, ch1)
            warnings = self.my_Pharp.Get_Warnings()
            self.status_Signal.emit(warnings)

            if self.histogram_Active and not self.histogram_Paused:
                # If desired, get the histogram data from the device as well.
                histo = self.my_Pharp.Get_A_Histogram()
                self.plot_Signal.emit(np.array(histo, dtype=np.int))
            else:
                # Otherwise wait (roughly) as long as it would have taken for
                # the histogram to have been collected. (otherwise the count
                # rate gets polled too frequently)
                time.sleep(self.my_Pharp.hw_Settings.acq_Time / 1000)

    def stop(self):
        self.thread_Active = False
        self.wait()
