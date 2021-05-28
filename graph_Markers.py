from PyQt5 import QtGui

import pyqtgraph

class Generic_Cursor():
    def __init__(self, plot_Widget = None):
        self._coords = (0, 0)
        self._is_enabled = False
        
        self._colour = QtGui.QColor(255, 255, 255)
        
        self._lines = ()
        
        self._plot_Widget = plot_Widget
        
    @property
    def coords(self):
        return self._coords
    
    @coords.setter
    def coords(self, value):
        x, y, = value
        self._coords = (x ,y)
        self._lines[0].setPos(y)
        self._lines[1].setPos(x)
        
    @property
    def colour(self):
        return self._colour
    
    @colour.setter
    def colour(self, value=QtGui.QColor(255, 255, 255)):
        self._colour = value
        self._lines[0].setPen(self._colour)
        self._lines[1].setPen(self._colour)
    
    @property
    def is_Enabled(self):
        return self._is_enabled
    
    @is_Enabled.setter
    def is_Enabled(self, value):
        self._is_enabled = value
        
    def Add_To_Plot(self):
        self._plot_Widget.addItem(self._lines[0])
        self._plot_Widget.addItem(self._lines[1])
        
    def Remove_From_Plot(self):
        self._plot_Widget.removeItem(self._lines[0])
        self._plot_Widget.removeItem(self._lines[1])
        
    def Attach_To_Widget(self, plot_Widget):
        self._plot_Widget = plot_Widget
        
class XY_Cursor(Generic_Cursor):
    def __init__(self, plot_Widget):
        super().__init__(plot_Widget)
        
        self._hLine = pyqtgraph.InfiniteLine(angle=0,
                                      movable=False,
                                      pen=self._colour)
        self._vLine = pyqtgraph.InfiniteLine(angle=90,
                                      movable=False,
                                      pen=self._colour)
        self._lines = (self._hLine,
                       self._vLine)
        
class Integral_Cursor(Generic_Cursor):
    def __init__(self, plot_Widget):
        super().__init__(plot_Widget)
        
        self._left_Line = pyqtgraph.InfiniteLine(angle=90,
                                      movable=False,
                                      pen=self._colour)
        self._right_Line = pyqtgraph.InfiniteLine(angle=90,
                                      movable=False,
                                      pen=self._colour)
        self._lines = (self._left_Line,
                       self._right_Line)
        
        self._width = 0
        self._left_Position = 0
        self._right_Position = 0
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, value):
        self._width = value
        self._Update_Lines()
        
    @property
    def coords(self):
        return self._coords
    
    @coords.setter
    def coords(self, value):
        x, y, = value
        self._coords = (x, y)
        self._Update_Lines()

    def _Update_Lines(self):
        self._left_Position = self._coords[0] - (self._width / 2)
        self._right_Position = self._coords[0] + (self._width / 2)
        
        self._lines[0].setPos(self._left_Position)
        self._lines[1].setPos(self._right_Position)
  
if __name__ == "__main__":
    ...