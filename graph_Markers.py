from PyQt5 import QtGui

import pyqtgraph

class Generic_Cursor():
    """
    Very generic concept of a cursor. Doesn't even define the lines, just
    keeps track of the high level properties of it. Does specifically have two
    lines though.
    """
    def __init__(self, plot_Widget = None, colour = None):
        """
        Initializer takes plot_Widget as an argument, otherwise it can be set
        later. This will probably behave weirdly if you change this dynamically
        If colour is not supplied, defaults to white.
        """
        self._coords = (0, 0)
        #self._is_enabled = False
        
        if isinstance(colour, type(None)):
            self._colour = QtGui.QColor(255, 255, 255)
        else:
            self._colour = colour
            
        self._colour_Alpha = QtGui.QColor(*self._colour.getRgb()[:3], 64)
        
        self._lines = ()
        
        self._plot_Widget = plot_Widget
        
    @property
    def coords(self):
        """
        The coordinates defining the cursor. Since this is likely defined by
        a click or other event on the plot, should be set as a tuple of the
        form (x, y).
        """
        return self._coords
    
    @coords.setter
    def coords(self, value):

        x, y, = value
        self._coords = (x ,y)
        self._lines[0].setPos(y)
        self._lines[1].setPos(x)
        
    @property
    def colour(self):
        """
        The colour of the cursor, as a QColor object. Having one cursor have
        multiple colours seems like madness and is not allowed here.
        """
        return self._colour
    
    @colour.setter
    def colour(self, value=QtGui.QColor(255, 255, 255)):
        self._colour = value
        self._lines[0].setPen(self._colour)
        self._lines[1].setPen(self._colour)
    
    # @property
    # def is_Enabled(self):
    #     """
    #     I think this is unused...
    #     """
    #     return self._is_enabled
    
    # @is_Enabled.setter
    # def is_Enabled(self, value):
    #     self._is_enabled = value
        
    def Add_To_Plot(self):
        """
        Add the cursor to the plot
        """
        self._plot_Widget.addItem(self._lines[0])
        self._plot_Widget.addItem(self._lines[1])
        
    def Remove_From_Plot(self):
        """
        Remove the cursor from the plot
        """
        self._plot_Widget.removeItem(self._lines[0])
        self._plot_Widget.removeItem(self._lines[1])
        
    def Attach_To_Widget(self, plot_Widget):
        """
        Set/change the plot widget this cursor is connected to.
        """
        self._plot_Widget = plot_Widget
        
        
class XY_Cursor(Generic_Cursor):
    """
    A cursor with one horizontal line and one vertical. The intersection of
    these two lines is the point specified by the coordinates of the cursor.
    Most likely this will correspond to a click or mouseover location.
    Inherits from Generic_Cursor so this mostly just sets the specifics of the
    lines
    """
    def __init__(self, plot_Widget, colour):
        """
        The plot widget this cursor should be applied to, and the colour (as
        a QColor object) 
        """
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
    """
    Two vertical lines that are some width apart, centred on the y coordinate
    of coords.
    Bars can be plotted between the cursor lines reflecting statistics of the
    data between the lines.
    """
    def __init__(self, plot_Widget, colour, resolution):
        """
        The plot widget this cursor should be applied to, and the colour (as
        a QColor object)
        In order to be able to interpret the data, needs to know the x scale,
        passed in here as "resolution". 
        """
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
        """
        Separation of the vertical lines, in units of the x axis.
        """
        return self._width
    
    @width.setter
    def width(self, value):
        self._width = value
        self._Update_Lines()
        
    @property
    def coords(self):
        """
        Overrides the base class because the line positions aren't directly
        defined by the coordinates passed.
        Coords passed as tuple (x, y), although y is ignored.
        """
        return self._coords
    
    @coords.setter
    def coords(self, value):
        x, y, = value
        self._coords = (x, y)
        self._Update_Lines()
    
    @property
    def resolution(self):
        """
        Resolution of x values, given that the data is passed in as y values,
        need to be able to map element number in the data to an x value.
        """
        return self._resolution
    
    @resolution.setter
    def resolution(self, value):
        self._resolution = value
        # Resolution change means the left and right lines need to be updated
        # since the scaling from time->bins has changed. The bars will take
        # care of themselves on the next data update
        self._Update_Lines()

    def _Update_Lines(self):
        """
        Updates the two vertical lines. This gets called if the coordinates,
        width or resolution change.
        """
        self._left_Position = self._coords[0] - (self._width / 2)
        self._right_Position = self._coords[0] + (self._width / 2)
        
        # Which elements in the data array correspond to the coordinates of
        # the lines?
        self._data_Bins = (
            int(self._left_Position / self._resolution),
            int(self._right_Position / self._resolution)
            )
        
        # Move the lines
        self._lines[0].setPos(self._left_Position)
        self._lines[1].setPos(self._right_Position)
        
    def Reset_Remove(self):
        """
        If desired, shunt all the lines to 0 (best default position I can
        think of). Then remove everything, note that setting the lines to zero
        automatically removes the bars because they are defined by those 
        values.
        """
        
        self._coords = (0, 0)
        self._left_Position = 0
        self._right_Position = 0
        for line in self._lines:
            line.setPos(0)
        self.Remove_From_Plot()
        
    def Update_Stats(self, data, display_Bars):
        """
        Calculate mean, max, fwhm of the data between the two markers.
        Optionally plot bars between the markers of the mean and max values.
        data should be an np.ndarray, display_Bars a boolean.
        Returns a tuple (mean, max, fwhm) so the caller can actually do
        something with them (like display on a GUI?)
        """
        
        # Get the data between the bars
        integral_Data = data[self._data_Bins[0]: self._data_Bins[1]]

        # If there isn't any data (usually this is if the cursor hasn't been
        # placed yet, or the width is accidentally 0), set everything to zero
        if len(integral_Data) == 0:
            mean_Value = 0
            max_Value = 0
            max_Pos = 0
            fwhm_Value = 0
        else:    
            # Calculate the values
            mean_Value = integral_Data.mean()
            max_Value = integral_Data.max()
            max_Pos = self._left_Position + integral_Data.argmax() * self._resolution
            fwhm_Value = sum(integral_Data > (max_Value / 2)) * self._resolution
                        
            if display_Bars:
                # Make some bars objects and add them to the plot widget.
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
                # If display bars is off, best make sure the bars aren't on
                # the widget right now.
                self.Remove_Bars()
        
        return mean_Value, max_Value, max_Pos, fwhm_Value
    
    def Add_Bars(self):
        """
        Add the bars to the plot widget, if they exist.
        """
        for bar in [self.mean_Bar, self.max_Bar]:
            if isinstance(bar, type(None)):
                pass
            else:
                self._plot_Widget.addItem(bar)        
    
    def Remove_Bars(self):
        """
        Remove the bars from the plot widget, if they exist.
        """
        for bar in [self.mean_Bar, self.max_Bar]:
            if isinstance(bar, type(None)):
                pass
            else:
                self._plot_Widget.removeItem(bar)
    
if __name__ == "__main__":
    pass