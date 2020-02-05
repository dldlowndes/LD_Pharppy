import numpy as np
from PyQt5 import QtWidgets
import sys

import counter
import plotter
from settings_gui import Ui_Settings

import LD_Pharp

""" TODO List:
    Option to disable ClearHistMem() for cumulative histograms
    Interact with plot via settings window. (live?)
    Grey out settings boxes when histogramming is running
        Or at least have settings not try to update.
    Auto scale with window size!
    To be honest, counter and plotter probably don't need to be separate
        Combine them into one thing. If possible without duplicate code.
    Add a fitted gaussian (optionally other shapes?) onto plot
        and display statistics
"""


class my_Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(my_Window, self).__init__()
        self.ui = Ui_Settings()
        self.ui.setupUi(self)

        self.my_Pharp = LD_Pharp.LD_Pharp(0)

        self.base_Resolution = self.my_Pharp.base_Resolution
        allowed_Resolutions = [self.base_Resolution * (2**n) for n in range(8)]
        for i, res in enumerate(allowed_Resolutions):
            self.ui.resolution.addItem(f"{res}")
        self.ui.resolution.setCurrentText(f"self.base_Resolution")

        # Connect UI elements to functions
        self.ui.button_ApplySettings.clicked.connect(self.apply_Settings)
        self.ui.button_Defaults.clicked.connect(self.default_Settings)
        self.ui.button_StartStop.clicked.connect(self.start_Stop)
        self.ui.button_SaveHisto.clicked.connect(self.on_Save_Histo)
        self.ui.button_AutoRange.clicked.connect(self.on_Auto_Range)

        # Modify the plot window
        self.ui.graph_Widget.plotItem.setLabel("left", "Counts")
        self.ui.graph_Widget.plotItem.setLabel("bottom", "Time", "s")
        self.ui.graph_Widget.plotItem.showGrid(x=True, y=True)
        self.ui.graph_Widget.plotItem.showButtons()
        # self.ui.graph_Widget.plotItem.

        self.ui.filename.setText(f"save_filename.csv")

        # Set up some default settings.
        self.histogram_Running = False
        self.current_Options = {}
        self.default_Settings()

        # Make some threads to do work.
        self.counter = counter.CountThread(self.my_Pharp)
        self.counter.count_Signal.connect(self.on_Count_Signal)

        self.plotter = plotter.PlotThread(self.my_Pharp)
        self.plotter.plot_Signal.connect(self.on_Histo_Signal)

        # Start the counter thread
        self.counter.start()

    def apply_Settings(self):
        if self.histogram_Running:
            print("Settings not pushed, histogram is running")
        else:
            resolution_Req = self.ui.resolution.currentText()
            binning = np.log2(float(resolution_Req) / self.base_Resolution)

            options = {
                    "binning": int(binning),
                    "sync_Offset": int(self.ui.sync_Offset.value()),
                    "sync_Divider": int(self.ui.sync_Divider.currentText()),
                    "CFD0_ZeroCross": int(self.ui.CFD0_Zerocross.value()),
                    "CFD0_Level": int(self.ui.CFD0_Level.value()),
                    "CFD1_ZeroCross": int(self.ui.CFD1_Zerocross.value()),
                    "CFD1_Level": int(self.ui.CFD1_Level.value()),
                    "acq_Time": int(self.ui.acq_Time.value())
                    }

            print(options)
            self.my_Pharp.Update_Settings(**options)

            self.current_Options = options

            x_Min = 0
            x_Max = 65536 * self.my_Pharp.resolution
            x_Step = self.my_Pharp.resolution
            self.x_Data = np.arange(x_Min, x_Max, x_Step)
            self.x_Data /= 1e12  # convert to seconds

    def default_Settings(self):
        default_Options = {
                "binning": 0,
                "sync_Offset": 0,
                "sync_Divider": 1,
                "CFD0_ZeroCross": 10,
                "CFD0_Level": 50,
                "CFD1_ZeroCross": 10,
                "CFD1_Level": 50,
                "acq_Time": 500
                }

        binning = default_Options["binning"]
        resolution = self.base_Resolution * (2 ** binning)

        self.ui.resolution.setCurrentText(f"{resolution}")
        self.ui.sync_Offset.setValue(default_Options["sync_Offset"])
        self.ui.sync_Divider.setCurrentText(
                str(default_Options["sync_Divider"]))
        self.ui.CFD0_Level.setValue(default_Options["CFD0_Level"])
        self.ui.CFD0_Zerocross.setValue(default_Options["CFD0_ZeroCross"])
        self.ui.CFD1_Level.setValue(default_Options["CFD1_Level"])
        self.ui.CFD1_Zerocross.setValue(default_Options["CFD1_ZeroCross"])
        self.ui.acq_Time.setValue(default_Options["acq_Time"])

        self.apply_Settings()

    def start_Stop(self):
        # Switch modes from counting to histogramming.
        if self.histogram_Running:
            print("Stop histo")
            self.histogram_Running = False
            self.plotter.stop()
            self.counter.start()

        else:
            print("Start histo")
            self.ui.counts_Ch0.setText("---")
            self.ui.counts_Ch1.setText("---")
            self.histogram_Running = True
            self.counter.stop()
            self.plotter.start()

    def on_Count_Signal(self, ch0, ch1):
        self.ui.counts_Ch0.setText(f"{ch0:.2E}")
        self.ui.counts_Ch1.setText(f"{ch1:.2E}")

    def on_Histo_Signal(self, ch0, ch1, histogram_Data):
        self.ui.counts_Ch0.setText(f"{ch0:.2E}")
        self.ui.counts_Ch1.setText(f"{ch1:.2E}")

        last_Full_Bin = histogram_Data.nonzero()[0][-1]

        self.ui.graph_Widget.plot(self.x_Data[:last_Full_Bin],
                                  histogram_Data[:last_Full_Bin],
                                  clear=True)
        self.last_Histogram = histogram_Data

    def on_Save_Histo(self):
        filename = self.ui.filename.text()

        np.savetxt(filename,
                   self.last_Histogram,
                   delimiter=", "
                   )

    def on_Auto_Range(self):
        self.ui.graph_Widget.plotItem.autoBtnClicked()


app = QtWidgets.QApplication([])

application = my_Window()

application.show()

sys.exit(app.exec())
