import time
import sched

from PyQt5 import QtCore
import numpy as np


class AutoSave(QtCore.QObject):
    """
    Thread to update time and automatically save the data.
    """

    # Signals to carry the collected data out of the thread.
    finished = QtCore.pyqtSignal()

    def __init__(self, mainWindow):
        QtCore.QThread.__init__(self)

        self.thread_Active = False

        self.histo_Time = 0
        self.elapsed_Time = 0
        self.s1 = None
        self.s2 = None
        self.s1_Event = None
        self.s2_Event = None
        self.s1 = sched.scheduler(time.time, time.sleep)
        self.s2 = sched.scheduler(time.time, time.sleep)

        self.mainWindow = mainWindow
        self.histo_Time = self.mainWindow.ui.histo_Time.text()


    def run(self):
        self.thread_Active = True

        # Clear the data and reset the time to zero
        self.mainWindow.on_Clear_Histogram()
        self.elapsed_Time = 0
        self.histo_Time = int(self.mainWindow.ui.histo_Time.text())
        self.mainWindow.ui.elapsed_Time.setText(f"{self.elapsed_Time}")

        self.event1 = self.s1.enter(self.histo_Time, 2, self.auto_Save)
        self.event2 = self.s1.enter(1, 1, self.update_Seconds)

        self.s1.run()
#        self.s2.run()

    def update_Seconds(self):
#        print(f"update_Seconds - elapsed_Time : {self.elapsed_Time}")
        self.elapsed_Time += 1
        self.mainWindow.ui.elapsed_Time.setText(f"{self.elapsed_Time}")
        self.event2 = self.s1.enter(1, 1, self.update_Seconds)

    def auto_Save(self):
        # Set the file name as current time in folder named by current date
        filename = time.strftime("%Y-%m-%d/%H-%M-%S.csv", time.localtime())
        # self.ui.output_File.text()
        print(f"auto_save excuted, histo_Time is {self.histo_Time}")
        self.mainWindow.ui.output_File.setText(filename)
        self.mainWindow.on_Save_Histo(filename)
        self.elapsed_Time = 0
        self.event1 = self.s1.enter(self.histo_Time, 2, self.auto_Save)

    def stop(self):
        self.thread_Active = False
        if self.s1:
            if self.event1:
                self.s1.cancel(self.event1)
            if self.event2:
                self.s1.cancel(self.event2)
        self.finished.emit()
