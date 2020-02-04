# LD_Pharppy
GUI for Picoquant Picoharp300 in TCSPC histogramming mode. Uses phlib so interface so *should* be cross platform.

# Setup
## udev
Add a udev rule for the Picoharp: ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="0e0d", ATTRS{idProduct}=="0003", MODE="0666"
## Libraries
In the interest of not sharing code that isn't mine, you'll have to provide your own phlib .dll (Windows) or .so (Linux). Drop it in this folder and the script will detect which one it needs.
## Python packages
Using your favourite technique, install pyqt5, pyqtgraph and numpy.

# Running
- Run ./run_Pharpy and after a bit of setup, the gui will appear.
- Initially the histogramming is off and the count rates of the two channels is displayed.
- Set the input parameters etc and press start/stop to start the histogramming
- Histogram will appear, the plot can be dragged around and variously controlled in the right click menu.
- Last histogram acquired will persist in the graph when start/stop is pressed.
- Last histogram can be saved to file for offline analysis.