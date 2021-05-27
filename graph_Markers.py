from PyQt5 import QtGui

import pyqtgraph

class XY_Cursor:
    def __init__(self):
        self._coords = (0, 0)
        self._is_enabled = False
        
        self._colour = QtGui.QColor(255, 255, 255)
        
        self._hLine = pyqtgraph.InfiniteLine(angle=0,
                                      movable=False,
                                      pen=self._colour)
        self._vLine = pyqtgraph.InfiniteLine(angle=90,
                                      movable=False,
                                      pen=self._colour)
        
    @property
    def Coords(self):
        return self._coords
    
    @setter.Coords
    def Coords(self, x, y):
        self._coords = (x ,y)
        self._hLine.setPos(y)
        self._vLine.setPos(x)
        
    @property
    def Colour(self):
        return self._colour
    
    @setter.Colour
    def Colour(self, value=QtGui.QColor(255, 255, 255)):
        self._colour = value
    
    @property
    def Is_Enabled(self):
        return self._is_enabled
    
    @setter.Is_Enabled
    def Is_Enabled(self, value):
        self._is_enabled = value
        
    def Add_To_Plot(self, plot_Widget):
        plot_Widget.addItem(self._hLine)
        plot_Widget.addItem(self._vLine)
        
    def Remove_From_Plot(self, plot_Widget):
        plot_Widget.removeItem(self._hLine)
        plot_Widget.removeItem(self._vLine)