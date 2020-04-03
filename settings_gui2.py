# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings_gui.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph

class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.resize(800, 600)
        
        self.Controls()
        self.Cursors()

        self.main_Layout = QtWidgets.QHBoxLayout()
        self.left_Layout = QtWidgets.QVBoxLayout()
        self.right_Layout = QtWidgets.QVBoxLayout()
        self.main_Layout.addLayout(self.left_Layout)
        self.main_Layout.addLayout(self.right_Layout)
        
        self.right_Layout.addWidget(self.ch0_Container)
        self.right_Layout.addWidget(self.ch1_Container)
        self.right_Layout.addWidget(self.general_Container)
        self.right_Layout.addWidget(self.histogram_Container)
        self.right_Layout.addWidget(self.control_Container)
        self.right_Layout.addWidget(self.counts_Container)
        
        self.graph_Widget = pyqtgraph.PlotWidget()
        self.left_Layout.addWidget(self.graph_Widget)
        self.left_Layout.addLayout(self.cursors_Layout)

        Settings.setLayout(self.main_Layout)

        QtCore.QMetaObject.connectSlotsByName(Settings)
        
    def Controls(self):
        ### CH0 settings
        self.CFD0_Zerocross_Label = QtWidgets.QLabel("Zero Crossing (mv)")
        self.CFD0_Zerocross = QtWidgets.QDoubleSpinBox()
        self.CFD0_Zerocross.setDecimals(0)
        self.CFD0_Zerocross.setMaximum(20.0)
        self.CFD0_Zerocross.setProperty("value", 10.0)
        
        self.CFD0_Level_Label = QtWidgets.QLabel("Discriminator (mv)")
        self.CFD0_Level = QtWidgets.QDoubleSpinBox()
        self.CFD0_Level.setDecimals(0)
        self.CFD0_Level.setMaximum(800.0)
        self.CFD0_Level.setProperty("value", 50.0)
        
        self.sync_Divider_Label = QtWidgets.QLabel("Clock Divider")
        self.sync_Divider = QtWidgets.QComboBox()
        self.sync_Divider.setObjectName("sync_Divider")
        self.sync_Divider.addItem("1")
        self.sync_Divider.addItem("2")
        self.sync_Divider.addItem("4")
        self.sync_Divider.addItem("8")
        
        self.sync_Offset_Label = QtWidgets.QLabel("Offset (ns)")
        self.sync_Offset = QtWidgets.QDoubleSpinBox()
        
        self.ch0_Settings = QtWidgets.QFormLayout()
        self.ch0_Settings.addRow(self.CFD0_Zerocross_Label,
                                 self.CFD0_Zerocross)
        self.ch0_Settings.addRow(self.CFD0_Level_Label,
                                 self.CFD0_Level)        
        self.ch0_Settings.addRow(self.sync_Divider_Label,
                                 self.sync_Divider)        
        self.ch0_Settings.addRow(self.sync_Offset_Label,
                                 self.sync_Offset)
        
        self.ch0_Container = QtWidgets.QGroupBox("Ch0 (sync)")
        self.ch0_Container.setLayout(self.ch0_Settings)
        
        ### CH1 settings
        self.CFD1_Zerocross_Label = QtWidgets.QLabel("Zero Crossing (mv)")
        self.CFD1_Zerocross = QtWidgets.QDoubleSpinBox()
        self.CFD1_Zerocross.setDecimals(0)
        self.CFD1_Zerocross.setMaximum(20.0)
        self.CFD1_Zerocross.setProperty("value", 10.0)
        
        self.CFD1_Level_Label = QtWidgets.QLabel("Discriminator (mv)")
        self.CFD1_Level = QtWidgets.QDoubleSpinBox()
        self.CFD1_Level.setDecimals(0)
        self.CFD1_Level.setMaximum(800.0)
        self.CFD1_Level.setProperty("value", 50.0)
        
        self.ch1_Settings = QtWidgets.QFormLayout()
        self.ch1_Settings.addRow(self.CFD1_Zerocross_Label,
                                 self.CFD1_Zerocross)
        self.ch1_Settings.addRow(self.CFD1_Level_Label,
                                 self.CFD1_Level)  
        
        self.ch1_Container = QtWidgets.QGroupBox("Ch1 (signal)")
        self.ch1_Container.setLayout(self.ch1_Settings)
        
        ### General settings
        self.resolution_Label = QtWidgets.QLabel("Resolution (ps)")
        self.resolution = QtWidgets.QComboBox()
        
        self.acq_Time_Label = QtWidgets.QLabel("Acq. time (ms)")
        self.acq_Time = QtWidgets.QDoubleSpinBox()
        self.acq_Time.setDecimals(0)
        self.acq_Time.setMaximum(36000000.0)
        self.acq_Time.setProperty("value", 1000.0)
        self.acq_Time.setObjectName("acq_Time")
        
        self.general_Settings = QtWidgets.QFormLayout()
        self.general_Settings.addRow(self.resolution_Label,
                                     self.resolution)
        self.general_Settings.addRow(self.acq_Time_Label,
                                     self.acq_Time)
        self.general_Container = QtWidgets.QGroupBox("General")
        self.general_Container.setLayout(self.general_Settings)
        
        ### Plot settings
        self.option_Cursor = QtWidgets.QCheckBox()
        self.option_Cursor.setEnabled(True)
        
        self.option_Deltas = QtWidgets.QCheckBox()
        self.option_Cursor.setEnabled(True)
        
        self.button_ClearHistogram = QtWidgets.QPushButton("Clear Histogram")

        self.button_ClearDeltas = QtWidgets.QPushButton("Clear Deltas")
        
        self.button_AutoRange = QtWidgets.QPushButton("Auto Range")
        
        self.filename_Label = QtWidgets.QLabel("Filename:")        
        self.filename = QtWidgets.QLineEdit()
        self.button_SaveHisto = QtWidgets.QPushButton("Save Histogram")
        
        self.histo_Layout = QtWidgets.QGridLayout()
        self.histo_Layout.addWidget(self.option_Cursor, 0, 0)
        self.histo_Layout.addWidget(self.option_Deltas, 0, 1)
        self.histo_Layout.addWidget(self.button_ClearHistogram, 1, 0)
        self.histo_Layout.addWidget(self.button_ClearDeltas, 1, 1)
        self.histo_Layout.addWidget(self.button_AutoRange, 2, 0)
        self.histo_Layout.addWidget(self.filename_Label, 3, 0)
        self.histo_Layout.addWidget(self.filename, 3, 1)
        self.histo_Layout.addWidget(self.button_SaveHisto, 4, 0)
        
        self.histogram_Container = QtWidgets.QGroupBox("Histogram")
        self.histogram_Container.setLayout(self.histo_Layout)
    
        ###Controls
        self.button_ApplySettings = QtWidgets.QPushButton("Save Histogram")
        self.button_Defaults = QtWidgets.QPushButton("Save Histogram")
        self.button_StartStop = QtWidgets.QPushButton("Save Histogram")
        self.status = QtWidgets.QLineEdit()
        
        self.control_Layout = QtWidgets.QVBoxLayout()
        self.control_Layout.addWidget(self.button_ApplySettings)
        self.control_Layout.addWidget(self.button_Defaults)
        self.control_Layout.addWidget(self.button_StartStop)
        self.control_Layout.addWidget(self.status)
        
        self.control_Container = QtWidgets.QGroupBox("Contols")
        self.control_Container.setLayout(self.control_Layout)
        
        ### Counts
        self.counts_Ch0_Label = QtWidgets.QLabel("Ch0 (sync)")
        self.counts_Ch0 = QtWidgets.QLineEdit()
        self.counts_Ch1_Label = QtWidgets.QLabel("Ch1 (signal)")
        self.counts_Ch1 = QtWidgets.QLineEdit()
        
        self.counts_Layout = QtWidgets.QVBoxLayout()
        self.counts_Layout.addWidget(self.counts_Ch0_Label)
        self.counts_Layout.addWidget(self.counts_Ch0)
        self.counts_Layout.addWidget(self.counts_Ch1_Label)
        self.counts_Layout.addWidget(self.counts_Ch1)
        
        self.counts_Container = QtWidgets.QGroupBox("Channel Counts")
        self.counts_Container.setLayout(self.counts_Layout)
        
    def Cursors(self):
        self.current_Label = QtWidgets.QLabel("Current (yellow)")
        self.click1_Label = QtWidgets.QLabel("Click1 (red)")
        self.click2_Label = QtWidgets.QLabel("Click2 (blue)")
        self.delta_Label = QtWidgets.QLabel("Click1 - Click2")
        self.x_Label = QtWidgets.QLabel("X:")
        self.y_Label = QtWidgets.QLabel("Y:")
        
        self.current_X = QtWidgets.QLineEdit()
        self.current_Y = QtWidgets.QLineEdit()
        self.click1_X = QtWidgets.QLineEdit()
        self.click1_Y = QtWidgets.QLineEdit()
        self.click2_X = QtWidgets.QLineEdit()
        self.click2_Y = QtWidgets.QLineEdit()
        self.delta_X = QtWidgets.QLineEdit()
        self.delta_Y = QtWidgets.QLineEdit()
        
        self.cursors_Layout = QtWidgets.QGridLayout()
        self.cursors_Layout.addWidget(self.current_Label, 0, 0)
        self.cursors_Layout.addWidget(self.click1_Label, 0, 1)
        self.cursors_Layout.addWidget(self.click2_Label, 0, 2)
        self.cursors_Layout.addWidget(self.delta_Label, 0, 3)
        self.cursors_Layout.addWidget(self.x_Label, 1, 0)
        self.cursors_Layout.addWidget(self.y_Label, 2, 0)
        self.cursors_Layout.addWidget(self.current_X, 1, 0)
        self.cursors_Layout.addWidget(self.current_Y, 2, 0)
        self.cursors_Layout.addWidget(self.click1_X, 1, 1)
        self.cursors_Layout.addWidget(self.click1_Y, 2, 1)
        self.cursors_Layout.addWidget(self.click2_X, 1, 2)
        self.cursors_Layout.addWidget(self.click2_Y, 2, 2)
        self.cursors_Layout.addWidget(self.delta_X, 1, 3)
        self.cursors_Layout.addWidget(self.delta_Y, 2, 3)
        
