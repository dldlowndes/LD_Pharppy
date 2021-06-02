from PyQt5 import QtGui

import pyqtgraph

class Generic_Cursor():
    def __init__(self, plot_Widget = None, colour = None):
        self._coords = (0, 0)
        self._is_enabled = False
        
        if isinstance(colour, type(None)):
            self._colour = QtGui.QColor(255, 255, 255)
        else:
            self._colour = colour
            
        self._colour_Alpha = QtGui.QColor(*self._colour.getRgb()[:3], 64)
        
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
    def __init__(self, plot_Widget, colour):
        super().__init__(plot_Widget, colour)
        
        self._hLine = pyqtgraph.InfiniteLine(angle=0,
                                      movable=False,
                                      pen=self._colour)
        self._vLine = pyqtgraph.InfiniteLine(angle=90,
                                      movable=False,
                                      pen=self._colour)
        self._lines = (self._hLine,
                       self._vLine)
        
        
class Integral_Cursor(Generic_Cursor):
    def __init__(self, plot_Widget, colour, resolution):
        super().__init__(plot_Widget, colour)
        
        self._left_Line = pyqtgraph.InfiniteLine(angle=90,
                                      movable=False,
                                      pen=self._colour)
        self._right_Line = pyqtgraph.InfiniteLine(angle=90,
                                      movable=False,
                                      pen=self._colour)
        
        self._lines = (self._left_Line,
                       self._right_Line)
        
        self._data_Bins = (0, 0)
        
        self._width = 0
        self._left_Position = 0
        self._right_Position = 0
        self._resolution = resolution
        
        self.mean_Bar = None
        self.max_Bar = None
    
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
    
    @property
    def resolution(self):
        return self._resolution
    
    @resolution.setter
    def resolution(self, value):
        self._resolution = value
        # Resolution change means the left and right lines need to be updated
        # since the scaling from time->bins has changed. The bars will take
        # care of themselves on the next data update
        self._Update_Lines()

    def _Update_Lines(self):
        self._left_Position = self._coords[0] - (self._width / 2)
        self._right_Position = self._coords[0] + (self._width / 2)
        
        self._data_Bins = (
            int(self._left_Position / self._resolution),
            int(self._right_Position / self._resolution)
            )
        
        self._lines[0].setPos(self._left_Position)
        self._lines[1].setPos(self._right_Position)
        
    def Reset_Remove(self):
        self._coords = (0, 0)
        self._left_Position = 0
        self._right_Position = 0
        for line in self._lines:
            line.setPos(0)
        self.Remove_From_Plot()
        
    def Update_Stats(self, data, display_Bars):
        integral_Data = data[self._data_Bins[0]: self._data_Bins[1]]

        if len(integral_Data) == 0:
            mean_Value = 0
            max_Value = 0
            fwhm_Value = 0
        else:    
            mean_Value = integral_Data.mean()
            max_Value = integral_Data.max()
            fwhm_Value = sum(integral_Data > (max_Value / 2)) * self._resolution
                        
            if display_Bars:
                self.mean_Bar = pyqtgraph.BarGraphItem(
                    x0 = [self._left_Position],
                    x1 = [self._right_Position],
                    height = [mean_Value],
                    pen = self._colour,
                    brush = self._colour
                    )
                
                self.max_Bar = pyqtgraph.BarGraphItem(
                    x0 = [self._left_Position],
                    x1 = [self._right_Position],
                    height = [max_Value],
                    pen = self._colour,
                    brush = self._colour_Alpha
                    )        
                
                self.Add_Bars()
            else:
                self.Remove_Bars()
            
        return mean_Value, max_Value, fwhm_Value
    
    def Add_Bars(self):
        for bar in [self.mean_Bar, self.max_Bar]:
            if isinstance(bar, type(None)):
                pass
            else:
                self._plot_Widget.addItem(bar)        
    
    def Remove_Bars(self):
        for bar in [self.mean_Bar, self.max_Bar]:
            if isinstance(bar, type(None)):
                pass
            else:
                self._plot_Widget.removeItem(bar)
    
if __name__ == "__main__":
    ...