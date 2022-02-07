import time
import sched
from PyQt5 import QtCore
import numpy as np
import csv
import zmq


class AutoSave(QtCore.QObject):
    """
    Worker to update time and automatically save the data.
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


        self.mainWindow = mainWindow
        self.histoTime = self.mainWindow.ui.histoTime.text()
        self.context = zmq.Context()
        #  Socket to talk to server
        print("Connecting to exp-control server...")
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

        self.isLast = False

    def run(self):
        # Clear the data and reset the time to zero
        self.isLast = False
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

        # Make directory named by current date
        # filename = time.strftime("%Y-%m-%d/", time.localtime())
        # Communicate with exp-control program and get the filename according to the previous parameters
        self.mainWindow.on_Save_Histo(self.mainWindow.ui.data_Filename.text())
        filename = self.send_and_receive()
        self.mainWindow.ui.output_File.setText(filename)
        self.mainWindow.on_Save_Histo(filename)

        if self.isLast:
            self.stop()
            return

        time.sleep(2) # Wait for two seconds to give some time to exp-control for pausing, updating, and restarting.
        self.mainWindow.on_Clear_Histogram() # clear and restart histogramming
        self.event1 = self.s1.enter(self.histoTime, 2, self.autoSave) # Enter next autosave event
        self.elapsedTime = 0


    def stop(self):
        if self.s1 and not self.s1.empty():
            if self.event1 and self.event1 in self.s1.queue:
                self.s1.cancel(self.event1)
                self.event1 = None
            if self.event2 and self.event2 in self.s1.queue:
                self.s1.cancel(self.event2)
                self.event2 = None
        self.finished.emit()

    def send_and_receive(self):

        # Send dummy message
        self.socket.send_string("pico-control: dummy message...")
        # Get the reply.
        # message is in the format: filename(,end)
        message = self.socket.recv().decode('utf-8')
        pair = message.split(',')
        if len(pair) > 1:
            if pair[1] == 'end':
                self.isLast = True
        print(f"Received reply [ {message} ]")

        return pair[0]
