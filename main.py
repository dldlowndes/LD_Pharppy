"""
GUI for controlling the Picoharp300, choosing settings, visualizing and
exporting histograms.

This script is fairly alpha status at the moment. Comments/questions/requests
are welcome - email david@lownd.es or through github.com/dldlowndes/LD_Pharppy)

Requires: Python 3.7+, Numpy, PyQt5, PyQtGraph.
"""

# pylint: disable=C0103
# pylint: disable=R0902

import logging
import sys

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph

import acq_Thread
from settings_gui import Ui_Settings

import LD_Pharp


class MyWindow(QtWidgets.QMainWindow):
    """
    Window for the UI for the Picoharp program.
    """
    def __init__(self):
        self.logger = logging.getLogger("PHarp")
        logging.basicConfig(level=logging.DEBUG)

        super(MyWindow, self).__init__()
        self.ui = Ui_Settings()
        self.ui.setupUi(self)

        # Has this program ever collected any data (i.e. the plot is in an
        # undefined state) - used to plot the cursors so the plot doesn't go
        # weird in the absence of data.
        self.no_Data = True

        self.Init_Hardware()
        self.Init_UI()
        self.Init_Plot()

        self.apply_Default_Settings()

    def Init_Hardware(self):
        """
        Connect to the actual device (or otherwise...)
        """

        try:
            self.my_Pharp = LD_Pharp.LD_Pharp(0)
        except UnboundLocalError as e:
            self.logger.warning(e)
            # If the dll can't get a device handle, the program falls over,
            # Alert the user and give the option to run the barebones simulator
            # which allows the UI to be explored with some representative data.
            error_Response = QtGui.QMessageBox.question(
                self,
                "Error",
                "No hardware found! Run in simulation mode?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
                )
            if error_Response == QtGui.QMessageBox.Yes:
                # Go get the simulator and launch it.
                import LD_Pharp_Dummy
                self.my_Pharp = LD_Pharp_Dummy.LD_Pharp()
            else:
                # Fall over
                # TODO: Do this gracefully
                raise e

        # The resolutions are all 2**n multiples of the base resolution so
        # get the base resolution from the device and work out all of the
        # resolutions to display in the dropdown box.
        self.base_Resolution = self.my_Pharp.base_Resolution
        self.allowed_Resolutions = [
            self.base_Resolution * (2**n) for n in range(8)
            ]

        # Make the worker thread.
        self.acq_Thread = acq_Thread.Acq_Thread(self.my_Pharp)
        self.acq_Thread.count_Signal.connect(self.on_Count_Signal)
        self.acq_Thread.plot_Signal.connect(self.on_Histo_Signal)
        self.acq_Thread.start()

    def Init_UI(self):
        """
        Populate the UI with default settings and connect the buttons
        to functions.
        """

        for res in self.allowed_Resolutions:
            self.ui.resolution.addItem(f"{res}")
        self.ui.resolution.setCurrentText(f"self.base_Resolution")

        self.ui.filename.setText(f"save_filename.csv")
        self.ui.status.setText("Counting")
        self.current_Options = {}
        self.apply_Default_Settings()
        self.count_Precision = 3

        # Cursor option defaults
        self.ui.option_Cursor.setChecked(True)
        self.cursors_On = self.ui.option_Cursor.isChecked()
        self.ui.option_Deltas.setChecked(True)
        self.deltas_On = self.ui.option_Deltas.isChecked()

        # Connect UI elements to functions
        self.ui.button_ApplySettings.clicked.connect(self.apply_Settings)
        self.ui.button_Defaults.clicked.connect(self.apply_Default_Settings)
        self.ui.button_StartStop.clicked.connect(self.start_Stop)
        self.ui.button_SaveHisto.clicked.connect(self.on_Save_Histo)
        self.ui.button_AutoRange.clicked.connect(self.on_Auto_Range)
        self.ui.option_Cursor.stateChanged.connect(self.on_Cursor_Button)
        self.ui.option_Deltas.stateChanged.connect(self.on_Deltas_Button)
        self.ui.button_ClearDeltas.clicked.connect(self.on_Clear_Deltas)
        self.ui.button_ClearHistogram.clicked.connect(self.on_Clear_Histogram)

    def Init_Plot(self):
        """
        Init the plot widget and containers relating so it.
        """

        self.last_Histogram = np.zeros(65536)

        # Modify the plot window
        self.ui.graph_Widget.plotItem.setLabel("left", "Counts")
        self.ui.graph_Widget.plotItem.setLabel("bottom", "Time", "s")
        self.ui.graph_Widget.plotItem.showGrid(x=True, y=True)
        # self.ui.graph_Widget.plotItem.showButtons() #does this do anything?

        # Fix the plot area before anything else starts, otherwise the auto
        # scaler goes crazy with the cursors.
        self.ui.graph_Widget.plotItem.vb.setLimits(xMin=0,
                                                   yMin=0,
                                                   xMax=1,
                                                   yMax=1)
        self.ui.graph_Widget.plotItem.plot([0.5, 0.5])

        # Connect mouse events to functions
        self.proxy = pyqtgraph.SignalProxy(
            self.ui.graph_Widget.sceneObj.sigMouseMoved,
            rateLimit=60,
            slot=self.on_Mouse_Move
            )
        self.ui.graph_Widget.sceneObj.sigMouseClicked.connect(
            self.on_Graph_Click
            )

        # Keep track of which crosshair should move on the next click.
        self.first_Click = True
        # Last click has to be somewhere so just stick it at the origin.
        # Holds the co-ordinates of the most previous click.
        self.last_Click = QtCore.QPoint(0, 0)

        # Set up crosshairs for markers, one that follows the mouse and two
        # that persist after click (for one click before they move again)
        # TODO: Must be a more elegant/pythonic way to do this?
        self.v_Line = pyqtgraph.InfiniteLine(angle=90, movable=False)
        self.h_Line = pyqtgraph.InfiniteLine(angle=0, movable=False)
        self.v_Line_1 = pyqtgraph.InfiniteLine(angle=90,
                                               movable=False,
                                               pen='r')
        self.h_Line_1 = pyqtgraph.InfiniteLine(angle=0,
                                               movable=False,
                                               pen='r')
        self.v_Line_2 = pyqtgraph.InfiniteLine(angle=90,
                                               movable=False,
                                               pen='g')
        self.h_Line_2 = pyqtgraph.InfiniteLine(angle=0,
                                               movable=False,
                                               pen='g')

        # Unnecessary?
        self.v_Line.setPos(0)
        self.h_Line.setPos(0)
        self.v_Line_1.setPos(0)
        self.h_Line_1.setPos(0)
        self.v_Line_2.setPos(0)
        self.h_Line_2.setPos(0)

    def apply_Settings(self):
        """
        Get the settings from the UI and tell the picoharp to update them.
        """

        # Hardware complains if you push settings while histogram is running,
        # it might lead to it ending up in an undefined state so just forbid
        # sending settings while the histogram is running
        if self.acq_Thread.histogram_Active:
            self.logger.warning("Histogram running, settings not pushed")
        else:
            # Translate desired resolution to a "binning" number. Binning
            # combines histogram bins to reduce the histogram resolution.
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

            self.logger.info(f"Push settings\n {options}")
            self.my_Pharp.Update_Settings(**options)

            # Remember the settings that were last pushed.
            self.current_Options = options

            # If binning (resolution) changes, the histogram x axis labels
            # change. Update this. The max number of bins is 65536, this will
            # be trimmed in the plotting function.
            x_Min = 0
            x_Max = 65536 * self.my_Pharp.resolution
            x_Step = self.my_Pharp.resolution
            self.x_Data = np.arange(x_Min, x_Max, x_Step)
            self.x_Data /= 1e12  # convert to seconds

    def apply_Default_Settings(self):
        """
        Some sensible defaults of the options. Sets the UI elements to the
        defaults and then calls the function that reads them and pushes.
        """
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

        self.logger.info("Reset settings to defaults")
        self.apply_Settings()

    def start_Stop(self):
        """
        Switch modes from counting to histogramming.
        """

        if self.no_Data:
            self.no_Data = False

        if self.acq_Thread.histogram_Active:
            self.logger.info("Stop histogramming")
            self.ui.status.setText("Counting")
            self.acq_Thread.histogram_Active = False
        else:
            self.logger.info("Start histogramming")
            self.on_Clear_Histogram()
            self.ui.status.setText("Histogramming")
            self.acq_Thread.histogram_Active = True

    def on_Count_Signal(self, ch0, ch1):
        """
        Handle the counts when the hardware thread emits them
        """

        self.ui.counts_Ch0.setText(f"{ch0:.{self.count_Precision}E}")
        self.ui.counts_Ch1.setText(f"{ch1:.{self.count_Precision}E}")

    def on_Histo_Signal(self, histogram_Data):
        """
        Handle the hsitogram when the hardware thread emits one.
        """

        # There are 65536 bins, but if (1/sync) is less than (65536*resolution)
        # then there will just be empty bins at the end of the histogram array.
        # Look from the END of the array and find the index of the first non
        # empty bin you find.
        last_Full_Bin = histogram_Data.nonzero()[0][-1]

        # Trim the histogram and labels so the empty bins (that will never
        # fill) are not plotted. Then plot them.
        self.ui.graph_Widget.plot(self.x_Data[:last_Full_Bin],
                                  histogram_Data[:last_Full_Bin],
                                  clear=True)
        # Change the plot limits so that the auto scale doesn't go crazy with
        # the cursors (if they're on) (plus a little margin so the labels show)
        x_Limit = self.x_Data[last_Full_Bin] * 1.05
        y_Limit = histogram_Data.max() * 1.05
        self.ui.graph_Widget.plotItem.vb.setLimits(xMin=0,
                                                   yMin=0,
                                                   xMax=x_Limit,
                                                   yMax=y_Limit)

        if self.no_Data:
            pass
        else:
            if self.cursors_On:
                self.Draw_Cursors()
            if self.deltas_On:
                self.Draw_Deltas()

        # Remember the last histogram, so it can be saved.
        self.last_Histogram = histogram_Data
        self.last_X_Data = self.x_Data

    def Draw_Cursors(self):
        """
        Add a vertical line and a horizontal line to the plot widget. The idea
        is these follow the cursor to help reading the graph
        """

        self.ui.graph_Widget.addItem(self.v_Line, ignoreBounds=False)
        self.ui.graph_Widget.addItem(self.h_Line, ignoreBounds=False)

    def Draw_Deltas(self):
        """
        Cursors that persist on mouse clicks.
        """

        self.ui.graph_Widget.addItem(self.v_Line_1, ignoreBounds=False)
        self.ui.graph_Widget.addItem(self.h_Line_1, ignoreBounds=False)
        self.ui.graph_Widget.addItem(self.v_Line_2, ignoreBounds=False)
        self.ui.graph_Widget.addItem(self.h_Line_2, ignoreBounds=False)

    def Remove_Cursors(self):
        """
        Remove the cursor lines from the plot widget
        """

        self.ui.graph_Widget.removeItem(self.v_Line)
        self.ui.graph_Widget.removeItem(self.h_Line)

    def Remove_Deltas(self):
        """
        Remove the deltas from the plot widget.
        """
        self.ui.graph_Widget.removeItem(self.v_Line_1)
        self.ui.graph_Widget.removeItem(self.h_Line_1)
        self.ui.graph_Widget.removeItem(self.v_Line_2)
        self.ui.graph_Widget.removeItem(self.h_Line_2)

    def on_Save_Histo(self):
        """
        This actually still works when histogramming is running but obviously
        there won't be certainty as to exactly what the histogram looks like.
        """
        # Read the filename box from the UI.
        filename = self.ui.filename.text()

        # Zip the bins and counts together into a structured array so the
        # bins get output as floats and the counts as ints.
        my_Type = [("Bin", np.float), ("Count", np.int)]
        out_Histo = np.empty(self.last_Histogram.shape, dtype=my_Type)
        out_Histo["Bin"] = self.last_X_Data
        out_Histo["Count"] = self.last_Histogram

        np.savetxt(
            filename,
            out_Histo,
            delimiter=", ",
            fmt="%1.6e,%8i",
            )

        self.logger.info(f"Histogram saved as {filename}")

    def on_Auto_Range(self):
        """
        Tell the plot widget to fit the full histogram on the plot.
        """
        # pyqtgraph has our back on this one!
        self.logger.debug("Auto range histogram")
        self.ui.graph_Widget.plotItem.autoBtnClicked()

    def on_Clear_Histogram(self):
        """
        Delete everything in the plot!
        """
        # pyqtgraph has our back on this one too.
        self.logger.debug("Clear histogram")
        self.ui.graph_Widget.plotItem.clear()

    def on_Mouse_Move(self, evt):
        """
        Move the crosshair that follows the mouse to the mouse position.
        """

        vb = self.ui.graph_Widget.plotItem.vb
        coords = vb.mapSceneToView(evt[0])

        self.v_Line.setPos(coords.x())
        self.h_Line.setPos(coords.y())

        self.ui.current_X.setText(f"{coords.x():3E}")
        self.ui.current_Y.setText(f"{coords.y():.0f}")

    def on_Graph_Click(self, evt):
        """
        Put a crosshair on the plot in the click location. There are two
        crosshairs so x and y differences can be calculated between click
        positions. The crosshair that moves alternates and the difference
        is calculated every click.
        """

        vb = self.ui.graph_Widget.plotItem.vb
        coords = vb.mapSceneToView(evt.scenePos())

        if self.first_Click:
            self.first_Click = False
            # print(f"first {coords}")
            self.logger.debug(f"First click at {coords}")
            self.v_Line_1.setPos(coords.x())
            self.h_Line_1.setPos(coords.y())
            self.ui.click_1_X.setText(f"{coords.x():3E}")
            self.ui.click_1_Y.setText(f"{coords.y():.0f}")

        else:
            self.first_Click = True
            # print(f"second {coords}")
            self.logger.debug(f"Second click at {coords}")
            self.v_Line_2.setPos(coords.x())
            self.h_Line_2.setPos(coords.y())
            self.ui.click_2_X.setText(f"{coords.x():3E}")
            self.ui.click_2_Y.setText(f"{coords.y():.0f}")

        self.ui.delta_X.setText(f"{coords.x() - self.last_Click.x():3E}")
        self.ui.delta_Y.setText(f"{coords.y() - self.last_Click.y():.0f}")
        self.last_Click = coords

    def on_Cursor_Button(self):
        """
        Toggle the live cursor on/off
        """
        self.cursors_On = self.ui.option_Cursor.isChecked()

        if self.cursors_On:
            # Redraw the cursor
            self.logger.info("Turn cursor on")
            self.Draw_Cursors()
        else:
            # Remove the cursor
            self.logger.info("Turn cursor off")
            self.Remove_Cursors()

    def on_Deltas_Button(self):
        """
        Toggle the (display) of the cursors that appear on mouse clicks for
        calculating deltas (deltas are still calculated - including new clicks
        so clicking with deltas off and turning them back on will not re-show
        the old deltas)
        """
        self.deltas_On = self.ui.option_Deltas.isChecked()

        if self.deltas_On:
            # Redraw the delta cursors
            self.logger.info("Turn deltas on")
            self.Draw_Deltas()
        else:
            # Remove the delta cursors
            self.logger.info("Turn deltas off")
            self.Remove_Deltas()

    def on_Clear_Deltas(self):
        """
        Get rid of the current displayed deltas cursors without turning off
        the deltas, also resets.
        """
        self.logger.info("Clear deltas")
        self.v_Line_1.setPos(0)
        self.h_Line_1.setPos(0)
        self.v_Line_2.setPos(0)
        self.h_Line_2.setPos(0)

        self.ui.click_1_X.setText(f"{0}")
        self.ui.click_1_Y.setText(f"{0}")
        self.ui.click_2_X.setText(f"{0}")
        self.ui.click_2_Y.setText(f"{0}")
        self.ui.delta_X.setText(f"{0}")
        self.ui.delta_Y.setText(f"{0}")

        self.last_Click = QtCore.QPoint(0, 0)
        self.first_Click = True


app = QtWidgets.QApplication([])

application = MyWindow()

application.show()

sys.exit(app.exec())
