# LD_Pharppy
GUI for Picoquant Picoharp300 in TCSPC histogramming mode. Uses phlib so interface so *should* be cross platform.

Comments/questions/etc welcome, email me at david@lownd.es

# Setup
## udev
Add a udev rule for the Picoharp: ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="0e0d", ATTRS{idProduct}=="0003", MODE="0666"
## Libraries
In the interest of not sharing code that isn't mine, you'll have to install phlib yourself. Pharppy looks in the default locations from the Picoquant phlib installer ("/usr/local/lib(64)/ph300/phlib.so") or (C:\\(System32/SysWOW64)\\phlib(64).dll)
## Python packages
Using your favourite technique, install pyqt5, pyqtgraph and numpy.

# Running
- (Linux) Run ./run_Pharpy and after a bit of setup, the gui will appear.
- (Windows) todo. for now run "python3 main.py".
- Initially the histogramming is off and the count rates of the two channels is displayed.
- Set the input parameters etc and press start/stop to start the histogramming
- Histogram will appear, the plot can be dragged around and variously controlled in the right click menu.
- Last histogram acquired will persist in the graph when start/stop is pressed.
- Last histogram can be saved to file for offline analysis.
