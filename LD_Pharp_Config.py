import configparser
import distutils.util

class LD_Pharp_Config():
    def __init__(self, config_File=None):
        # Defaults
        self._binning = 0
        self._sync_Offset = 0
        self._sync_Divider = 1
        self._CFD0_ZeroCrossing = 10
        self._CFD0_Level = 50
        self._CFD1_ZeroCrossing = 10
        self._CFD1_Level = 50
        self._acq_Time = 500

        if config_File:
            self.Load_From_File(config_File)

    def to_Dict(self):
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
        if (value < 250):
            print(f"Acq time of {value} too short for GUI to remain responsive")
            print(f"Value set to 250 instead")
            value = 250
        self._acq_Time = value


class LD_Pharppy_Settings():
    def __init__(self, config_File=None):
        self.Device_Settings = LD_Pharp_Config()

        self._show_Cursor = True
        self._show_Deltas = True
        self._show_Bars = True

        if config_File:
            self.Load_From_File(config_File)

    def to_Dict(self):
        config = {"Show Cursor": str(self.show_Cursor),
                  "Show Deltas": str(self.show_Deltas),
                  "Show Bars": str(self.show_Bars)
                  }
        return config

    def __repr__(self):
        return str(self.to_Dict()) + self.Device_Settings.__repr__()

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

    def Load_From_File(self, path):
        config = configparser.ConfigParser()
        config.read(path)
        print(f"Read config file from {path}")

        hw_Settings = config["Hardware Settings"]
        sw_Settings = config["Software Settings"]

        self.Device_Settings.binning = hw_Settings["Binning"]
        self.Device_Settings.sync_Offset = hw_Settings["Sync Offset"]
        self.Device_Settings.sync_Divider = hw_Settings["Sync Divider"]
        self.Device_Settings.CFD0_ZeroCrossing = hw_Settings["CFD0 Zero Crossing"]
        self.Device_Settings.CFD0_Level = hw_Settings["CFD0 Level"]
        self.Device_Settings.CFD1_ZeroCrossing = hw_Settings["CFD1 Zero Crossing"]
        self.Device_Settings.CFD1_Level = hw_Settings["CFD1 Level"]
        self.Device_Settings.acq_Time = hw_Settings["Acquisition Time"]

        self.show_Cursor = sw_Settings["Show Cursor"]
        self.show_Deltas = sw_Settings["Show Deltas"]
        self.show_Bars = sw_Settings["Show Bars"]

    def Save_To_File(self, path):
        if not path.endswith(".ini"):
            path += ".ini"
        if path.endswith("defaults.ini"):
            raise ValueError

        with open(path, "w") as out_File:
            config = configparser.ConfigParser()
            config["Hardware Settings"] = self.Device_Settings.to_Dict()
            config["Software Settings"] = self.to_Dict()

            config.write(out_File)

if __name__ == "__main__":
    cfg = LD_Pharppy_Settings("defaults.ini")