import time
import sched
import driver
from PyQt5 import QtCore
import numpy as np
import csv



class AutoSave(QtCore.QObject):
    """
    Thread to update time and automatically save the data.
    """

    # Signals to carry the collected data out of the thread.
    finished = QtCore.pyqtSignal()

    def __init__(self, mainWindow):
        QtCore.QObject.__init__(self)

        self.histoTime = 0
        self.elapsedTime = 0
        self.s1 = sched.scheduler(time.time, time.sleep)
        self.event1 = None
        self.event2 = None

        self.communication = {}
        self.MOTCount = 0 # MOT is on when MOTCount is even, and MOT is off when MOTCount is odd.
        self.port = 'COM4'
        self.ch = 0
        self.freqStart = 86.0
        self.freqEnd = 96
        self.freqStep = 0.5
        self.freq = np.arange(self.freqStart, self.freqEnd, self.freqStep).tolist()
        self.currentFreq = self.freqStart

        self.dev = driver.Novatech409B(self.port)
        self.dev.set_freq(self.ch, self.currentFreq)

        self.mainWindow = mainWindow
        self.histoTime = self.mainWindow.ui.histoTime.text()


    def run(self):
        # Clear the data and reset the time to zero
        self.mainWindow.on_Clear_Histogram()
        self.elapsedTime = 0
        self.histoTime = int(self.mainWindow.ui.histoTime.text())
        self.mainWindow.ui.elapsedTime.setText(f"{self.elapsedTime}")

        self.event1 = self.s1.enter(self.histoTime, 2, self.autoSave)
        self.event2 = self.s1.enter(1, 1, self.updateSeconds)

        self.s1.run()

    def updateSeconds(self):
        self.event2 = self.s1.enter(1, 1, self.updateSeconds)
        self.elapsedTime += 1
        self.mainWindow.ui.elapsedTime.setText(f"{self.elapsedTime}")

    def autoSave(self):
        self.event1 = self.s1.enter(self.histoTime, 2, self.autoSave)

        # Set the file name as current time in folder named by current date
        filename = time.strftime("%Y-%m-%d/", time.localtime())
        filename += str(self.currentFreq) + "_MHz_"
        if self.MOTCount == 0:
            filename += "MOT_on.csv"
        elif self.MOTCount == 1:
            filename += "MOT_off.csv"
        self.mainWindow.ui.output_File.setText(filename)
        self.mainWindow.on_Save_Histo(filename)


        self.mainWindow.on_Clear_Histogram()
        self.elapsedTime = 0

        self.toggleMOT()
        if self.MOTCount == 2:
            if self.currentFreq < self.freqEnd:
                self.MOTCount = 0
                self.currentFreq += self.freqStep
                self.dev.set_freq(self.ch, self.currentFreq)
            elif self.currentFreq == self.freqEnd:
                self.stop()


    def stop(self):
        if self.s1 and not self.s1.empty():
            if self.event1:
                self.s1.cancel(self.event1)
                self.event1 = None
            if self.event2:
                self.s1.cancel(self.event2)
                self.event2 = None
        self.finished.emit()

    def toggleMOT(self):
        self.MOTCount += 1
        if self.MOTCount == 1:
            # Now MOT should be turned off.
            self.communication.update({'sequenceName': 'MOT_off.csv'})
        elif self.MOTCount == 2:
            # Now MOT should be turned on.
            self.communication.update({'sequenceName': 'MOT_on.csv'})
        self.writeCommunication()

    def writeCommunication(self, filename = 'communication.csv'):
        with open(filename, 'w') as f:
            w = csv.writer(f)
            for k,v in self.communication.items():
                w.writerow([k,v])
