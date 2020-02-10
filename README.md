# LD_Pharppy
Cross platform thanks to Picoquant's phlib. It's developed and tested in Ubuntu 18.04 so caution is advised for Windows users.

Basically this was born from from a confluence of necessity and an adventure into writing GUIs. My lab is almost 100% Linux compatible so it was becoming frustrating every time I needed a TCSPC histogram to have to disconnect a load of hardware and switch PCs. 

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
- (Windows) todo. For now run "python3 main.py".
- Initially the histogramming is off and the count rates of the two channels is displayed.
- Set the input parameters etc and press start/stop to start the histogramming
- Histogram will appear, the plot can be dragged around and variously controlled in the right click menu.
- Last histogram acquired will persist in the graph when start/stop is pressed.
- Last histogram can be saved to file for offline analysis.

# TODOs
- Batch file to launch in Windows for those uncomfortable with the terminal.
- Get crosshairs for reading exact data values from the histograms.
- Set up a two click system like in the official software for reading deltas from the graph.
- Estimate FWHM
- Optional curve fitting to the histogram
- General QOL upgrades to the GUI, proper scaling of the window etc (at the moment I think it only works on 1920x1080 screens)
