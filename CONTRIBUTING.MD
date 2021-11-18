# Project Structure
## LD_Pharp_DLL.py and LD_Pharp.py
LD_Pharp_DLL.py is the thinnest imaginable wrapper to phlib.dll without just using the ctypes library directly.
LD_Pharp.py is a more human-friendly wrapper, which has methods which call things from LD_Pharp_DLL. This has methods with sensible names and some QoL features (see LD_Pharp_Config.py)

## LD_Pharp_Dummy.py
Has the same methods as LD_Pharp but doesn't connect to hardware. When data is requested it generates a gaussian histogram with some random noise added for... authenticity?. Anyway, this is mostly for developing the GUI where it's nice to have incoming data without having to be adjacent to the hardware while developing.

## LD_Pharp_Config.py
Contains classes (Hardware_Settings, Software_Settings) for holding the parameters for the Picoharp hardware, and the GUI respectively. Also contains a class LD_Pharp_Config which contains one of each of Hardware_Settings and Software_Settings and some methods to save to file and print etc.

## acq_Thread.py
Called by main.py in the GUI, making a thread which polls the hardware (via LD_Pharp.py) periodically and emits a signal containing the counts/histogram data when some arrives.

## graph_Markers.py
Graph markers became a big enough code distraction that they ended up getting their own file. In an general sense, the two types of cursor currently implemented are XY_Cursors which is one horizontal line and one vertical line, and Integral_Cursor which is two vertical lines separated by some preset distance.
An instance of Generic_Cursor has two lines, but doesn't specify things like what type of lines they are (meaning a subclass of this can set the orientation of each).
XY_Cursors generally represent a mouse click, or more generally a position on a graph. The Integral_Cursors represent a region of interest on the X axis and have a method for calculating some statistics of the graph data in that region.

## settings_gui.py and settings_gui.ui
settings_gui.py IS NOT FOR HUMAN EDITING, settings_gui.ui is edited using QT Designer and converted to settings_gui.py by running the command "pyuic5 settings_gui.ui > settings_gui.py" or by running "make_gui.bat" or "make_gui.sh" depending on your platform (Windows/Linux respectively).

# General Philosophy
I'm trying to keep this as relatively general-purpose, which in this case means that it should interface with the hardware settings, collect histograms and count rates from a picoharp, display them in various ways, and display values derived from these (statistical or otherwise).

# Extending
I would love to keep a list here of any forks that use this project as a base and extend it beyond the simple design here. I can't guarantee some of your ideas won't end up back in my project though :)

# Credits
If you do contribute, either directly by Pull Request, or indirectly by implementing something cool in a fork, I'll put your name in a CREDITS.MD file in this project (with your consent)