"""
Uses LD_PharpDLL to make an interface to the Picoharp300's histogramming
mode for humans to use.
"""

# pylint: disable=C0103
# pylint: disable=R0902

import logging

import LD_PharpDLL
import LD_Pharp_Config
import numpy as np


class LD_Pharp:
    def __init__(self, device_Number=0, pharp_Config=None, dll_Path=None):
        """
        Binning:
            How many bins of width "resolution" to combine to output the
            histogram. Number of bins combined are 2**binning. Changes the
            resolution by this factor compared to the base resolution.
        Sync Offset:
            Emulates adding a cable delay to sync input (ch0)
            (+ve value is longer delay)
        Acquisition Time:
            In milliseconds.
        Sync_Divider:
            Divides the clock on the sync channel (ch0)
        CFD_...:
            Zerocross and discriminator level for channels 0 and 1

        """

        self.logger = logging.getLogger("PHarp.Hardware")
        logging.basicConfig(level=logging.DEBUG)

        if isinstance(pharp_Config, type(None)):
            self.logger.debug("Making default HW settings")
            self.hw_Settings = LD_Pharp_Config.LD_Pharp_Config().hw_Settings
            self.router_Settings = LD_Pharp_Config.LD_Pharp_Config().router_Settings
        else:
            self.logger.debug("HW Settings passed in")
            self.hw_Settings = pharp_Config.hw_Settings
            self.router_Settings = pharp_Config.router_Settings
            print(f"router setting: {self.router_Settings}")

        # Connect to the Picoharp device.
        self.my_PharpDLL = LD_PharpDLL.LD_PharpDLL(device_Number, dll_Path)

        # TODO: Check this is the expected version.
        self.library_Version = self.my_PharpDLL.Get_LibraryVersion()

        # Housekeeping for getting the Picoharp up.
        self.my_PharpDLL.Open()
        self.my_PharpDLL.Initialize(LD_Pharp_Config.phdefine_h["MODE_HIST"])
        self.hardware_Info = self.my_PharpDLL.Get_HardwareInfo()
        self.my_PharpDLL.Calibrate()

        # Get base resolution from the device.
        #self.base_Resolution = self.my_PharpDLL.Get_BaseResolution()
        # Base resolution is 4ps. For some reason Get_BaseResolution doesn't
        # work on Windows so for now it's hard coded.
        # TODO: Fix base resolution on Windows.
        self.base_Resolution = 4.0  # picoseconds
        self.logger.debug(f"Base Resolution is {self.base_Resolution}ps")
        # Also read the resolution the Picoharp thinks it has (considering
        # also the binning)
        self.resolution = self.my_PharpDLL.Get_Resolution()
        self.logger.debug(f"Resolution is {self.resolution}")

        self.Update_Settings(self.hw_Settings)

    def __del__(self):
        self.logger.debug(f"Bye")
        self.my_PharpDLL.Close()

    def Update_Settings(self, hw_Settings):
        """
        Even though args are best sent as an unpacked dict, enforcing the
        parameters separately enforces that they all get sent.
        """

        self.hw_Settings = hw_Settings
        # Set the ones that need to be set now with functions.
        self.my_PharpDLL.Set_SyncDiv(hw_Settings.sync_Divider)
        self.my_PharpDLL.Set_InputCFD(hw_Settings.CFD0_Level,
                                      hw_Settings.CFD0_ZeroCrossing,
                                      hw_Settings.CFD1_Level,
                                      hw_Settings.CFD1_ZeroCrossing
                                      )
        self.my_PharpDLL.Set_Binning(hw_Settings.binning)
        self.my_PharpDLL.Set_SyncOffset(hw_Settings.sync_Offset)
        # Figure out the resolution that is implied by the requested binning.
        new_Resolution = self.base_Resolution * (2 ** hw_Settings.binning)
        self.logger.debug(f"Asked for resolution {new_Resolution}")
        # Check that the resolution requested is the same as the resolution
        # the Picoharp thinks it's providing.
        self.resolution = self.my_PharpDLL.Get_Resolution()
        self.logger.debug(f"New resolution is {self.resolution}")

        if self.hw_Settings.router_Enabled:
            self.my_PharpDLL.Set_RoutingEnable(True)
            for i in range(4):
                # The number of routing channels is hard-coded for now.
                # Only TTL mode is supported.
                self.my_PharpDLL.Set_RoutingChannelOffset(i, self.router_Settings.router_Offset[i])
                self.my_PharpDLL.Set_PHR800Input(i, self.router_Settings.PHR800_Level[i], self.router_Settings.PHR800_Edge[i])
                # self.my_PharpDLL.Set_PHR800CFD(i, self.router_Settings.PHR800_CFD_Level[i], self.router_Settings.PHR800_CFD_ZC[i])
                # print(f"{i}-th channel: offset: {self.router_Settings.router_Offset[i]}, phr800 level: {self.router_Settings.PHR800_Level[i]}, phr800 edge: {self.router_Settings.PHR800_Edge[i]}, cfd level: {self.router_Settings.PHR800_CFD_Level[i]}, cfd zc: {self.router_Settings.PHR800_CFD_ZC[i]}")
        else:
            self.my_PharpDLL.Set_RoutingEnable(False)


    def Get_CountRate(self):
        """
        Returns both channel count rates in a python list.
        """
        count_Channels = self.my_PharpDLL.Get_CountRate()
        return count_Channels

    # deprecated - not used ever since router is implemented
    def Get_A_Histogram(self, n_Channels=65536):
        """
        Returns the time tagging histogram as a python list. It's always the
        full number of channels that can be supplied by the Picoharp. They can
        be trimmed later.
        """
        # If this isn't called, the histogram is a cumulative one rather than
        # a single shot.
        # TODO: Optionally be able to clear this?
        self.my_PharpDLL.ClearHistMem()

        self.my_PharpDLL.Start(self.hw_Settings.acq_Time)

        # Ask the Picoharp if it's done yet. Either because acq_Time has passed
        # or because a bin in the histogram has been filled.
        # TODO: Start using 3.8 or whatever for walrus operator
        ctc = self.my_PharpDLL.Get_CTCStatus()
        while ctc == 0:
            ctc = self.my_PharpDLL.Get_CTCStatus()
        # Manual says you still have to explicitly stop the Picoharp.
        self.my_PharpDLL.Stop()

        # Pull the histogram off the Picoharp.
        histogram = self.my_PharpDLL.Get_Histogram(0, n_Channels)

        # Some Picoharp status stuff that might be useful?
        # flags = self.my_PharpDLL.Get_Flags()
        # time = self.my_PharpDLL.Get_ElapsedMeasTime()
        # print(f"Flags {flags}")
        return histogram

    # for routed case
    def Get_Histograms(self, n_Channels=65536):
        """
        Returns the time tagging histogram as a python list. It's always the
        full number of channels that can be supplied by the Picoharp. They can
        be trimmed later.
        """
        # If this isn't called, the histogram is a cumulative one rather than
        # a single shot.
        # TODO: Optionally be able to clear this?
        if self.hw_Settings.router_Enabled:
            for ch in range(4):
                self.my_PharpDLL.ClearHistMem(ch)
        else:
            self.my_PharpDLL.ClearHistMem(0)

        self.my_PharpDLL.Start(self.hw_Settings.acq_Time)

        # Ask the Picoharp if it's done yet. Either because acq_Time has passed
        # or because a bin in the histogram has been filled.
        # TODO: Start using 3.8 or whatever for walrus operator
        ctc = self.my_PharpDLL.Get_CTCStatus()
        while ctc == 0:
            ctc = self.my_PharpDLL.Get_CTCStatus()
        # Manual says you still have to explicitly stop the Picoharp.
        self.my_PharpDLL.Stop()

        # Pull the histogram off the Picoharp.
        histogram = np.empty((0,n_Channels),int)
        if self.hw_Settings.router_Enabled:
            for ch in range(4):
                histogram = np.append(histogram, np.array([self.my_PharpDLL.Get_Histogram(ch, n_Channels)]),axis=0)
                # print(f"Get_RouterVersion: {self.my_PharpDLL.Get_RouterVersion()}")
        else:
            histogram = np.append(histogram, np.array([self.my_PharpDLL.Get_Histogram(0, n_Channels)]),axis=0)


        # Some Picoharp status stuff that might be useful?
        # flags = self.my_PharpDLL.Get_Flags()
        # time = self.my_PharpDLL.Get_ElapsedMeasTime()
        # print(f"Flags {flags}")
        # print(histogram)
        return histogram

    def Get_Warnings(self):
        warn_Code = self.my_PharpDLL.Get_Warnings()
        warn_Text = self.my_PharpDLL.Get_WarningsText(warn_Code)
        # Strip any multiple newlines, and also the trailing newline.
        return warn_Text.replace("\n\n\n", "\n").replace("\n\n", "\n")[:-1]

if __name__ == "__main__":
    my_LDPharp = LD_Pharp()

    print(f"Count rate: {my_LDPharp.Get_CountRate()}")

    warns = my_LDPharp.Get_Warnings()
    print(warns)
