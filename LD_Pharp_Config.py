"""
Classes to hold settings information for various aspects of LD_Pharppy.

Mirroring the structure in the ini files, the main class contains two separate
objects, Hardware_Settings and Software_Settings. Hardware_Settings is all the
settings that are sent to the device, Software_Settings influence the GUI
behaviour
"""

import configparser
import distutils.util

class Hardware_Settings():
    """
    Settings which are sent to the picoharp, these are almost directly passed
    in to the functions defined in phlib. (although the binning, and acq_Time
    effect the GUI functionality indirectly)
    """
    
    def __init__(self):
        """
        Set some super safe factory defaults, defining them in the code means
        that they can be used as a complete fallback if no ini files can be
        found anywhere.
        """
        
        # Defaults
        self._binning = 0
        self._sync_Offset = 0
        self._sync_Divider = 1
        self._CFD0_ZeroCrossing = 10
        self._CFD0_Level = 50
        self._CFD1_ZeroCrossing = 10
        self._CFD1_Level = 50
        self._acq_Time = 500

    def to_Dict(self):
        """
        Mostly for printing but potentially useful in and of itself.
        """
        params = {"Binning": str(self.binning),
                  "Sync Offset": str(self.sync_Offset),
                  "Sync Divider": str(self.sync_Divider),
                  "CFD0 Zero Crossing": str(self.CFD0_ZeroCrossing),
                  "CFD0 Level": str(self.CFD0_Level),
                  "CFD1 Zero Crossing": str(self.CFD1_ZeroCrossing),
                  "CFD1 Level": str(self.CFD1_Level),
                  "Acquisition Time": str(self.acq_Time)
                  }
        return params

    def __repr__(self):
        """
        Dictionary converted to a string is probably the laziest way of doing
        this but it's effective and clear.
        """
        return str(self.to_Dict())

    @property
    def binning(self):
        return self._binning

    @binning.setter
    def binning(self, value):
        self._binning = int(value)

    @property
    def sync_Offset(self):
        return self._sync_Offset

    @sync_Offset.setter
    def sync_Offset(self, value):
        self._sync_Offset = int(value)

    @property
    def sync_Divider(self):
        return self._sync_Divider

    @sync_Divider.setter
    def sync_Divider(self, value):
        self._sync_Divider = int(value)

    @property
    def CFD0_ZeroCrossing(self):
        return self._CFD0_ZeroCrossing

    @CFD0_ZeroCrossing.setter
    def CFD0_ZeroCrossing(self, value):
        self._CFD0_ZeroCrossing = int(value)

    @property
    def CFD0_Level(self):
        return self._CFD0_Level

    @CFD0_Level.setter
    def CFD0_Level(self, value):
        self._CFD0_Level = int(value)

    @property
    def CFD1_ZeroCrossing(self):
        return self._CFD1_ZeroCrossing

    @CFD1_ZeroCrossing.setter
    def CFD1_ZeroCrossing(self, value):
        self._CFD1_ZeroCrossing = int(value)

    @property
    def CFD1_Level(self):
        return self._CFD1_Level

    @CFD1_Level.setter
    def CFD1_Level(self, value):
        self._CFD1_Level = int(value)

    @property
    def acq_Time(self):
        return self._acq_Time

    @acq_Time.setter
    def acq_Time(self, value):
        value = int(value)
        # There's some value here where the GUI just locks up because too much
        # time is being spent updating the histograms/ Ensure >250ms for now.
        if (value < 250):
            print(f"Acq time of {value} too short for GUI to remain responsive")
            print(f"Value set to 250 instead")
            value = 250
        self._acq_Time = value


