"""
GUI for controlling the Picoharp300, choosing settings, visualizing and
exporting histograms.

This script is fairly alpha status at the moment. Comments/questions/requests
are welcome - email david@lownd.es or through github.com/dldlowndes/LD_Pharppy)

Requires: Python 3.7+, Numpy, PyQt5, PyQtGraph.

TODO list:
    Disable settings button when data is running (doesn't work anyway)
    Give option to specify DLL path on FileNotFoundError when starting
    Use click number to index lists in on_Graph_Click
    Add horizontal lines in integration mode (max? mean? both?)
    Add dynamic number of delta/integration cursors instead of 2/4 respectively
    Investigate getting this to work with other hardware...
    py2exe or something for distribution
    Read and print warnings (counts too high etc)
    Curve fitting/FWHM estimate.
    Cumulative histograms
    Option to update width on already placed integrals (two buttons)
    Add ratios comparison between integral values (normalize to this checkbox?)
"""

# pylint: disable=C0103
# pylint: disable=R0902
# pylint: disable=R0904
# pylint: disable=W0511
# pylint: disable=W1203

import itertools
import logging
import sys

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph

import acq_Thread
import settings_gui
import LD_Pharp
import LD_Pharp_Dummy

# So this works nicely on my Surface.
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

class MyWindow(QtWidgets.QMainWindow):
    """
    Window for the UI for the Picoharp program.
    """
    def __init__(self):
        self.logger = logging.getLogger("PHarp")
        logging.basicConfig(level=logging.DEBUG)

        super().__init__()
        self.ui = settings_gui.Ui_MainWindow()
        self.ui.setupUi(self)

        # Has this program ever collected any data (i.e. the plot is in an
        # undefined state) - used to plot the cursors so the plot doesn't go
        # weird in the absence of data.
        self.no_Data = True

        # Number of DPs to round counts data to.
        self.count_Precision = 3

        # Dict to lookup the angles for H and V oriented lines on the plot.
        self.orientations = {"h": 0, "v": 90}

        # Define hardware info members, then init them (and the hardware)
        self.my_Pharp = None
        self.base_Resolution = None
        self.allowed_Resolutions = None
        self.Init_Hardware()

        # Members involved with UI, then init them (and the UI)
        self.integral_Coords = []
        self.integral_Values = ()
        self.cursors_On = None
        self.deltas_On = None
        self.integrals_On = None
        self.current_Options = None
        self.Init_UI()

        # Members involved with plotting, then init them (and the plots)
        self.this_Data = None
        self.x_Data = None
        self.last_Histogram = None
        self.last_X_Data = None
        self.click_Number = 0
        self.last_Click = None
        self.Init_Plot()

        # Send some default settings to the Picoharp so it always starts in
        # a well defined state.
        self.apply_Default_Settings()

    def Init_Hardware(self):
        """
        Connect to the actual device (or otherwise...)
        """

        try:
            self.my_Pharp = LD_Pharp.LD_Pharp(0)
        except (FileNotFoundError, UnboundLocalError) as e:
            # FileNotFoundError if DLL can't be found.
            # UnboundLocalError if the DLL can't find a Picoharp.
            self.logger.warning(e)
            self.logger.info("Picoharp library or Picoharp device not found")
            self.logger.info("Prompt user if they want to use simulation mode")
            # If the dll can't get a device handle, the program falls over,
            # Alert the user and give the option to run the barebones simulator
            # which allows the UI to be explored with some representative data.
            error_Response = QtGui.QMessageBox.question(
                self,
                "Error",
                "No driver/hardware found! Run in simulation mode?",
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
                )
            if error_Response == QtGui.QMessageBox.Yes:
                # Go get the simulator and launch it.
                self.my_Pharp = LD_Pharp_Dummy.LD_Pharp()
            else:
                # Fall over
                # TODO: Quit program gracefully?
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

        # Picoharp time resolution is a specific set of values.
        for res in self.allowed_Resolutions:
            self.ui.resolution.addItem(f"{res}")
        self.ui.resolution.setCurrentText("self.base_Resolution")

        self.ui.filename.setText("save_filename.csv")
        self.ui.status.setText("Counting")
        self.current_Options = {}
        self.apply_Default_Settings()

        # Cursor option defaults
        self.ui.option_Cursor.setChecked(True)
        self.cursors_On = self.ui.option_Cursor.isChecked()
        self.ui.option_Deltas.setChecked(True)
        self.deltas_On = self.ui.option_Deltas.isChecked()
        self.integrals_On = False
        self.ui.cursors_Tabber.setCurrentIndex(0)

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
        self.ui.button_ClearIntegrals.clicked.connect(self.on_Clear_Intervals)
        self.ui.cursors_Tabber.currentChanged.connect(self.on_Cursor_Tab)

        self.integral_Coords = [(0, 0),
                                (0, 0),
                                (0, 0),
                                (0, 0)]
        self.integral_Values = (
            self.ui.integral_Red,
            self.ui.integral_Green,
            self.ui.integral_Blue,
            self.ui.integral_Magenta
            )

        self.max_Values = (
            self.ui.max_Red,
            self.ui.max_Green,
            self.ui.max_Blue,
            self.ui.max_Magenta
            )

    def Init_Plot(self):
        """
        Init the plot widget and containers relating so it.
        """

        # Empty data structure.
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
        self.click_Number = 0
        # Last click has to be somewhere so just stick it at the origin.
        # Holds the co-ordinates of the most previous click.
        self.last_Click = QtCore.QPoint(0, 0)

        # Set up crosshairs for markers, one that follows the mouse, two
        # that persist after click (for one click before they move again), and
        # Four that are just pairs of vertical lines to appear round clicks in
        # "integral" mode.
        self.cursor_Lines = (
            self.Make_Line("h", "y"),
            self.Make_Line("v", "y")
            )

        self.delta_Lines = (
            (self.Make_Line("h", "r"), self.Make_Line("v", "r")),
            (self.Make_Line("h", "g"), self.Make_Line("v", "g"))
            )

        self.integral_vLines = (
            (self.Make_Line("v", "r"), self.Make_Line("v", "r")),
            (self.Make_Line("v", "g"), self.Make_Line("v", "g")),
            (self.Make_Line("v", "b"), self.Make_Line("v", "b")),
            (self.Make_Line("v", "w"), self.Make_Line("v", "w"))
            )

        # Necessary? Thought it would be good for every line to be in a
        # well defined position on init...
        for line in self.cursor_Lines:
            line.setPos(0)
        for line in itertools.chain.from_iterable(self.delta_Lines):
            line.setPos(0)
        for line in itertools.chain.from_iterable(self.integral_vLines):
            line.setPos(0)

    def Make_Line(self, orientation, colour):
        """
        Make a pyqtgraph line object, orientation either "h" or "v", colour
        is a single character passed directly to the pyqtgraph.InifiniteLine
        constructor.
        """
        this_Angle = self.orientations[orientation.lower()]
        return pyqtgraph.InfiniteLine(angle=this_Angle,
                                      movable=False,
                                      pen=colour)

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

        self.this_Data = histogram_Data

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
                #self.Integrate_Deltas()
            if self.integrals_On:
                self.Draw_Integrals()
                self.Display_Integrals()

        # Remember the last histogram, so it can be saved.
        self.last_Histogram = histogram_Data
        self.last_X_Data = self.x_Data

    def on_Cursor_Tab(self, tab_Number):
        """
        If the cursors tab is switched between "deltas" and "integrate" mode.
        If this happens, clear everything from the old tab from the plot and
        set everything up for the other function.
        """
        self.logger.debug(f"Cursors tab switched to {tab_Number}")

        self.click_Number = 0

        # Tab 0 is deltas mode (two cursors, calculate difference between them)
        if tab_Number == 0:
            self.deltas_On = self.ui.option_Deltas.isChecked()
            self.integrals_On = False

        # Tab 1 is integrals mode
        elif tab_Number == 1:
            self.deltas_On = False
            self.integrals_On = True
        # Something's gone very awry. There are only tabs 0 and 1...
        else:
            pass

    def Draw_Cursors(self):
        """
        Add a vertical line and a horizontal line to the plot widget. The idea
        is these follow the cursor to help reading the graph
        """
        for line in self.cursor_Lines:
            self.ui.graph_Widget.addItem(line) #, ignoreBounds=False)

    def Draw_Deltas(self):
        """
        Cursors that persist on mouse clicks.
        """
        for line in itertools.chain.from_iterable(self.delta_Lines):
            self.ui.graph_Widget.addItem(line) #, ignoreBounds=False)

    def Draw_Integrals(self):
        """
        Persistent cursors. 4 pairs spaced by a user supplied value.
        """
        for line in itertools.chain.from_iterable(self.integral_vLines):
            self.ui.graph_Widget.addItem(line) #, ignoreBounds=False)

    def Remove_Cursors(self):
        """
        Remove the cursor lines from the plot widget
        """
        for line in self.cursor_Lines:
            self.ui.graph_Widget.removeItem(line)

    def Remove_Deltas(self):
        """
        Remove the deltas from the plot widget.
        """
        for line in itertools.chain.from_iterable(self.delta_Lines):
            self.ui.graph_Widget.removeItem(line)

    def Remove_Integrals(self):
        """
        Remove integral cursors.
        """
        for line in itertools.chain.from_iterable(self.integral_vLines):
            self.ui.graph_Widget.removeItem(line)

    def Display_Integrals(self):
        """
        Go through the coordinates of the integral cursors, summing the bins
        between the bottom and top values. Display the sum in the relevant
        text box.
        """
        # So the for loop decalaration isn't too long.
        iterable = zip(self.integral_Coords, self.integral_Values, self.max_Values)
        for (bottom_Bin, top_Bin), mean_Box, max_Box in iterable:
            # Slice out the data relevant to the integral cursor locations
            this_Interval = self.this_Data[bottom_Bin : top_Bin]
            # Sum the slice and update the GUI
            this_Mean = this_Interval.mean()
            this_Max = this_Interval.max()
            mean_Box.setText(f"{this_Mean:.3E}")
            max_Box.setText(f"{this_Max:.3E}")

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

        # Get coords of cursor
        vb = self.ui.graph_Widget.plotItem.vb
        coords = vb.mapSceneToView(evt[0])

        # Plot h and v lines at cursor position
        self.cursor_Lines[1].setPos(coords.x())
        self.cursor_Lines[0].setPos(coords.y())

        # Update GUI cursor co-ordinates
        self.ui.current_X.setText(f"{coords.x():3E}")
        self.ui.current_Y.setText(f"{coords.y():.0f}")

    def on_Graph_Click(self, evt):
        """
        Clicks on the graph now depend on what the state of the
        self.ui.cursors_Tabber UI object. If it's set for deltas, clicking puts
        down one of two cursors and the X and Y different are written to text
        boxes.
        If it's set for integrals, pairs of cursors are placed (up to 4) and
        the bin values between them are summed (live).
        """

        # Get the xy coordinates of the click.
        vb = self.ui.graph_Widget.plotItem.vb
        coords = vb.mapSceneToView(evt.scenePos())

        if self.deltas_On:
            # Draw the lines where the click was. Update the GUI co-ordinates
            # corresponding to the click number.
            # TODO: Tidy this up! Use click_Number to index lists?
            if self.click_Number == 0:
                self.click_Number = 1
                # print(f"first {coords}")
                self.logger.debug(f"First click at {coords}")
                self.delta_Lines[0][1].setPos(coords.x())
                self.delta_Lines[0][0].setPos(coords.y())
                self.ui.click_1_X.setText(f"{coords.x():3E}")
                self.ui.click_1_Y.setText(f"{coords.y():.0f}")

            else:
                self.click_Number = 0
                # print(f"second {coords}")
                self.logger.debug(f"Second click at {coords}")
                self.delta_Lines[1][1].setPos(coords.x())
                self.delta_Lines[1][0].setPos(coords.y())
                self.ui.click_2_X.setText(f"{coords.x():3E}")
                self.ui.click_2_Y.setText(f"{coords.y():.0f}")

            # Update the delta GUI values.
            self.ui.delta_X.setText(f"{coords.x() - self.last_Click.x():3E}")
            self.ui.delta_Y.setText(f"{coords.y() - self.last_Click.y():.0f}")
            self.last_Click = coords

        elif self.integrals_On:
            # Cursors stored in a list, get the relevant ones for this click
            cursor_Bottom, cursor_Top = self.integral_vLines[self.click_Number]
            # Fetch the current desired width of the window between cursors.
            integral_Width = float(self.ui.integral_Width.text())

            # Centre the cursors on the click point, calculate the actual
            # cursor positions.
            middle = coords.x()
            bottom_Position = middle - (integral_Width / 2)
            top_Position = middle + (integral_Width / 2)

            # Set the cursor positions
            cursor_Bottom.setPos(bottom_Position)
            cursor_Top.setPos(top_Position)

            # Calculate the histogram bin numbers of the cursors (the graph
            # gives them in x axis units)
            resolution_ps = self.my_Pharp.resolution * 1e-12
            bottom_Bin = int(bottom_Position / resolution_ps)
            top_Bin = int(top_Position / resolution_ps)

            # Update a list so they can be stored and the integration can
            # happen live on each data refresh.
            self.integral_Coords[self.click_Number] = bottom_Bin, top_Bin

            # Advance click number through values 0, 1, 2, 3 repeating.
            self.click_Number = (self.click_Number + 1) % 4
        else:
            # Something's gone wrong if this happens.
            pass

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

        # I think this will always be zero (everything sets this to zero when
        # it's switched off) but let's be safe and set it to zero here.
        self.click_Number = 0

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

        # Put all the lines to zero (hide them)
        for line in itertools.chain.from_iterable(self.delta_Lines):
            line.setPos(0)

        # Fill GUI with zeros.
        self.ui.click_1_X.setText(f"{0}")
        self.ui.click_1_Y.setText(f"{0}")
        self.ui.click_2_X.setText(f"{0}")
        self.ui.click_2_Y.setText(f"{0}")
        self.ui.delta_X.setText(f"{0}")
        self.ui.delta_Y.setText(f"{0}")

        # Reset so the first click after this is the first delta
        self.click_Number = 0
        self.last_Click = QtCore.QPoint(0, 0)

    def on_Clear_Intervals(self):
        """
        Clear the interval cursors from the plot.
        Update the display
        """

        # So the first interval displayed after clikcing this is the first
        # one in the list
        self.click_Number = 0

        # Move all the interval lines to zero. (i.e. hide them)
        for line in itertools.chain.from_iterable(self.integral_vLines):
            line.setPos(0)

        # Set the co-ords of the top/bottom all to zero. So the data between
        # the positions is zero
        self.integral_Coords = [(0, 0),
                                (0, 0),
                                (0, 0),
                                (0, 0)]

app = QtWidgets.QApplication([])

application = MyWindow()

application.show()

sys.exit(app.exec())
