"""
GUI for controlling the Picoharp300, choosing settings, visualizing and
exporting histograms.

This script is fairly alpha status at the moment. Comments/questions/requests
are welcome - email david@lownd.es or through github.com/dldlowndes/LD_Pharppy)

Requires: Python 3.7+, Numpy, PyQt5, PyQtGraph.

TODO list:
  Easy:
    - Give option to specify DLL path on FileNotFoundError when starting
    - Type checking in config setters so they take either str or relevant type
    - use the X data to limit the plot axis when there's no data (otherwise
    cursor clicks with no data cause an exception)
    - Consider interpreting warning codes manually so unwanted warnings can
    be masked out.
  Med:
    - Curve fitting (choose function - not just gaussian).
    - BUG: Integral bars only show when x=0 is visible on axis! (what.)
  Hard
    - Add dynamic number of delta/integration cursors instead of 2/4
    respectively
    - Two y axes for counts mode (hard in pyqtplot)
    - Investigate getting this to work with other hardware...
"""

# Quieten pylint recommendations
# Quiet naming conventions
# pylint: disable=C0103
# Quiet too many attributes
# pylint: disable=R0902
# Quiet too many methods
# pylint: disable=R0904
# Quiet f strings in log messages
# pylint: disable=W1203

import collections
import itertools
import logging
import os
import sys

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph
import qdarkstyle

import acq_Thread
import graph_Markers
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

        # Colours to choose from and the order they are chosen
        self.palette = (
            QtGui.QColor(255, 0, 0),  # red
            QtGui.QColor(0, 255, 0),  # green
            QtGui.QColor(0, 0, 255),  # blue
            QtGui.QColor(255, 0, 255) # magenta
            )
        
        # Define hardware info members, then init them (and the hardware)
        self.my_Pharp = None
        self.allowed_Resolutions = None
        self.this_Data = np.zeros(65536)
        self.last_Histogram = np.zeros(65536)
        self.x_Data = np.zeros(65536)
        
        # LD_Pharp_Config inits with some sensible defaults
        self.pharppy_Config = LD_Pharp_Config.LD_Pharp_Config()
        # Save those defaults to a defaults file
        self.pharppy_Config.Save_To_File("defaults.ini")
        # See if there is an init.ini file to init the program with.
        try:
            # Remember this is initted with default values so if this fails
            # it's not a super big deal, the values are still good.
            self.pharppy_Config.Load_From_File("init.ini")
        except KeyError:
            # If there isn't one, make one.
            self.pharppy_Config.Save_To_File("init.ini")
        self.Init_Hardware()

        # Members involved with UI, then init them (and the UI)
        self.mean_TextBoxes = ()
        self.max_TextBoxes = ()
        self.fwhm_TextBoxes = ()
        self.click_TextBoxes = ()
        self.normalize_Buttons = ()
        self.cursors_On = None
        self.deltas_On = None
        self.integrals_On = None
        self.bars_On = None
        self.count_Mode = False
        self.n_Counts = 0
        self.count_History = collections.deque(maxlen=100000)
        self.detected_inis = []
        self.last_Warnings = ""
        self.Init_UI()
        # Init_UI has set up the normalize buttons, the last one is checked by
        # default, so this should be the initial state.
        self.normalize_This = len(self.normalize_Buttons)

        # Members involved with plotting, then init them (and the plots)
        self.last_Histogram = None
        self.last_X_Data = None
        self.click_Number = 0
        self.last_Click = None
        self.cursor_Marker = graph_Markers.XY_Cursor(self.ui.graph_Widget,
                                                     QtGui.QColor(255, 255, 0))
        self.delta_Cursors = []
        self.Init_Plot()