class Software_Settings():
    """
    Settings that influence the GUI, the hardware is totally unaware of these
    values.
    """
    
    def __init__(self):
        """
        Set some super safe factory defaults, defining them in the code means
        that they can be used as a complete fallback if no ini files can be
        found anywhere.
        """
        
        # Defaults
        self._show_Cursor = True
        self._show_Deltas = True
        self._show_Bars = True
        self._integral_Width = 5e-9
        self._cumulative_Mode = False
        self._log_Y = False

    def to_Dict(self):
        """
        Mostly for printing but potentially useful in and of itself.
        """
        config = {"Show Cursor": str(self.show_Cursor),
                  "Show Deltas": str(self.show_Deltas),
                  "Show Bars": str(self.show_Bars),
                  "Integral Width": str(self.integral_Width),
                  "Cumulative Mode": str(self._cumulative_Mode),
                  "Log Y": str(self._log_Y)
                  }
        return config
    
    def __repr__(self):
        """
        Dictionary converted to a string is probably the laziest way of doing
        this but it's effective and clear.
        """
        return str(to_Dict)

    @property
    def show_Cursor(self):
        return self._show_Cursor

    @show_Cursor.setter
    def show_Cursor(self, value):
        self._show_Cursor = bool(distutils.util.strtobool(value))

    @property
    def show_Deltas(self):
        return self._show_Deltas

    @show_Deltas.setter
    def show_Deltas(self, value):
        self._show_Deltas = bool(distutils.util.strtobool(value))

    @property
    def show_Bars(self):
        return self._show_Bars

    @show_Bars.setter
    def show_Bars(self, value):
        self._show_Bars = bool(distutils.util.strtobool(value))

    @property
    def integral_Width(self):
        return self._integral_Width
    
    @integral_Width.setter
    def integral_Width(self, value):
        self._integral_Width = float(value)
        
    @property
    def cumulative_Mode(self):
        return self._cumulative_Mode
    
    @cumulative_Mode.setter
    def cumulative_Mode(self, value):
        self._cumulative_Mode = bool(distutils.util.strtobool(value))

    @property
    def log_Y(self):
        return self._log_Y
    
    @log_Y.setter
    def log_Y(self, value):
        self._log_Y = bool(distutils.util.strtobool(value))


class LD_Pharp_Config():
    """
    Container for Hardware_Settings and Software_Settings so they can be
    handled as a single object (since, to an end user, all the settings
    equally effect the experience of using this program)
    """
    
    def __init__(self, config_File=None):
        """
        Hardware_Settings and Software_Settings are initted with default
        values in their initializers. If config_File is supplied, the ini is
        read and the values are updated in this initializer.
        """
        
        self.hw_Settings = Hardware_Settings()
        self.sw_Settings = Software_Settings()

        if config_File:
            self.Load_From_File(config_File)

    def to_Dict(self):
        """
        Actually useful since configparser objects are addressed like dicts of
        dicts, this can be used to get the settings back into a format that
        configparser understands.
        """
        
        # Separate dicts of the component parts
        hw = self.hw_Settings.to_Dict()
        sw = self.sw_Settings.to_Dict()
        
        # Dict of both together. Keys here mirror the section titles in the
        # ini files.
        my_Dict = {
            "Hardware Settings": hw,
            "Software Settings": sw            
            }
        return my_Dict

    def __repr__(self):
        """
        Dictionary converted to a string is probably the laziest way of doing
        this but it's effective and clear.
        """
        return str(self.to_Dict())
    
    def Load_From_File(self, path):
        """
        Load an ini from file and populate the values in Hardware_Settings and
        Software_Settings, they are read as strings which is why the properties
        in the settings classes all have setters.
        """
        
        config = configparser.ConfigParser()
        config.read(path)
        #print(f"Read config file from {path}")

        hw_Settings = config["Hardware Settings"]
        sw_Settings = config["Software Settings"]

        # Really feels like there's a more concise/pythonic way of doing this
        self.hw_Settings.binning = hw_Settings["Binning"]
        self.hw_Settings.sync_Offset = hw_Settings["Sync Offset"]
        self.hw_Settings.sync_Divider = hw_Settings["Sync Divider"]
        self.hw_Settings.CFD0_ZeroCrossing = hw_Settings["CFD0 Zero Crossing"]
        self.hw_Settings.CFD0_Level = hw_Settings["CFD0 Level"]
        self.hw_Settings.CFD1_ZeroCrossing = hw_Settings["CFD1 Zero Crossing"]
        self.hw_Settings.CFD1_Level = hw_Settings["CFD1 Level"]
        self.hw_Settings.acq_Time = hw_Settings["Acquisition Time"]

        self.sw_Settings.show_Cursor = sw_Settings["Show Cursor"]
        self.sw_Settings.show_Deltas = sw_Settings["Show Deltas"]
        self.sw_Settings.show_Bars = sw_Settings["Show Bars"]
        self.sw_Settings.integral_Width = sw_Settings["Integral Width"]
        self.sw_Settings.cumulative_Mode = sw_Settings["Cumulative Mode"]
        self.sw_Settings.log_Y = sw_Settings["Log Y"]


    def Save_To_File(self, path):
        if not path.endswith(".ini"):
            path += ".ini"

        with open(path, "w") as out_File:
            config = configparser.ConfigParser()
            # config["Hardware Settings"] = self.hw_Settings.to_Dict()
            # config["Software Settings"] = self.sw_Settings.to_Dict()
            config.read_dict(self.to_Dict())

            config.write(out_File)

if __name__ == "__main__":
    cfg = LD_Pharp_Config("defaults.ini")