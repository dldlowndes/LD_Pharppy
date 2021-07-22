"""
Uses LD_PharpDLL to make an interface to the Picoharp300's histogramming
mode for humans to use.
"""

# pylint: disable=C0103
# pylint: disable=R0902

import logging

import LD_PharpDLL
import LD_Pharp_Config

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
        "FLAG_FIFOFULL": 0x0003,
        "FLAG_OVERFLOW": 0x0040,
        "FLAG_SYSERROR": 0x0100,
        "BINSTEPSMAX": 8,
        "SYNCDIVMIN": 1,
        "SYNCDIVMAX": 8,
        "ZCMIN": 0,
        "ZCMAX": 20,
        "DISCRMIN": 0,
        "DISCRMAX": 800,
        "OFFSETMIN": 0,
        "OFFSETMAX": 1000000000,
        "SYNCOFFSMIN": -99999,
        "SYNCOFFSMAX": 99999,
        "CHANOFFSMIN": -8000,
        "CHANOFFSMAX": 8000,
        "ACQTMIN": 1,
        "ACQTMAX": 360000000,
        "PHR800LVMIN": -1600,
        "PHR800LVMAX": 2400,
        "HOLDOFFMAX": 210480,
        "WARNING_INP0_RATE_ZERO": 0x0001,
        "WARNING_INP0_RATE_TOO_LOW": 0x0002,
        "WARNING_INP0_RATE_TOO_HIGH": 0x0004,
        "WARNING_INP1_RATE_ZERO": 0x0010,
        "WARNING_INP1_RATE_TOO_HIGH": 0x0040,
        "WARNING_INP_RATE_RATIO": 0x0100,
        "WARNING_DIVIDER_GREATER_ONE": 0x0200,
        "WARNING_TIME_SPAN_TOO_SMALL": 0x0400,
        "WARNING_OFFSET_UNNECESSARY": 0x0800
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


class LD_Pharp:
    def __init__(self, device_Number=0, hw_Config=None, dll_Path=None):
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

        if isinstance(hw_Config, type(None)):
            self.logger.debug("Making default HW settings")
            self.hw_Settings = LD_Pharp_Config.LD_Pharp_Config().hw_Settings
        else:
            self.logger.debug("HW Settings passed in")
            self.hw_Settings = hw_Config

        # Connect to the Picoharp device.
        self.my_PharpDLL = LD_PharpDLL.LD_PharpDLL(device_Number, dll_Path)

        # TODO: Check this is the expected version.
        self.library_Version = self.my_PharpDLL.Get_LibraryVersion()

        # Housekeeping for getting the Picoharp up.
        self.my_PharpDLL.Open()
        self.my_PharpDLL.Initialize(0)
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

    def Get_CountRate(self):
        """
        Returns both channel count rates in a python list.
        """
        count_Channels = self.my_PharpDLL.Get_CountRate()
        return count_Channels

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
        histogram = self.my_PharpDLL.Get_Histogram(n_Channels)

        # Some Picoharp status stuff that might be useful?
        # flags = self.my_PharpDLL.Get_Flags()
        # time = self.my_PharpDLL.Get_ElapsedMeasTime()
        # print(f"Flags {flags}")
        return histogram

    def Get_Warnings(self):
        print("get warnings code")
        warn_Code = self.my_PharpDLL.Get_Warnings()
        print("translate warnings code")
        warn_Text = self.my_PharpDLL.Get_WarningsText(warn_Code)
        return warn_Code, warn_Text

if __name__ == "__main__":    
    my_LDPharp = LD_Pharp()

    print(f"Count rate: {my_LDPharp.Get_CountRate()}")
    
    w = my_LDPharp.Get_Warnings()
    
    del my_LDPharp
