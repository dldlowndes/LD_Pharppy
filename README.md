# LD_Pharppy
Cross platform thanks to Picoquant's phlib. It's developed and tested in Ubuntu 18.04 so caution is advised for Windows users.

Basically this was born from from a confluence of necessity and an adventure into writing GUIs. My lab is almost 100% Linux compatible so it was becoming frustrating every time I needed a TCSPC histogram to have to disconnect a load of hardware and switch PCs. 

Comments/questions/etc welcome, email me at david@lownd.es

# Setup (Linux)

## udev
Add a udev rule for the Picoharp: ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="0e0d", ATTRS{idProduct}=="0003", MODE="0666"
## Libraries
In the interest of not sharing code that isn't mine, you'll have to install phlib yourself (https://www.picoquant.com/dl_software/PicoHarp300/PicoHarp300_SW_and_DLL_v3_0_0_3.zip).
Pharppy looks in the default locations from the Picoquant phlib installer ("/usr/local/lib(64)/ph300/phlib.so") or (C:\\(System32/SysWOW64)\\phlib(64).dll)
## Python packages
Using your favourite technique (pip, anaconda etc), install:
- pyqt5
- pyqtgraph
- numpy

# Running
- (Linux) Run ./run_Pharppy and after a bit of setup, the gui will appear.
- (Windows) Click/run "run_Pharppy.bat"
- Initially the histogramming is off and the count rates of the two channels is displayed.
- Set the input parameters etc and press start/stop to start the histogramming
- Histogram will appear, the plot can be dragged around and variously controlled in the right click menu.
- Last histogram acquired will persist in the graph when start/stop is pressed.
- Last histogram can be saved to file for offline analysis.