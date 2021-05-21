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

        print("Settings constructed")

    def __repr__(self):
        params = {"Binning": self.binning,
                  "Sync Offset": self.sync_Offset,
                  "Sync Divider": self.sync_Divider,
                  "CFD0 Zero Crossing": self.CFD0_ZeroCrossing,
                  "CFD0 Level": self.CFD0_Level,
                  "CFD1 Zero Crossing": self.CFD1_ZeroCrossing,
                  "CFD1 Level": self.CFD1_Level,
                  "Acq. Time": self.acq_Time
                  }
        return str(params)

    @property
    def binning(self):
        return self._binning

    @binning.setter
    def binning(self, value):
        self._binning = value

    @property
    def sync_Offset(self):
        return self._sync_Offset

    @sync_Offset.setter
    def sync_Offset(self, value):
        self._sync_Offset = value

    @property
    def sync_Divider(self):
        return self._sync_Divider

    @sync_Divider.setter
    def sync_Divider(self, value):
        self._sync_Divider = value

    @property
    def CFD0_ZeroCrossing(self):
        return self._CFD0_ZeroCrossing

    @CFD0_ZeroCrossing.setter
    def CFD0_ZeroCrossing(self, value):
        self._CFD0_ZeroCrossing = value

    @property
    def CFD0_Level(self):
        return self._CFD0_Level

    @CFD0_Level.setter
    def CFD0_Level(self, value):
        self._CFD0_Level = value

    @property
    def CFD1_ZeroCrossing(self):
        return self._CFD1_ZeroCrossing

    @CFD1_ZeroCrossing.setter
    def CFD1_ZeroCrossing(self, value):
        self._CFD1_ZeroCrossing = value

    @property
    def CFD1_Level(self):
        return self._CFD1_Level

    @CFD1_Level.setter
    def CFD1_Level(self, value):
        self._CFD1_Level = value

    @property
    def acq_Time(self):
        return self._acq_Time

    @acq_Time.setter
    def acq_Time(self, value):
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

    @property
    def show_Cursor(self):
        return self._show_Cursor

    @show_Cursor.setter
    def show_Cursor(self, value):
        self._show_Cursor = value

    @property
    def show_Deltas(self):
        return bool(distutils.util.strtobool(self._show_Deltas))

    @show_Deltas.setter
    def show_Deltas(self, value):
        self._show_Deltas = value

    @property
    def show_Bars(self):
        return bool(distutils.util.strtobool(self._show_Bars))

    @show_Bars.setter
    def show_Bars(self, value):
        self._show_Bars = value

    def Load_From_File(self, path):
        config = configparser.ConfigParser()
        config.read(path)

        hw_Settings = config["Hardware Settings"]
        sw_Settings = config["Software Settings"]

        self.Device_Settings.binning = int(
            hw_Settings["Binning"]
            )
        self.Device_Settings.sync_Offset = int(
            hw_Settings["Sync Offset"]
            )
        self.Device_Settings.sync_Divider = int(
            hw_Settings["Sync Divider"]
            )
        self.Device_Settings.CFD0_ZeroCrossing = int(
            hw_Settings["CFD0 Zero Crossing"]
            )
        self.Device_Settings.CFD0_Level = int(
            hw_Settings["CFD0 Level"]
            )
        self.Device_Settings.CFD1_ZeroCrossing = int(
            hw_Settings["CFD1 Zero Crossing"]
            )
        self.Device_Settings.CFD1_Level = int(
            hw_Settings["CFD1 Level"]
            )
        self.Device_Settings.acq_Time = int(
            hw_Settings["Acquisition Time"]
            )

        self.show_Cursor = bool(
            distutils.util.strtobool(sw_Settings["Show Cursor"])
            )
        self.show_Deltas = bool(
            distutils.util.strtobool(sw_Settings["Show Deltas"])
            )
        self.show_Bars = bool(
            distutils.util.strtobool(sw_Settings["Show Bars"])
            )

    def Save_To_File(self, path):
        if path.endswidth("defaults.ini"):
            raise ValueError

        with open(path, "w") as out_File:
            config.write(out_File)

if __name__ == "__main__":
    cfg = LD_Pharppy_Settings("defaults.ini")