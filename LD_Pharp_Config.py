"""
Classes to hold settings information for various aspects of LD_Pharppy.

Mirroring the structure in the ini files, the main class contains two separate
objects, Hardware_Settings and Software_Settings. Hardware_Settings is all the
settings that are sent to the device, Software_Settings influence the GUI
behaviour
"""

import configparser
import distutils.util

# Dunno what to do with this right now but it's in the source code now
# TODO: Use these?
phdefine_h = {
        "LIB_VERSION": "3.0",
        "MAXDEVNUM": 8,
        "HISTCHAN": 65536,
        "TTREADMAX": 131072,
        "MODE_HIST": 0,
        "MODE_T2": 2,
        "MODE_T3": 3,
        "FEATURE_DLL": 0x0001,
        "FEATURE_TTTR": 0x0002,
        "FEATURE_MARKERS": 0x0004,
        "FEATURE_LOWRES": 0x0008,
        "FEATURE_TRIGOUT": 0x0010,
        "FLAG_FIFOFULL": 0x0003,    # T-modes
        "FLAG_OVERFLOW": 0x0040,    # Histmode
        "FLAG_SYSERROR": 0x0100,    # Hardware problem
        "BINSTEPSMAX": 8,
        "SYNCDIVMIN": 1,
        "SYNCDIVMAX": 8,
        "ZCMIN": 0,    # mV
        "ZCMAX": 20,    # mV
        "DISCRMIN": 0,    # mV
        "DISCRMAX": 800,    # mV
        "OFFSETMIN": 0,    # ps
        "OFFSETMAX": 1000000000,    # ps
        "SYNCOFFSMIN": -99999,    # ps
        "SYNCOFFSMAX": 99999,    # ps
        "CHANOFFSMIN": -8000,    # ps
        "CHANOFFSMAX": 8000,    # ps
        "ACQTMIN": 1,    # ms
        "ACQTMAX": 360000000,    # ms
        "PHR800LVMIN": -1600,    # mV
        "PHR800LVMAX": 2400,    # mV
        "HOLDOFFMAX": 210480,    # ns
        "WARNING_INP0_RATE_ZERO": 0x0001,
        "WARNING_INP0_RATE_TOO_LOW": 0x0002,
        "WARNING_INP0_RATE_TOO_HIGH": 0x0004,
        "WARNING_INP1_RATE_ZERO": 0x0010,
        "WARNING_INP1_RATE_TOO_HIGH": 0x0040,
        "WARNING_INP_RATE_RATIO": 0x0100,
        "WARNING_DIVIDER_GREATER_ONE": 0x0200,
        "WARNING_TIME_SPAN_TOO_SMALL": 0x0400,
        "WARNING_OFFSET_UNNECESSARY": 0x0800
            # "PHR800Level": 1500,    # mV
            # "PHR800Edge": 1,    # not sure about this value
            # "PHR800CFDLevel": 0,    # mV , not sure about this value
            # "PHR800CFDZeroCross": 0    # mV
        }