##############################################################################
# INIT METHODS
##############################################################################

    def Init_Hardware(self):
        """
        Connect to the actual device (or otherwise...)
        """

        try:
            self.my_Pharp = LD_Pharp.LD_Pharp(
                0,
                self.pharppy_Config.hw_Settings
                )
        except (UnboundLocalError, FileNotFoundError) as e:
            # FileNotFoundError if the DLL can't be found
            # UnboundLocalError if the DLL can't find a Picoharp.
            self.logger.warning(e)
            if isinstance(e, FileNotFoundError):
                self.logger.info("phlib dll not found. Is it installed?")
            if isinstance(e, UnboundLocalError):
                self.logger.info("Picoharp not found. Not plugged in or powered?")
                self.logger.info("Prompt user if they want to use simulation mode")
            # If the dll can't get a device handle, the program falls over,
            # Alert the user and give the option to run the barebones simulator
            # which allows the UI to be explored with some representative data.
            error_Response = QtWidgets.QMessageBox.question(
                self,
                "Error",
                "No driver/hardware found! Run in simulation mode?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
            if error_Response == QtWidgets.QMessageBox.Yes:
                # Go get the simulator and launch it.
                self.my_Pharp = LD_Pharp_Dummy.LD_Pharp(
                    0,
                    self.pharppy_Config.hw_Settings)
            else:
                # Fall over
                raise e

        # The resolutions are all 2**n multiples of the base resolution so
        # get the base resolution from the device and work out all of the
        # resolutions to display in the dropdown box.
        self.allowed_Resolutions = [
            self.my_Pharp.base_Resolution * (2**n) for n in range(8)
            ]

        # Make the worker thread.
        self.acq_Thread = acq_Thread.Acq_Thread(self.my_Pharp)
        self.acq_Thread.count_Signal.connect(self.on_Count_Signal)
        self.acq_Thread.plot_Signal.connect(self.on_Histo_Signal)
        self.acq_Thread.status_Signal.connect(self.on_Status_Signal)
        self.acq_Thread.start()

    def Init_UI(self):
        """
        Populate the UI with default settings and connect the buttons
        to functions.
        """

        # Picoharp time resolution is a specific set of values.
        for res in self.allowed_Resolutions:
            self.ui.resolution.addItem(f"{res}")
        self.ui.resolution.setCurrentText("self.my_Pharp.base_Resolution")

        self.ui.data_Filename.setText("save_filename.csv")
        self.ui.status.setText("Counting")
        self.Update_Settings_GUI()

        self.cursors_On = self.ui.option_Cursor.isChecked()
        self.deltas_On = self.ui.option_Deltas.isChecked()
        self.bars_On = self.ui.option_ShowBars.isChecked()
        self.integrals_On = False
        self.ui.cursors_Tabber.setCurrentIndex(0)

        # Scan for settings ini files and populate the dropdown for loading.
        self.detected_inis = [x for x in os.listdir() if x.endswith(".ini")]
        for ini in self.detected_inis:
            self.ui.existing_inis.addItem(ini)
            
        self.ui.counts_Ch0_Big.setStyleSheet("color: red")
        self.ui.counts_Ch1_Big.setStyleSheet("color: green")

        # Connect UI elements to functions
        self.ui.button_ApplySettings.clicked.connect(self.Push_Settings_To_HW)
        self.ui.button_Defaults.clicked.connect(self.Apply_Default_Settings)
        self.ui.button_StartStop.clicked.connect(self.start_Stop)
        self.ui.button_SaveHisto.clicked.connect(self.on_Save_Histo)
        self.ui.button_AutoRange.clicked.connect(self.on_Auto_Range)
        self.ui.option_Cursor.stateChanged.connect(self.on_Cursor_Button)
        self.ui.option_Deltas.stateChanged.connect(self.on_Deltas_Button)
        self.ui.option_ShowBars.stateChanged.connect(self.on_Bars_Button)
        self.ui.button_ClearDeltas.clicked.connect(self.on_Clear_Deltas)
        self.ui.button_ClearHistogram.clicked.connect(self.on_Clear_Histogram)
        self.ui.button_ClearIntegrals.clicked.connect(self.on_Clear_Intervals)
        self.ui.button_IntegralWidth.clicked.connect(self.on_Integral_Width_Button)
        self.ui.cursors_Tabber.currentChanged.connect(self.on_Cursor_Tab)
        self.ui.button_SaveSettings.clicked.connect(self.on_Save_Settings)
        self.ui.button_LoadSettings.clicked.connect(self.on_Load_Settings)
        # All normalize radio buttons connected to the same method
        self.ui.normalize_Red.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Green.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Blue.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Magenta.toggled.connect(self.on_Normalize_Click)
        self.ui.normalize_Off.toggled.connect(self.on_Normalize_Click)
        self.ui.button_CountsReset.clicked.connect(self.on_Counts_Reset)

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
        
        self.max_Pos_TestBoxes = (
            self.ui.max_Pos_Red,
            self.ui.max_Pos_Green,
            self.ui.max_Pos_Blue,
            self.ui.max_Pos_Magenta
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

        # X labels for the plot. The hardware only sends Y values so the
        # x values need to be inferred from the resolution.
        self.x_Data = np.arange(0,
                        65536 * self.my_Pharp.resolution,
                        self.my_Pharp.resolution
                        ) / 1e12

        # Modify the plot window
        self.ui.graph_Widget.plotItem.setLabel("left", "Counts")
        self.ui.graph_Widget.plotItem.setLabel("bottom", "Time", "s")
        self.ui.graph_Widget.plotItem.showGrid(x=True, y=True)
        # self.ui.graph_Widget.plotItem.showButtons() #does this do anything?

        # Dummy data that at least makes the axes look sensible...
        self.ui.graph_Widget.plotItem.plot(self.x_Data,
                                           np.ones_like(self.x_Data)
                                           )

        # Fix the plot area before anything else starts, otherwise the auto
        # scaler goes crazy with the cursors.
        self.ui.graph_Widget.plotItem.vb.setLimits(xMin=0,
                                                   yMin=0,
                                                   xMax=len(self.x_Data),
                                                   yMax=10)

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

        self.delta_Cursors = [graph_Markers.XY_Cursor(self.ui.graph_Widget,
                                                      self.palette[i])
                              for i in range(2)]

        self.integral_Cursors = [
            graph_Markers.Integral_Cursor(
                self.ui.graph_Widget,
                self.palette[i],
                self.my_Pharp.resolution * 1e-12)
            for i in range(4)
            ]

        self.cursor_Marker.coords = (0, 0)
        self.cursor_Marker.colour = (255, 255, 0)

        # Necessary? Thought it would be good for every line to be in a
        # well defined position on init...
        for cursor in self.delta_Cursors:
            cursor.coords = (0, 0)

##############################################################################
# HARDWARE SETTINGS METHODS
##############################################################################

    def Push_Settings_To_HW(self):
        """
        Get the settings from the UI and tell the picoharp to update them.
        """

        # To ensure avoiding trying to send settings while the hardware is
        # sending data, ask the hardware to pause briefly (not stop) then
        # un pause when settings send is finished. Pause/unpause insted of
        # start/stop preserves the started/stopped state when settings are
        # sent.
        self.acq_Thread.histogram_Paused = True
        
        # Translate desired resolution to a "binning" number. Binning
        # combines histogram bins to reduce the histogram resolution.
        resolution_Req = self.ui.resolution.currentText()
        binning = np.log2(float(resolution_Req) / self.my_Pharp.base_Resolution)

        hw_Settings = self.pharppy_Config.hw_Settings
        hw_Settings.binning = int(binning)
        hw_Settings.sync_Offset = int(self.ui.sync_Offset.value())
        hw_Settings.sync_Divider = int(self.ui.sync_Divider.currentText())
        hw_Settings.CFD0_ZeroCrossing = int(self.ui.CFD0_Zerocross.value())
        hw_Settings.CFD0_Level = int(self.ui.CFD0_Level.value())
        hw_Settings.CFD1_ZeroCrossing = int(self.ui.CFD1_Zerocross.value())
        hw_Settings.CFD1_Level = int(self.ui.CFD1_Level.value())
        hw_Settings.acq_Time = int(self.ui.acq_Time.value())

        self.logger.info(f"Push settings\n {hw_Settings}")
        self.my_Pharp.Update_Settings(hw_Settings)

        # If binning (resolution) changes, the histogram x axis labels
        # change. Update this. The max number of bins is 65536, this will
        # be trimmed in the plotting function.
        self.x_Data = np.arange(0,
                                65536 * self.my_Pharp.resolution,
                                self.my_Pharp.resolution
                                ) * 1e-12

        # Let the cursors know the resolution has been updated (since the
        # data->bin mapping depends on resolution)
        for cursor in self.integral_Cursors:
            cursor.resolution = self.my_Pharp.resolution * 1e-12

        self.acq_Thread.histogram_Paused = False

    def Apply_Default_Settings(self):
        """
        Make a default config file by making another instance of
        LD_Pharp_Config with no arguments. Update the GUI, then read the
        GUI for the settings to send to the hardware.
        """

        default_Config = LD_Pharp_Config.LD_Pharp_Config()

        self.Update_Settings_GUI(default_Config)
        self.Push_Settings_To_HW()

    def Update_Settings_GUI(self, config=None):
        """
        Copy the values from the LD_Pharp_Config object to the relevant boxes
        in the GUI
        """

        if isinstance(config, LD_Pharp_Config.LD_Pharp_Config):
            self.pharppy_Config = config

        hw_Settings = self.pharppy_Config.hw_Settings
        sw_Settings = self.pharppy_Config.sw_Settings

        binning = hw_Settings.binning
        resolution = self.my_Pharp.base_Resolution * (2 ** binning)

        self.logger.info("Update GUI elements")
        self.ui.resolution.setCurrentText(f"{resolution}")
        self.ui.sync_Offset.setValue(hw_Settings.sync_Offset)
        self.ui.sync_Divider.setCurrentText(str(hw_Settings.sync_Divider))
        self.ui.CFD0_Level.setValue(hw_Settings.CFD0_Level)
        self.ui.CFD0_Zerocross.setValue(hw_Settings.CFD0_ZeroCrossing)
        self.ui.CFD1_Level.setValue(hw_Settings.CFD1_Level)
        self.ui.CFD1_Zerocross.setValue(hw_Settings.CFD1_ZeroCrossing)
        self.ui.acq_Time.setValue(hw_Settings.acq_Time)

        self.ui.option_Cursor.setChecked(sw_Settings.show_Cursor)
        self.ui.option_Deltas.setChecked(sw_Settings.show_Deltas)
        self.ui.option_ShowBars.setChecked(sw_Settings.show_Bars)
        self.ui.integral_Width.setText(f"{sw_Settings.integral_Width}")
        self.ui.option_Cumulative.setChecked(sw_Settings.cumulative_Mode)
        self.ui.option_LogY.setChecked(sw_Settings.log_Y)

    def on_Load_Settings(self):
        """
        Load an ini file that's in the parent folder of this application.
        The program auto scans for .ini files and adds them to a dropdown
        """

        # Filename specified by selecting from the dropdown in the GUI
        filename = self.ui.existing_inis.currentText()
        self.logger.info(f"Loading settings file from {filename}")

        # Load the config, update the GUI and then push the settings displayed
        # in the GUI to the hardware (this ensures the GUI and the hardware
        # match, in case there's some weird error updating the GUI)
        self.pharppy_Config.Load_From_File(filename)
        self.logger.debug(f"New config {self.pharppy_Config}")
        self.Update_Settings_GUI(self.pharppy_Config)
        self.Push_Settings_To_HW()

        # Might as well re-scan again to make sure the dropdown is most up to
        # date. (in case the user has deleted any ini files)
        self.ui.existing_inis.clear()
        self.detected_inis = [x for x in os.listdir() if x.endswith(".ini")]
        for ini in self.detected_inis:
            self.ui.existing_inis.addItem(ini)

    def on_Save_Settings(self):
        """
        Save the most recent settings that were pushed to the hardware to an
        ini file with a name specified by the GUI element settings_SaveName
        """

        filename = self.ui.settings_SaveName.text()
        # Enforce the file type
        if not filename.endswith(".ini"):
            filename += ".ini"
        # rescan the folder for existing files before enforcing that the
        # filename can't clash with an existing one.
        self.detected_inis = [x for x in os.listdir() if x.endswith(".ini")]
        # prevent accidental overwriting of previous ini files
        if filename in self.detected_inis:
            self.logger.error("Log file name exists")
            raise ValueError
        self.logger.info(f"Saving latest applied settings to {filename}")

        self.pharppy_Config.Save_To_File(filename)

        # Update the list of existing ini files now there's another one. Could
        # save a call to os.listdir here since it was performed above but it's
        # not really a problem and there's more certainty doing it like this.
        self.ui.existing_inis.clear()
        self.detected_inis = [x for x in os.listdir() if x.endswith(".ini")]
        for ini in self.detected_inis:
            self.ui.existing_inis.addItem(ini)

##############################################################################
# HARDWARE INTERFACE METHODS
##############################################################################

    def start_Stop(self):
        """
        Switch modes from counting to histogramming.
        """

        if self.no_Data:
            self.no_Data = False

        if self.acq_Thread.histogram_Active:
            self.start_Hist_Mode()
        else:
            self.stop_Hist_Mode()

    def start_Hist_Mode(self):
        self.logger.info("Stop histogramming")
        self.ui.status.setText("Counting")
        self.acq_Thread.histogram_Active = False
        # self.ui.button_ApplySettings.setEnabled(True)
        # self.ui.button_Defaults.setEnabled(True)
        # self.ui.button_LoadSettings.setEnabled(True)
        # self.ui.button_SaveSettings.setEnabled(True)
        
    def stop_Hist_Mode(self):
        self.logger.info("Start histogramming")
        self.on_Clear_Histogram()
        self.ui.status.setText("Histogramming")
        self.acq_Thread.histogram_Active = True
        # self.ui.button_ApplySettings.setEnabled(False)
        # self.ui.button_Defaults.setEnabled(False)
        # self.ui.button_LoadSettings.setEnabled(False)
        # self.ui.button_SaveSettings.setEnabled(False)
        
    def on_Count_Signal(self, ch0, ch1):
        """
        Handle the counts when the hardware thread emits them
        """

        # Write to the small text boxes on the GUI whatever the settings are
        self.ui.counts_Ch0.setText(f"{ch0:.{self.count_Precision}E}")
        self.ui.counts_Ch1.setText(f"{ch1:.{self.count_Precision}E}")
        
        # Remember the counts in case they want to be plotted later.
        self.count_History.append([ch0, ch1])
        self.n_Counts += 1
        
        if self.count_Mode:
            """
            Count mode is a dedicated display tab that shows the counts in 
            much bigger font (for visibility for example when aligning optics),
            a line graph is also shown on the graph pane (instead of the TCSPC
            histogram) colour coded to the colours of the displayed counts.
            """
            
            # Set the format of the values put in the UI, either integers with
            # thousands separated by commas, or as scientific numbers with 
            # adjustable precision.
            fmt = ","
            if self.ui.option_SciCounts.isChecked():
                fmt = f".{self.ui.value_CountPrecision.value()}E"
            self.ui.counts_Ch0_Big.setText(f"{ch0:{fmt}}")
            self.ui.counts_Ch1_Big.setText(f"{ch1:{fmt}}")
            
            # How many counts to show on the graph before the oldest ones start
            # to be dropped. The counts are stored in a massive deque so
            # extending the display after shrinking it brings back the old 
            # values.
            n_Counts_Display = self.ui.value_NumGraphCounts.value()
            # If the deque contains less than n_Counts_Display counts, set the
            # first value to the 0th element, otherwise it's the 
            # n_Counts_Display'th to last element.
            start_i = max(0, len(self.count_History) - n_Counts_Display) # 0 or +ve value
            # Get just the data for plotting from the deque.
            display_Counts = itertools.islice(self.count_History,
                                              start_i,
                                              None)
            # Split into channels to plot separately
            ch0, ch1 = zip(*display_Counts)
            ch0 = np.array(ch0, dtype=np.int32)
            ch1 = np.array(ch1, dtype=np.int32)
            
            # Make the x labels correspond to the number of count signals
            # received. (because why not)
            x_Data = range(self.n_Counts - len(ch0), self.n_Counts)
            # Plot the data
            red = QtGui.QColor(255, 0, 0)
            green = QtGui.QColor(0, 255, 0)
            
            if self.ui.option_LogY.isChecked():
                ch0 = np.log10(ch0, where=ch0>0)
                ch1 = np.log10(ch1, where=ch1>0)
            
            # Clear the plot before replotting otherwise if the options are
            # unchecked it just doesn't show new data (but still shows data
            # from before the option was unchecked).
            self.ui.graph_Widget.clear()
            
            if self.ui.option_Ch0_Counts.isChecked():
                self.ui.graph_Widget.plot(x_Data, ch0, pen=red)
            if self.ui.option_Ch1_Counts.isChecked():
                self.ui.graph_Widget.plot(x_Data, ch1, pen=green)
        
            # Auto scale to the visible values.
            self.ui.graph_Widget.plotItem.vb.setLimits(
                xMin=x_Data[0]-0.1,
                yMin=0,
                xMax=x_Data[-1]+0.1,
                yMax=1.1*max(max(ch0), max(ch1))
                )
        
    def on_Histo_Signal(self, histogram_Data):
        """
        Handle the histogram when the hardware thread emits one.
        """

        if self.ui.option_Cumulative.isChecked():
            self.this_Data += histogram_Data
        else:
            self.this_Data = histogram_Data
            
        if self.count_Mode:
            return

        # There are 65536 bins, but if (1/sync) is less than (65536*resolution)
        # then there will just be empty bins at the end of the histogram array.
        # Look from the END of the array and find the index of the first non
        # empty bin you find.
        last_Full_Bin = histogram_Data.nonzero()[0][-1]

        # Trim the histogram and labels so the empty bins (that will never
        # fill) are not plotted. Then plot them.
        plot_X = self.x_Data[:last_Full_Bin]
        plot_Y = self.this_Data[:last_Full_Bin]
        # pyqtgraph log mode seems weird, just log the bin values instead if
        # log scale is what's required...
        if self.ui.option_LogY.isChecked():
            plot_Y = np.log10(plot_Y, where=plot_Y>0)
            
        self.ui.graph_Widget.plot(plot_X,
                                  plot_Y,
                                  clear=True)
        # Change the plot limits so that the auto scale doesn't go crazy with
        # the cursors (if they're on) (plus a little margin so the labels show)
        self.ui.graph_Widget.plotItem.vb.setLimits(xMin=0,
                                                   yMin=0,
                                                   xMax=plot_X[-1] * 1.05,
                                                   yMax=plot_Y.max() * 1.05)

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
    
    def on_Status_Signal(self, warnings):
        # Check if the warnings are any different to last time. If not, don't
        # do anything. This saves an interaction with the GUI but also doesn't
        # reset the scroll position of the text box back to the top which is
        # annoying if you're trying to read the error.
        if warnings == self.last_Warnings:
            pass
        else:
            log_String = "\n".join(["New Warnings",
                                    "-----------",
                                    warnings[:-1],
                                    "-----------"])
            self.logger.warning(log_String)
            self.last_Warnings = warnings
            # I THINK the string "WARNING_" only occurs once per warning.
            # There's nothing else there is consistently once in every warning
            # (there's not even consistent newline characters), maybe colons
            # would work too?
            n_Warnings = warnings.count("WARNING_")
            # Update the tab label to show the number of warnings in brackets
            # Then update the actual text box with the warnings text reported
            # by the phlib dll.
            self.ui.control_Warning_Tabber.setTabText(1, f"Warnings ({n_Warnings})")
            self.ui.warnings_Display.setText(warnings)
                
##############################################################################
# GUI METHODS (NON GRAPHING)
##############################################################################

    def on_Counts_Reset(self):
        self.count_History.clear()
        self.n_Counts = 0

    def on_Cursor_Button(self):
        """
        Toggle the live cursor on/off
        """
        self.cursors_On = self.ui.option_Cursor.isChecked()
        self.pharppy_Config.sw_Settings.show_Cursor = str(self.cursors_On)

        if self.cursors_On:
            # Redraw the cursor
            self.logger.info("Turn cursor on")
            self.Draw_Cursors()
        else:
            # Remove the cursor
            self.logger.info("Turn cursor off")
            self.Remove_Cursors()

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
            self.deltas_On = self.pharppy_Config.sw_Settings.show_Deltas
            self.integrals_On = False
            self.count_Mode = False
            self.acq_Thread.histogram_Paused = False
            # enable xy cursor if the GUI element wants them
            self.on_Cursor_Button()
        # Tab 1 is integrals mode
        elif tab_Number == 1:
            self.deltas_On = False
            self.integrals_On = True
            self.count_Mode = False
            self.acq_Thread.histogram_Paused = False
            # enable xy cursor if the GUI element wants them
            self.on_Cursor_Button()
        elif tab_Number == 2:
            self.deltas_On = False
            self.integrals_On = False
            self.count_Mode = True
            self.acq_Thread.histogram_Paused = True
            self.cursors_On = False
        # Something's gone very awry.
        else:
            pass

    def on_Integral_Width_Button(self):
        """
        Take new value for integral width from the GUI.
        """
        new_Width = self.ui.integral_Width.text()
        self.pharppy_Config.sw_Settings.integral_Width = new_Width

        for cursor in self.integral_Cursors:
            cursor.width = self.pharppy_Config.sw_Settings.integral_Width

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

    def on_Save_Histo(self):
        """
        This actually still works when histogramming is running but obviously
        there won't be certainty as to exactly what the histogram looks like.
        """
        # Read the filename box from the UI.
        filename = self.ui.data_Filename.text()

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

##############################################################################
# PLOTTING METHODS
##############################################################################

    def Draw_Cursors(self):
        """
        Add a vertical line and a horizontal line to the plot widget. The idea
        is these follow the cursor to help reading the graph
        """
        self.cursor_Marker.Add_To_Plot()

    def Draw_Deltas(self):
        """
        Cursors that persist on mouse clicks.
        """
        for cursor in self.delta_Cursors:
            cursor.Add_To_Plot()

    def Draw_Integrals(self):
        """
        Persistent cursors. 4 pairs spaced by a user supplied value.
        """
        # for line in itertools.chain.from_iterable(self.integral_vLines):
        #     self.ui.graph_Widget.addItem(line)
        for integral in self.integral_Cursors:
            integral.Add_To_Plot()

    def Remove_Cursors(self):
        """
        Remove the cursor lines from the plot widget
        """
        self.cursor_Marker.Remove_From_Plot()

    def Remove_Deltas(self):
        """
        Remove the deltas from the plot widget.
        """
        for cursor in self.delta_Cursors:
            cursor.Remove_From_Plot()

    def Remove_Integrals(self):
        """
        Remove integral cursors.
        """
        # for line in itertools.chain.from_iterable(self.integral_vLines):
        #     self.ui.graph_Widget.removeItem(line)
        for integral in self.integral_Cursors:
            integral.Remove_From_Plot()

    def Display_Integrals(self):
        """
        Send the histogram data to the cursors objects, which know where to
        look for the data between their markers.
        Integral cursor objects calculate and return the mean, max and fwhm
        of the data between the markers.
        Then Update the GUI as well (including optional normalizing)
        """

        # Send the histogram data to each cursor so it can extract the relevant
        # data, update the bars and returns the mean, max and fwhm values.
        integrals_Readings = [
            cursor.Update_Stats(self.this_Data, self.bars_On, self.ui.option_LogY.isChecked())
            for cursor in self.integral_Cursors
            ]

        # A big iterable so let's define it separate to the for loop
        iterable = zip(
            integrals_Readings,
            self.mean_TextBoxes,
            self.max_TextBoxes,
            self.max_Pos_TestBoxes,
            self.fwhm_TextBoxes
            )

        # Update the GUI
        for ((this_Mean, this_Max, this_Max_Pos, this_FWHM),
             mean_Box, max_Box, max_Pos_Box, fwhm_Box) in iterable:

            # Check if normalization is turned on, and if so for which channel
            if self.normalize_This < len(self.normalize_Buttons) - 1:
                mean_Factor = integrals_Readings[self.normalize_This][0]
                max_Factor = integrals_Readings[self.normalize_This][1]
                zero_Time = integrals_Readings[self.normalize_This][2]

                # Check for invalid normalization factors
                if mean_Factor > 0:
                    this_Mean /= mean_Factor
                else:
                    this_Mean = np.inf
                if max_Factor > 0:
                    this_Max /= max_Factor
                else:
                    this_Max = np.inf
                    
                this_Max_Pos -= zero_Time

            # Finally, update the GUI
            mean_Box.setText(f"{this_Mean:.3E}")
            max_Box.setText(f"{this_Max:.3E}")
            max_Pos_Box.setText(f"{this_Max_Pos:.3E}")
            fwhm_Box.setText(f"{this_FWHM:.3E}")

    def on_Auto_Range(self):
        """
        Tell the plot widget to fit the full histogram on the plot.
        """
        # pyqtgraph has our back on this one!
        self.logger.debug("Auto range histogram")
        self.ui.graph_Widget.plotItem.autoBtnClicked()

    def on_Bars_Button(self):
        """
        Toggle display of bars in integral mode showing max/mean values
        inside the interval.
        """

        self.bars_On = self.ui.option_ShowBars.isChecked()
        self.pharppy_Config.sw_Settings.show_Bars = str(self.bars_On)

    def on_Clear_Deltas(self):
        """
        Get rid of the current displayed deltas cursors without turning off
        the deltas mode, also resets click number.
        """
        self.logger.info("Clear deltas")

        # Put all the lines to zero (hide them)
        for cursor in self.delta_Cursors:
            cursor.coords = (0, 0)

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

    def on_Clear_Histogram(self):
        """
        Delete everything in the plot!
        """
        # pyqtgraph has our back on this one too.
        self.logger.debug("Clear histogram")
        self.ui.graph_Widget.plotItem.clear()

    def on_Clear_Intervals(self):
        """
        Clear the interval cursors from the plot.
        """

        # So the first interval displayed after clikcing this is the first
        # one in the list
        self.click_Number = 0

        # Move all the interval lines to zero. (i.e. hide them)
        for cursor in self.integral_Cursors:
            cursor.Reset_Remove()

    def on_Click_Deltas(self, coords):
        """
        Draw the lines where the click was. Update the GUI co-ordinates
        corresponding to the click number.
        """

        self.logger.debug(f"Click number {self.click_Number} at {coords}")
        # Move the lines to the click coordinates.
        self.delta_Cursors[self.click_Number].coords = (coords.x(), coords.y())

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

        this_Cursor = self.integral_Cursors[self.click_Number]
        this_Cursor.coords = (coords.x(), coords.y())
        this_Cursor.width = self.pharppy_Config.sw_Settings.integral_Width

        # Advance click number through values 0, 1, 2, 3 repeating.
        self.click_Number = (self.click_Number + 1) % 4

    def on_Deltas_Button(self):
        """
        Toggle the (display) of the cursors that appear on mouse clicks for
        calculating deltas (deltas are still calculated - including new clicks
        so clicking with deltas off and turning them back on will not re-show
        the old deltas)
        """

        self.deltas_On = self.ui.option_Deltas.isChecked()
        self.pharppy_Config.sw_Settings.show_Deltas = str(self.deltas_On)

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

    def on_Mouse_Move(self, evt):
        """
        Move the crosshair that follows the mouse to the mouse position.
        """

        # Get coords of cursor
        view_Box = self.ui.graph_Widget.plotItem.vb
        coords = view_Box.mapSceneToView(evt[0])

        # Plot h and v lines at cursor position
        self.cursor_Marker.coords = (coords.x(), coords.y())

        # Update GUI cursor co-ordinates
        self.ui.current_X.setText(f"{coords.x():3E}")
        self.ui.current_Y.setText(f"{coords.y():.0f}")

        # Hack. For some reason the cursor moving removes any bars that the
        # cursor overlaps. This way at least they're only missing for
        if self.bars_On and self.integrals_On:
            for cursor in self.integral_Cursors:
                cursor.Remove_Bars()
                cursor.Add_Bars()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    #app.setFont(QtGui.QFont("MS Shell Dlg", 12))

    application = MyWindow()

    application.show()

    sys.exit(app.exec())
