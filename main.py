"""
GUI for controlling the Picoharp300, choosing settings, visualizing and
exporting histograms.

This script is fairly alpha status at the moment. Comments/questions/requests
are welcome - email david@lownd.es or through github.com/dldlowndes/LD_Pharppy)

Requires: Python 3.7+, Numpy, PyQt5, PyQtGraph.

TODO list:
  Easy:
    - Give option to specify DLL path on FileNotFoundError when starting
    - Read and print DLL warnings (counts too high etc)
    - Cumulative histograms
    - Default options into an ini file
  Med:
    - Curve fitting (choose function - not just gaussian).
    - BUG: Integral bars only show when x=0 is visible on axis! (what.)
  Hard
    - Add dynamic number of delta/integration cursors instead of 2/4
    respectively
    - Investigate getting this to work with other hardware...
    - py2exe or something for distribution
    - Make a separate class for the integral cursors that wraps both vLines,
    the width, and data bars
        - Option to update width on already placed integrals
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
import scipy.signal

import acq_Thread
import settings_gui
import LD_Pharp
import LD_Pharp_Dummy
import LD_Pharp_Config

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

        # Colours to choose from and the order they are chosen
        self.palette = (
            QtGui.QColor(255, 0, 0),  # red
            QtGui.QColor(0, 255, 0),  # green
            QtGui.QColor(0, 0, 255),  # blue
            QtGui.QColor(255, 0, 255) # magenta
            )
        # Take the palette and make a copy with transparancy (alpha=64 seems
        # good?)
        self.palette_Alpha = [
            QtGui.QColor(*col.getRgb()[:3], 64) for col in self.palette]

        # Define hardware info members, then init them (and the hardware)
        self.my_Pharp = None
        self.base_Resolution = None
        self.allowed_Resolutions = None
        self.this_Data = np.zeros(65536)
        self.last_Histogram = np.zeros(65536)
        self.x_Data = np.zeros(65536)
        self.pharppy_Config = LD_Pharp_Config.LD_Pharppy_Settings("defaults.ini")
        self.Init_Hardware()

        # Members involved with UI, then init them (and the UI)
        self.integral_Coords = np.zeros((4, 2), dtype=np.int)
        self.integral_Means = np.zeros(4)
        self.integral_Maxes = np.zeros(4)
        self.integral_SDs = np.zeros(4)
        self.mean_TextBoxes = ()
        self.max_TextBoxes = ()
        self.fwhm_TextBoxes = ()
        self.click_TextBoxes = ()
        self.normalize_Buttons = ()
        self.cursors_On = None
        self.deltas_On = None
        self.integrals_On = None
        self.current_Options = None
        self.Init_UI()
        # Init_UI has set up the normalize buttons, the last one is checked by
        # default, so this should be the initial state.
        self.normalize_This = len(self.normalize_Buttons)

        # Members involved with plotting, then init them (and the plots)
        self.last_Histogram = None
        self.last_X_Data = None
        self.click_Number = 0
        self.last_Click = None
        self.Init_Plot()

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
        # All normalize radio buttons connected to the same method
        self.ui.normalize_Red.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Green.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Blue.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Magenta.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Off.toggled.connect(self.on_Normalize_Click)

        self.mean_TextBoxes = (
            self.ui.integral_Red,
            self.ui.integral_Green,
            self.ui.integral_Blue,
            self.ui.integral_Magenta
            )

        self.max_TextBoxes = (
            self.ui.max_Red,
            self.ui.max_Green,
            self.ui.max_Blue,
            self.ui.max_Magenta
            )

        self.click_TextBoxes = (
            (self.ui.click_1_X, self.ui.click_1_Y),
            (self.ui.click_2_X, self.ui.click_2_Y)
            )

        self.normalize_Buttons = (
            self.ui.normalize_Red,
            self.ui.normalize_Green,
            self.ui.normalize_Blue,
            self.ui.normalize_Magenta,
            self.ui.normalize_Off
            )

        self.fwhm_TextBoxes = (
            self.ui.fwhm_Red,
            self.ui.fwhm_Green,
            self.ui.fwhm_Blue,
            self.ui.fwhm_Magenta
            )

    def Init_Plot(self):
        """
        Init the plot widget and containers relating so it.
        """

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
            (self.Make_Line_Pair("h", "v", self.palette[0])),
            (self.Make_Line_Pair("h", "v", self.palette[1]))
            )

        self.integral_vLines = (
            (self.Make_Line_Pair("v", "v", self.palette[0])),
            (self.Make_Line_Pair("v", "v", self.palette[1])),
            (self.Make_Line_Pair("v", "v", self.palette[2])),
            (self.Make_Line_Pair("v", "v", self.palette[3]))
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

    def Make_Line_Pair(self, orientation1, orientation2, colour):
        """
        Make two lines, of the same colour, of any specified orientation.
        A bit excessive but saves some repetition
        """
        return (self.Make_Line(orientation1, colour),
                self.Make_Line(orientation2, colour))

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

            pharp_Config = self.pharppy_Config.Device_Settings
            pharp_Config.binning = int(binning)
            pharp_Config.sync_Offset = int(self.ui.sync_Offset.value())
            pharp_Config.sync_Divider = int(self.ui.sync_Divider.currentText())
            pharp_Config.CFD0_ZeroCrossing = int(self.ui.CFD0_Zerocross.value())
            pharp_Config.CFD0_Level = int(self.ui.CFD0_Level.value())
            pharp_Config.CFD1_ZeroCrossing = int(self.ui.CFD1_Zerocross.value())
            pharp_Config.CFD1_Level = int(self.ui.CFD1_Level.value())
            pharp_Config.acq_Time = int(self.ui.acq_Time.value())

            self.logger.info(f"Push settings\n {pharp_Config}")
            self.my_Pharp.Update_Settings(pharp_Config)

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

        self.pharppy_Config = LD_Pharp_Config.LD_Pharppy_Settings("defaults.ini")
        pharp_Config = self.pharppy_Config.Device_Settings

        binning = pharp_Config.binning
        resolution = self.base_Resolution * (2 ** binning)

        self.ui.resolution.setCurrentText(f"{resolution}")
        self.ui.sync_Offset.setValue(pharp_Config.sync_Offset)
        print(f"Just set sync offset, value now {self.ui.sync_Offset.value()}")
        self.ui.sync_Divider.setCurrentText(str(pharp_Config.sync_Divider))
        self.ui.CFD0_Level.setValue(pharp_Config.CFD0_Level)
        self.ui.CFD0_Zerocross.setValue(pharp_Config.CFD0_ZeroCrossing)
        self.ui.CFD1_Level.setValue(pharp_Config.CFD1_Level)
        self.ui.CFD1_Zerocross.setValue(pharp_Config.CFD1_ZeroCrossing)
        self.ui.acq_Time.setValue(pharp_Config.acq_Time)

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
            self.ui.button_ApplySettings.setEnabled(True)
            self.ui.button_Defaults.setEnabled(True)
        else:
            self.logger.info("Start histogramming")
            self.on_Clear_Histogram()
            self.ui.status.setText("Histogramming")
            self.acq_Thread.histogram_Active = True
            self.ui.button_ApplySettings.setEnabled(False)
            self.ui.button_Defaults.setEnabled(False)

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

        # TODO: Make this += for cumulative trace
        self.this_Data = histogram_Data

        # There are 65536 bins, but if (1/sync) is less than (65536*resolution)
        # then there will just be empty bins at the end of the histogram array.
        # Look from the END of the array and find the index of the first non
        # empty bin you find.
        last_Full_Bin = histogram_Data.nonzero()[0][-1]

        # Trim the histogram and labels so the empty bins (that will never
        # fill) are not plotted. Then plot them.
        self.ui.graph_Widget.plot(self.x_Data[:last_Full_Bin],
                                  self.this_Data[:last_Full_Bin],
                                  clear=True)
        # Change the plot limits so that the auto scale doesn't go crazy with
        # the cursors (if they're on) (plus a little margin so the labels show)
        x_Limit = self.x_Data[last_Full_Bin] * 1.05
        y_Limit = self.this_Data.max() * 1.05
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
            if self.integrals_On:
                self.Draw_Integrals()
                self.Display_Integrals()

        # Remember the last histogram, so it can be saved.
        self.last_Histogram = self.this_Data
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
            self.ui.graph_Widget.addItem(line)

    def Draw_Deltas(self):
        """
        Cursors that persist on mouse clicks.
        """
        for line in itertools.chain.from_iterable(self.delta_Lines):
            self.ui.graph_Widget.addItem(line)

    def Draw_Integrals(self):
        """
        Persistent cursors. 4 pairs spaced by a user supplied value.
        """
        for line in itertools.chain.from_iterable(self.integral_vLines):
            self.ui.graph_Widget.addItem(line)

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

        resolution_ps = self.my_Pharp.resolution * 1e-12

        # Go fetch the data between each pair of integral cursors.
        # Calculate mean/max values in separate loop up here so the values
        # can be normalized when displaying if required.
        for i, (bottom_Bin, top_Bin) in enumerate(self.integral_Coords):
            integral_Data = self.this_Data[bottom_Bin: top_Bin]
            this_X_Data = self.x_Data[bottom_Bin: top_Bin]

            # Numpy complains if this slice has no length, so catch that.
            if len(integral_Data) > 0:
                self.integral_Means[i] = integral_Data.mean()
                self.integral_Maxes[i] = integral_Data.max()

                # Get FWHM by literally counting the number of bins above half
                # the maximum value (after subtracting the noise floor)
                y_Range = integral_Data.max() - integral_Data.min()
                half_Max = y_Range / 2
                fwhm_Bins = sum(integral_Data > half_Max) * resolution_ps
                self.integral_SDs[i] = fwhm_Bins / 2.355

#                fit_Middle = np.average(this_X_Data, weights=integral_Data)
#                integral_Middle_Value = np.median(this_X_Data)
#                middle_Offset = integral_Middle_Value - fit_Middle
#                fit_Data = scipy.signal.gaussian(len(this_X_Data),
#                                                 self.integral_SDs[i] /resolution_ps)
#
#                fit_Graph = pyqtgraph.PlotCurveItem(
#                        x=this_X_Data - middle_Offset,
#                        y=fit_Data * integral_Data.max(),
#                        pen=self.palette[i],
#                        )
#                self.ui.graph_Widget.addItem(fit_Graph)

            else:
                # I suppose the mean and max of no data is zero?
                self.integral_Means[i] = 0
                self.integral_Maxes[i] = 0
                self.integral_SDs[i] = 0


        # Do this separately to make the for loop declaration neater.
        iterable = zip(
            self.integral_Means,
            self.integral_Maxes,
            self.integral_SDs,
            self.mean_TextBoxes,
            self.max_TextBoxes,
            self.fwhm_TextBoxes,
            )

        for (this_Mean, this_Max, this_SD,
             mean_Box, max_Box, fwhm_Box) in iterable:
            # The last normalize_Button is "off" i.e. don't do normalization.
            if self.normalize_This < (len(self.normalize_Buttons) - 1):
                # Otherwise normalize by the value of the specified cursor.
                mean_Factor = self.integral_Means[self.normalize_This]
                max_Factor = self.integral_Maxes[self.normalize_This]

                # Catch if this would lead to division by zero.
                if mean_Factor > 0:
                    this_Mean /= mean_Factor
                else:
                    this_Mean = np.inf
                if max_Factor > 0:
                    this_Max /= max_Factor  # because you're worth it.
                else:
                    this_Max = np.inf

            # Update the text box.
            mean_Box.setText(f"{this_Mean:.3E}")
            max_Box.setText(f"{this_Max:.3E}")
            fwhm_Box.setText(f"{this_SD * 2.355:.3E}")

        if self.ui.option_ShowBars.isChecked():
            # Plot bars between the interval cursors
            # Solid bars at the means
            mean_Bars = pyqtgraph.BarGraphItem(
                    x0 = self.integral_Coords[:,0] * resolution_ps,
                    x1 = self.integral_Coords[:,1] * resolution_ps,
                    height = self.integral_Means,
                    pens=self.palette,
                    brushes=self.palette)
            # Transparentish bars at the maxes
            max_Bars = pyqtgraph.BarGraphItem(
                    x0 = self.integral_Coords[:,0] * resolution_ps,
                    x1 = self.integral_Coords[:,1] * resolution_ps,
                    height = self.integral_Maxes,
                    pens=self.palette,
                    brushes=self.palette_Alpha)

            self.ui.graph_Widget.addItem(mean_Bars)
            self.ui.graph_Widget.addItem(max_Bars)

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
        view_Box = self.ui.graph_Widget.plotItem.vb
        coords = view_Box.mapSceneToView(evt[0])

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
        view_Box = self.ui.graph_Widget.plotItem.vb
        coords = view_Box.mapSceneToView(evt.scenePos())

        if self.deltas_On:
            self.on_Click_Deltas(coords)

        elif self.integrals_On:
            self.on_Click_Integrals(coords)
        else:
            # Something's gone wrong if this happens.
            pass

    def on_Click_Deltas(self, coords):
        """
        Draw the lines where the click was. Update the GUI co-ordinates
        corresponding to the click number.
        """

        self.logger.debug(f"Click number {self.click_Number} at {coords}")
        # Move the lines to the click coordinates.
        self.delta_Lines[self.click_Number][1].setPos(coords.x())
        self.delta_Lines[self.click_Number][0].setPos(coords.y())
        # Update the UI values.
        self.click_TextBoxes[self.click_Number][0].setText(f"{coords.x():3E}")
        self.click_TextBoxes[self.click_Number][1].setText(f"{coords.y():3E}")

        # Update the delta GUI values.
        self.ui.delta_X.setText(f"{coords.x() - self.last_Click.x():3E}")
        self.ui.delta_Y.setText(f"{coords.y() - self.last_Click.y():.0f}")
        self.last_Click = coords

        # 0->1, 1->0
        self.click_Number = (self.click_Number + 1) % 2

    def on_Click_Integrals(self, coords):
        """
        Draw the lines where the click was. Update the GUI co-ordinates
        corresponding to the click number.
        """

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
        # YOU CAN'T SLICE THE DATA HERE; IT WILL BE OUT OF DATE ON THE
        # NEXT on_Histo_Signal AND WON'T AUTO REFRESH CORRECTLY.
        self.integral_Coords[self.click_Number] = bottom_Bin, top_Bin

        # Advance click number through values 0, 1, 2, 3 repeating.
        self.click_Number = (self.click_Number + 1) % 4

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
        self.integral_Coords = np.array([(0, 0),
                                         (0, 0),
                                         (0, 0),
                                         (0, 0)])

    def on_Normalize_Click(self, checked):
        """
        When a normalize radio button is clicked. Update a variable keeping
        track of which one is clicked.
        Note that the signal is emitted when a radio button changes state, so
        this triggers twice on any click, once for a deactivate and once for
        an activate. Hence this only runs for the checked radio box. (not that
        it would do any harm but it's neater this way)
        """

        # Check the event was from a "checked" event not an "unchecked" event
        if checked:
            for i, radio in enumerate(self.normalize_Buttons):
                # Go through all the buttons looking for the checked one.
                if radio.isChecked():
                    self.logger.debug(f"Normalize button {i} is pressed")
                    # Remember which button it was that was checked.
                    self.normalize_This = i


app = QtWidgets.QApplication([])

application = MyWindow()

application.show()

sys.exit(app.exec())