# TODO: Check the error handler in Pharp_DLL already uses these.
errcodes_h = {
        "ERROR_NONE": 0,
        "ERROR_DEVICE_OPEN_FAIL": -1,
        "ERROR_DEVICE_BUSY": -2,
        "ERROR_DEVICE_HEVENT_FAIL": -3,
        "ERROR_DEVICE_CALLBSET_FAIL ": -4,
        "ERROR_DEVICE_BARMAP_FAIL": -5,
        "ERROR_DEVICE_CLOSE_FAIL": -6,
        "ERROR_DEVICE_RESET_FAIL": -7,
        "ERROR_DEVICE_GETVERSION_FAIL": -8,
        "ERROR_DEVICE_VERSION_MISMATCH ": -9,
        "ERROR_DEVICE_NOT_OPEN": -10,
        "ERROR_DEVICE_LOCKED": -11,
        "ERROR_INSTANCE_RUNNING": -16,
        "ERROR_INVALID_ARGUMENT": -17,
        "ERROR_INVALID_MODE": -18,
        "ERROR_INVALID_OPTION": -19,
        "ERROR_INVALID_MEMORY": -20,
        "ERROR_INVALID_RDATA": -21,
        "ERROR_NOT_INITIALIZED": -22,
        "ERROR_NOT_CALIBRATED": -23,
        "ERROR_DMA_FAIL": -24,
        "ERROR_XTDEVICE_FAIL": -25,
        "ERROR_FPGACONF_FAIL": -26,
        "ERROR_IFCONF_FAIL": -27,
        "ERROR_FIFORESET_FAIL": -28,
        "ERROR_STATUS_FAIL": -29,
        "ERROR_USB_GETDRIVERVER_FAIL": -32,
        "ERROR_USB_DRIVERVER_MISMATCH": -33,
        "ERROR_USB_GETIFINFO_FAIL": -34,
        "ERROR_USB_HISPEED_FAIL": -35,
        "ERROR_USB_VCMD_FAIL": -36,
        "ERROR_USB_BULKRD_FAIL": -37,
        "ERROR_HARDWARE_F01 ": -64,
        "ERROR_HARDWARE_F02": -65,
        "ERROR_HARDWARE_F03": -66,
        "ERROR_HARDWARE_F04": -67,
        "ERROR_HARDWARE_F05": -68,
        "ERROR_HARDWARE_F06": -69,
        "ERROR_HARDWARE_F07": -70,
        "ERROR_HARDWARE_F08": -71,
        "ERROR_HARDWARE_F09": -72,
        "ERROR_HARDWARE_F10": -73,
        "ERROR_HARDWARE_F11": -74,
        "ERROR_HARDWARE_F12": -75,
        "ERROR_HARDWARE_F13": -76,
        "ERROR_HARDWARE_F14": -77,
        "ERROR_HARDWARE_F15": -78
        }

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
        self._router_Enabled = 1 # 0 for false, otherwise true
        # self._router_Offset = [0, 0, 0, 0]
        # self._PHR800_Level = [1500, 1500, 1500, 1500]  # mV
        # self._PHR800_Edge = [1, 1, 1, 1]      # not sure about this value
        # self._PHR800_CFD_Level = [0, 0, 0, 0] # mV, not sure about this value
        # self._PHR800_CFD_ZC = [0, 0, 0, 0]     # mV

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
                  "Acquisition Time": str(self.acq_Time),
                  "Router Enabled": str(self.router_Enabled)
                  # "Router Offset": str(self.router_Offset),
                  # "PHR800 Level": str(self.PHR800_Level),
                  # "PHR800 Edge": str(self.PHR800_Edge),
                  # "PHR800 CFD Level": str(self.PHR800_CFD_Level),
                  # "PHR800 CFD ZC": str(self.PHR800_CFD_ZC)
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

    @property
    def router_Enabled(self):
        return self._router_Enabled

    @router_Enabled.setter
    def router_Enabled(self, value):
        self._router_Enabled = int(value)

