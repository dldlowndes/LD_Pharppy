from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.resize(1600, 900)

        self.graph_Widget = PlotWidget(Settings)
        self.graph_Widget.setGeometry(QtCore.QRect(10, 20, 800, 600))