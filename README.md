# LD_Pharppy
Cross platform thanks to Picoquant's phlib, even if their GUI is Windows only.

Basically this was born from from a confluence of necessity and an adventure into writing GUIs. My lab is almost 100% Linux compatible so it was becoming frustrating every time I needed a TCSPC histogram to have to disconnect a load of hardware and switch PCs. Meanwhile the Covid-19 pandemic lockdown meant I suddently had plenty of time to sit at home and do programming instead of lab work!

Comments/questions/etc welcome, email me at david@lownd.es

# Contributing
Please feel free to fork and adapt for your specific lab's requirements. I'll consider PRs for any general improvements, or will consider feature requests by email (although I'm finding less and less free time to work on this). I might also read your PR and then reimplement your feature myself (I'll check if you mind first and am happy to credit you if you are!)

Please see CONTRIBUTING.MD for some notes on the project structure and what some of the different files do.

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