class Router_Settings():
    """
    Ahreum: Router settings which are sent to the picoharp, these are almost directly passed
    in to the functions defined in phlib.
    """

    def __init__(self):
        """
        Set some super safe factory defaults, defining them in the code means
        that they can be used as a complete fallback if no ini files can be
        found anywhere.
        """

        # Defaults
        # self._router_Enabled = 0 # 0 for false, otherwise true
        self._router_Offset = [0, 0, 0, 0]
        self._PHR800_Level = [1500, 1500, 1500, 1500]  # mV
        self._PHR800_Edge = [1, 1, 1, 1]      # not sure about this value
        self._PHR800_CFD_Level = [0, 0, 0, 0] # mV, not sure about this value
        self._PHR800_CFD_ZC = [0, 0, 0, 0]     # mV

    def to_Dict(self):
        """
        Mostly for printing but potentially useful in and of itself.
        """
        router_offset = {"router1": str(self.router_Offset[0]),
                         "router2": str(self.router_Offset[1]),
                         "router3": str(self.router_Offset[2]),
                         "router4": str(self.router_Offset[3])}
        phr800_level = {"router1": str(self.PHR800_Level[0]),
                        "router2": str(self.PHR800_Level[1]),
                        "router3": str(self.PHR800_Level[2]),
                        "router4": str(self.PHR800_Level[3])}
        phr800_edge = {"router1": str(self.PHR800_Edge[0]),
                       "router2": str(self.PHR800_Edge[1]),
                       "router3": str(self.PHR800_Edge[2]),
                       "router4": str(self.PHR800_Edge[3])}
        phr800_cfd_level = {"router1": str(self.PHR800_CFD_Level[0]),
                            "router2": str(self.PHR800_CFD_Level[1]),
                            "router3": str(self.PHR800_CFD_Level[2]),
                            "router4": str(self.PHR800_CFD_Level[3])}
        phr800_cfd_zc = {"router1": str(self.PHR800_CFD_ZC[0]),
                         "router2": str(self.PHR800_CFD_ZC[1]),
                         "router3": str(self.PHR800_CFD_ZC[2]),
                         "router4": str(self.PHR800_CFD_ZC[3])}

        return {"Router Offset": router_offset,
                "PHR800 Level": phr800_level,
                "PHR800 Edge": phr800_edge,
                "PHR800 CFD Level": phr800_cfd_level,
                "PHR800 CFD ZC": phr800_cfd_zc}

    def __repr__(self):
        """
        Dictionary converted to a string is probably the laziest way of doing
        this but it's effective and clear.
        """
        return str(self.to_Dict())

    @property
    def router_Offset(self):
        return self._router_Offset

    @router_Offset.setter
    def router_Offset(self, valueDict):
        # PH300 only supports up to 4 channels when using router
        if len(valueDict) != 4:
            print(f"Number of router offset not match with number of routers")
            print(f"Offset set to 0 for all routers instead")
            self._router_Offset = [0 for i in range(4)]
            return

        # print(valueDict)
        value = []
        for i in valueDict:
            # print(f"valueDict[i]: {valueDict[i]}")
            if int(valueDict[i]) > 8000:
                print(f"Router offset {valueDict[i]} exceeds the maximum 8000")
                print(f"Offset set to 8000 instead")
                value.append(8000)
                continue
            elif int(valueDict[i]) < -8000:
                print(f"Router offset {valueDict[i]} exceeds the minimum -8000")
                print(f"Offset set to -8000 instead")
                value.append(-8000)
                continue
            value.append(int(valueDict[i]))

        self._router_Offset = value

    @property
    def PHR800_Level(self):
        return self._PHR800_Level

    @PHR800_Level.setter
    def PHR800_Level(self, valueDict):

        # if more or less than 4 levels are given
        if len(valueDict) != 4:
            print(f"Number of router levels not match with number of routers")
            print(f"Levels set to defaults for all routers instead")
            value = [1500 for i in range(4)]

        for i in valueDict:
            if int(valueDict[i]) < phdefine_h["PHR800LVMIN"]:
                print(f'PHR800 level of {value} lower than limitation {phdefine_h["PHR800LVMIN"]}')
                print(f'PHR800 level set to {phdefine_h["PHR800LVMIN"]}')
                valueDict[i] = phdefine_h["PHR800LVMIN"]
            if int(valueDict[i]) > phdefine_h["PHR800LVMAX"]:
                print(f'PHR800 level of {value} greater than limitation {phdefine_h["PHR800LVMAX"]}')
                print(f'PHR800 level set to {phdefine_h["PHR800LVMAX"]}')
                valueDict[i] = phdefine_h["PHR800LVMAX"]

        self._PHR800_Level = [int(valueDict[x]) for x in valueDict]

    @property
    def PHR800_Edge(self):
        return self._PHR800_Edge

    @PHR800_Edge.setter
    def PHR800_Edge(self, valueDict):

        # if more or less than 4 levels are given
        if len(valueDict) != 4:
            print(f"Number of router levels not match with number of routers")
            print(f"Levels set to defaults for all routers instead")
            value = [0 for i in range(4)]

        self._PHR800_Edge = [int(valueDict[x]) for x in valueDict]

    @property
    def PHR800_CFD_Level(self):
        return self._PHR800_CFD_Level

    @PHR800_CFD_Level.setter
    def PHR800_CFD_Level(self, valueDict):

        # if more or less than 4 levels are given
        if len(valueDict) != 4:
            print(f"Number of router levels not match with number of routers")
            print(f"Levels set to defaults for all routers instead")
            value = [0 for i in range(4)]

        # for i in valueDict:
        #     if valueDict[i] < phdefine_h["PHR800LVMIN"]:
        #         print(f'PHR800 level of {value} lower than limitation {phdefine_h["PHR800LVMIN"]}')
        #         print(f'PHR800 level set to {phdefine_h["PHR800LVMIN"]}')
        #         valueDict[i] = phdefine_h["PHR800LVMIN"]
        #     if valueDict[i] > phdefine_h["PHR800LVMAX"]:
        #         print(f'PHR800 level of {value} greater than limitation {phdefine_h["PHR800LVMAX"]}')
        #         print(f'PHR800 level set to {phdefine_h["PHR800LVMAX"]}')
        #         valueDict[i] = phdefine_h["PHR800LVMAX"]

        self._PHR800_CFD_Level = [int(valueDict[x]) for x in valueDict]

    @property
    def PHR800_CFD_ZC(self):
        return self._PHR800_CFD_ZC

    @PHR800_CFD_ZC.setter
    def PHR800_CFD_ZC(self, valueDict):
            # if more or less than 4 levels are given
            if len(valueDict) != 4:
                print(f"Number of router levels not match with number of routers")
                print(f"Levels set to defaults for all routers instead")
                value = [0 for i in range(4)]

            # for i in valueDict:
            #     if valueDict[i] < phdefine_h["PHR800LVMIN"]:
            #         print(f'PHR800 level of {value} lower than limitation {phdefine_h["PHR800LVMIN"]}')
            #         print(f'PHR800 level set to {phdefine_h["PHR800LVMIN"]}')
            #         valueDict[i] = phdefine_h["PHR800LVMIN"]
            #     if valueDict[i] > phdefine_h["PHR800LVMAX"]:
            #         print(f'PHR800 level of {value} greater than limitation {phdefine_h["PHR800LVMAX"]}')
            #         print(f'PHR800 level set to {phdefine_h["PHR800LVMAX"]}')
            #         valueDict[i] = phdefine_h["PHR800LVMAX"]

            self._PHR800_CFD_ZC = [int(valueDict[x]) for x in valueDict]

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
        self._max_t = 1000

    def to_Dict(self):
        """
        Mostly for printing but potentially useful in and of itself.
        """
        config = {"Show Cursor": str(self.show_Cursor),
                  "Show Deltas": str(self.show_Deltas),
                  "Show Bars": str(self.show_Bars),
                  "Integral Width": str(self.integral_Width),
                  "Cumulative Mode": str(self._cumulative_Mode),
                  "Log Y": str(self._log_Y),
                  "Max Time": str(self._max_t)
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

    @property
    def max_t(self):
        return self._max_t

    @max_t.setter
    def max_t(self, value):
        self._max_t = float(value)


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
        self.router_Settings = Router_Settings()

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
        router = self.router_Settings.to_Dict()

        # Dict of both together. Keys here mirror the section titles in the
        # ini files.
        my_Dict = {
            "Hardware Settings": hw,
            "Software Settings": sw,
            **router
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
        self.hw_Settings.router_Enabled = hw_Settings["Router Enabled"]

        self.router_Settings.router_Offset = dict(config["Router Offset"])
        self.router_Settings.PHR800_Level = dict(config["PHR800 Level"])
        self.router_Settings.PHR800_Edge = dict(config["PHR800 Edge"])
        self.router_Settings.PHR800_CFD_Level = dict(config["PHR800 CFD Level"])
        self.router_Settings.PHR800_CFD_ZC = dict(config["PHR800 CFD ZC"])

        self.sw_Settings.show_Cursor = sw_Settings["Show Cursor"]
        self.sw_Settings.show_Deltas = sw_Settings["Show Deltas"]
        self.sw_Settings.show_Bars = sw_Settings["Show Bars"]
        self.sw_Settings.integral_Width = sw_Settings["Integral Width"]
        self.sw_Settings.cumulative_Mode = sw_Settings["Cumulative Mode"]
        self.sw_Settings.log_Y = sw_Settings["Log Y"]
        self.sw_Settings.max_t = sw_Settings["max time"]


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
